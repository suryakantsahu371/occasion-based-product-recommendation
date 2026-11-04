"""Payload adapter: maps either the brief's schema or the raw catalog schema to ``Product``."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.config import Settings
from app.quality import assess
from app.schemas import Product

_TRAILING_RANDOM = re.compile(r"-[a-z0-9]{8}$")
_WORD = re.compile(r"[a-z0-9]+")
_BOILERPLATE_MIN_REPEATS = 3  # a "short description" shared by this many products is a category blurb


def _first(payload: dict[str, Any], *keys: str) -> Any:
    """First non-None value among ``keys`` (handles the product_id/productId style aliases)."""
    for key in keys:
        if payload.get(key) is not None:
            return payload[key]
    return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_text(text: Any) -> str:
    """Collapse ``\\r\\n`` and runs of whitespace into single spaces."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def extract_shop(payload: dict[str, Any]) -> str:
    """Recover the shop name embedded in ``slug`` (e.g. ``flower-bloom by the hour``).

    The slug is ``<product-slug>-<Shop Name>[-<8 char dedupe suffix>]``. The product part is
    lower-case and hyphenated, whereas the shop name contains a space or a capital letter,
    so the shop starts at the first hyphen-separated segment that does. Falls back to ``brand``.
    """
    slug = clean_text(payload.get("slug"))
    segments = slug.split("-")
    for i, segment in enumerate(segments):
        if i > 0 and (" " in segment or any(c.isupper() for c in segment)):
            return _TRAILING_RANDOM.sub("", "-".join(segments[i:])).strip()
    return clean_text(payload.get("brand"))


def _files(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("files")
    if raw is None and payload.get("mainImage"):
        raw = [payload["mainImage"]]
    urls: list[str] = []
    for item in raw or []:
        url = item.get("url") or item.get("path") if isinstance(item, dict) else item
        if url:
            urls.append(str(url))
    return urls


def _truncate_to_sentence_or_word(text: str) -> str:
    """Drop the dangling fragment of a ~150 char truncated blurb."""
    text = text.strip()
    if text and text[-1] not in ".!?":
        cut = max(text.rfind(". "), text.rfind("! "), text.rfind("? "))
        text = text[: cut + 1] if cut > 0 else text.rstrip(" ,;:-")
    return text


def normalize_payload(payload: dict[str, Any]) -> Product:
    """Normalise one raw payload into a ``Product``.

    Accepts both the brief's keys (``product_id``/``productId``, ``vendor_id``/``vendorId``,
    ``vendor_category``, ``vendor_category_desc``, ``title``, ``description``, ``files``)
    and the catalog's keys (``id``, ``shopId``, ``categoryId``, ``name``, ``mainImage`` ...).
    """
    product_id = _first(payload, "product_id", "productId", "id")
    if product_id is None:
        raise ValueError("payload has no product id")

    description = clean_text(payload.get("description"))
    short = clean_text(payload.get("shortDescription"))
    extra = ""
    # Short descriptions are often a truncated copy: keep one only if it adds new words.
    if short and len(set(_WORD.findall(short.lower())) - set(_WORD.findall(description.lower()))) >= 3:
        extra = _truncate_to_sentence_or_word(short)
    if not description and short:
        description, extra = short, ""

    status = str(payload.get("status") or "ACTIVE").upper()
    return Product(
        product_id=str(product_id),
        vendor_id=_first(payload, "vendor_id", "vendorId", "shopId"),
        vendor_category=_first(payload, "vendor_category", "categoryId"),
        vendor_category_desc=payload.get("vendor_category_desc"),
        title=clean_text(_first(payload, "title", "name")),
        description=description,
        extra_description=extra,
        files=_files(payload),
        shop=extract_shop(payload),
        price=_to_float(payload.get("price")),
        discount_pct=max(0.0, min(100.0, _to_float(payload.get("discountPercentage")) or 0.0)),
        stock=int(stock) if (stock := _to_float(payload.get("stock"))) is not None else 1,
        status=status,
        is_approved=bool(payload.get("isApproved", True)),
        deleted=payload.get("deletedAt") is not None,
        product_group_id=payload.get("productGroupId"),
    )


def load_products(path: Path, settings: Settings) -> list[Product]:
    """Load and normalise every payload in ``path`` (all statuses), with quality flags set.

    Category blurbs repeated across several products are dropped from ``extra_description``
    because they describe the shelf, not the product, and would blur occasion signals.
    """
    payloads = json.loads(Path(path).read_text(encoding="utf-8"))
    products = [normalize_payload(p) for p in payloads]
    repeats = Counter(p.extra_description for p in products if p.extra_description)
    for p in products:
        if repeats[p.extra_description] >= _BOILERPLATE_MIN_REPEATS:
            p.category_blurb, p.extra_description = p.extra_description, ""
        p.quality_flags = assess(p, settings)
    return products


def published(products: list[Product]) -> list[Product]:
    """Products allowed in the index: ACTIVE, approved, not deleted and in stock."""
    return [p for p in products if p.is_published]
