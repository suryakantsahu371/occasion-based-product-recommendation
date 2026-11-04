"""Offline enrichment: category labels + occasion tags for every published product.

Two interchangeable backends write the same ``data/enriched_products.json``:

* ``llm``   - Claude with forced tool-use (structured output), temperature 0, Pydantic-validated.
              Needs ``ANTHROPIC_API_KEY``. Results are cached: re-runs only tag new products.
* ``rules`` - deterministic keyword/vendor rules (``app/tagger.py``); needs no network or key.

``auto`` (default) picks ``llm`` when a key is present, otherwise ``rules``.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from app.adapter import load_products, published  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.enrichment import load_enrichment, save_enrichment  # noqa: E402
from app.schemas import Enrichment, Product  # noqa: E402
from app.tagger import DEFAULT_CATEGORY, infer_category_labels, tag_product  # noqa: E402
from app.taxonomy import OCCASIONS, TAXONOMY_KEYS  # noqa: E402

log = logging.getLogger("enrich")
DEFAULT_LLM_MODEL = os.environ.get("ENRICH_MODEL", "claude-haiku-5-5")

TAG_TOOL = {
    "name": "record_tags",
    "description": "Record occasion-fit scores for one gift product.",
    "input_schema": {
        "type": "object",
        "properties": {
            "occasions": {
                "type": "object",
                "description": "Fit score 0-1 per occasion key. Omit occasions scoring below 0.2.",
                "properties": {k: {"type": "number", "minimum": 0, "maximum": 1} for k in TAXONOMY_KEYS},
                "additionalProperties": False,
            },
            "recipients": {"type": "array", "items": {"type": "string"}},
            "occasion_specific_to": {
                "type": ["string", "null"],
                "enum": [*TAXONOMY_KEYS, None],
                "description": "Set only when the product is tied to ONE occasion (e.g. a Holi hamper -> holi).",
            },
        },
        "required": ["occasions", "recipients", "occasion_specific_to"],
    },
}
CATEGORY_TOOL = {
    "name": "record_category",
    "description": "Record a short human-readable category label.",
    "input_schema": {
        "type": "object",
        "properties": {"label": {"type": "string", "maxLength": 40}},
        "required": ["label"],
    },
}


def _call_tool(client, model: str, system: str, user: str, tool: dict) -> dict:
    """One forced tool-use call; returns the tool input (already JSON-decoded)."""
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
    )
    return next(block.input for block in response.content if block.type == "tool_use")


def llm_category_labels(client, model: str, products: list[Product]) -> dict[str, str]:
    """Ask the LLM once per category group for a human-readable label."""
    groups: dict[str, list[str]] = defaultdict(list)
    for p in products:
        groups[p.vendor_category or "unknown"].append(p.title)
    labels = {}
    for category, titles in groups.items():
        out = _call_tool(
            client,
            model,
            "You label product categories for a gifting marketplace in 2-3 words, e.g. 'Fresh Flowers'.",
            "Product names in one category: " + "; ".join(sorted(set(titles))),
            CATEGORY_TOOL,
        )
        labels[category] = str(out.get("label") or DEFAULT_CATEGORY).strip()[:40]
    return labels


def llm_tag_product(client, model: str, product: Product, category_label: str) -> Enrichment:
    """Score one product against the fixed taxonomy; invalid output raises ``ValidationError``."""
    taxonomy = "\n".join(f"- {o.key}: {o.label}" for o in OCCASIONS)
    out = _call_tool(
        client,
        model,
        "You tag gift products with the occasions they suit. Use ONLY these occasion keys:\n"
        f"{taxonomy}\nScore 0-1 how well the product fits each occasion; be strict and consistent.",
        f"Shop: {product.shop}\nCategory: {category_label}\nTitle: {product.title}\n"
        f"Description: {product.description} {product.extra_description}",
        TAG_TOOL,
    )
    return Enrichment(product_id=product.product_id, category_label=category_label, **out)


def run_llm(products: list[Product], settings, model: str) -> list[Enrichment]:
    import anthropic  # imported lazily: only needed on the LLM path

    client = anthropic.Anthropic()
    cached: dict[str, Enrichment] = {}
    if settings.enriched_path.exists():
        meta, existing = load_enrichment(settings.enriched_path)
        if meta.get("method") == "llm" and meta.get("model") == model:
            cached = existing
    labels = llm_category_labels(client, model, products)
    results = []
    for p in products:
        if p.product_id in cached:
            results.append(cached[p.product_id])
            continue
        label = labels.get(p.vendor_category or "unknown", DEFAULT_CATEGORY)
        try:
            results.append(llm_tag_product(client, model, p, label))
        except (ValidationError, StopIteration, KeyError, TypeError) as exc:
            log.warning("LLM output rejected for %s (%s); using rule-based tags", p.product_id, exc)
            results.append(tag_product(p, label))
    return results


def run_rules(products: list[Product]) -> list[Enrichment]:
    labels = infer_category_labels(products)
    return [tag_product(p, labels[p.vendor_category or "unknown"]) for p in products]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--method", choices=["auto", "llm", "rules"], default="auto")
    parser.add_argument("--model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--sample", type=int, default=0, help="print N sample enrichments")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    settings = get_settings()
    products = published(load_products(settings.products_path, settings))
    method = args.method
    if method == "auto":
        method = "llm" if os.environ.get("ANTHROPIC_API_KEY") else "rules"
        log.info("auto-selected method: %s", method)

    if method == "llm":
        items, model = run_llm(products, settings, args.model), args.model
    else:
        items, model = run_rules(products), None
    save_enrichment(settings.enriched_path, method, model, items)
    log.info("wrote %d enrichments to %s (method=%s)", len(items), settings.enriched_path, method)

    by_id = {p.product_id: p for p in products}
    for item in items[: args.sample]:
        print(json.dumps({"title": by_id[item.product_id].title, **item.model_dump()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
