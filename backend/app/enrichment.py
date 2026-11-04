"""Read/write the cached enrichment file produced by ``scripts/enrich.py``."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import Enrichment


def save_enrichment(path: Path, method: str, model: str | None, items: list[Enrichment]) -> None:
    """Write enrichments (sorted by product id so the file is deterministic and diff-friendly)."""
    payload = {
        "meta": {"method": method, "model": model},
        "products": [e.model_dump() for e in sorted(items, key=lambda e: e.product_id)],
    }
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_enrichment(path: Path) -> tuple[dict, dict[str, Enrichment]]:
    """Return ``(meta, {product_id: Enrichment})`` from ``path``."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw["meta"], {e["product_id"]: Enrichment.model_validate(e) for e in raw["products"]}
