"""Junk / test-data detector. Flags are used to down-weight products, never to delete them."""

from __future__ import annotations

import re

from app.config import Settings
from app.schemas import Product

_VOWELS = set("aeiou")
_PLACEHOLDER_PATTERNS = (
    re.compile(r"\bcreated by\b"),
    re.compile(r"\bdeepesh\b"),
    re.compile(r"\blorem ipsum\b"),
    re.compile(r"^\W*(test|testing|asdf|qwerty|xyz)\b"),
    re.compile(r"\bdescription\W*$"),
)


def _vowel_ratio(word: str) -> float:
    return sum(ch in _VOWELS for ch in word) / len(word)


def is_gibberish(text: str) -> bool:
    """True when most long words look like keyboard mashing (very few vowels)."""
    words = re.findall(r"[a-z]+", text.lower())
    long_words = [w for w in words if len(w) >= 7]
    if not long_words:
        return False
    junk = sum(_vowel_ratio(w) < 0.2 for w in long_words)
    return junk / len(long_words) >= 0.5


def assess(product: Product, settings: Settings) -> list[str]:
    """Return the sorted list of quality flags for ``product``.

    Flags: ``junk_text`` (gibberish), ``placeholder_text`` (test phrases), ``price_outlier``
    (implausibly low/high) and ``thin_description`` (fewer than 3 words of copy).
    """
    flags: set[str] = set()
    text = f"{product.title} {product.description}".strip().lower()

    if is_gibberish(product.description):
        flags.add("junk_text")
    if any(p.search(product.description.lower()) for p in _PLACEHOLDER_PATTERNS):
        flags.add("placeholder_text")
    if len(product.description.split()) < 3:
        flags.add("thin_description")
    if product.price is not None and not (
        settings.min_plausible_price <= product.price <= settings.max_plausible_price
    ):
        flags.add("price_outlier")
    if not text:
        flags.add("thin_description")
    return sorted(flags)
