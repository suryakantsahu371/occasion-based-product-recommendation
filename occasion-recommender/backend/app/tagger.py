"""Deterministic rule-based tagger: the zero-API-key fallback for the offline LLM enrichment.

It produces the same ``Enrichment`` structure as the LLM path, from three signals:
keyword evidence in the title/description, the vendor's identity, and name terms
("Diwali" in a title means the product is tied to Diwali).
"""

from __future__ import annotations

import re
from collections import defaultdict
from functools import cache

from app.schemas import Enrichment, Product
from app.taxonomy import OCCASIONS, SHOP_PRIORS, Occasion

MIN_TAG_SCORE = 0.2
_RULE_CAP = 0.95
_TITLE_MULTIPLIER = 1.5
SIBLING_FESTIVAL_CAP = 0.3

# (label, evidence phrases). The label with the most evidence in a category's products wins.
CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Festive Hampers", ("hamper",)),
    ("Chocolates", ("chocolate",)),
    ("Fresh Flowers", ("flower", "bouquet", "tulip", "lilies", "marigold")),
    ("Corporate Gifts", ("corporate", "pen", "pens", "employee", "office")),
    ("Apparel", ("shirt", "tshirt", "jeans", "pants", "kurti", "saree", "suit", "cargo", "print")),
    ("Fragrance & Candles", ("perfume", "soap", "fragrance")),
    ("Watches", ("watch",)),
    ("Jewellery", ("necklace", "bracelet", "earring", "choker", "jewel")),
    ("Eco Home & Living", ("bamboo", "plants", "natural fibers", "plant-derived")),
    ("Recycled & Upcycled Gifts", ("recycled", "upcycled", "repurposed")),
    ("Organic Wellness", ("organic", "herbal", "skincare", "wellness")),
    ("Craft & DIY Kits", ("diy", "craft", "painting", "slime")),
    ("Soft Toys & Plushies", ("plush", "teddy", "soft toys")),
    ("Musical Toys", ("xylophone", "drum", "guitar", "musical")),
    ("Long-Distance Love Gifts", ("long-distance", "distance", "open when")),
    ("Romantic Gifts", ("romance", "romantic", "couple")),
    ("Personalised Gifts", ("personalized", "custom star map", "story book")),
    ("Gift Cards", ("gift card",)),
    ("Gift Accessories", ("gift accessories", "wrapping", "wax seal")),
    ("Celebration Gifts", ("personal celebrations", "housewarming", "baby shower", "engagement")),
)
DEFAULT_CATEGORY = "General Gifts"

_RECIPIENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("kids", ("kids", "children", "toy", "plush", "teddy")),
    ("partner", ("couple", "partner", "romantic", "his and hers")),
    ("colleague", ("employee", "office", "corporate", "workplace", "client")),
    ("her", ("women", "necklace", "earring", "saree", "kurti", "bracelet", "skincare")),
    ("him", ("men", "executive", "pen")),
    ("family", ("family", "festive", "hamper", "togetherness")),
)


@cache
def _phrase_re(phrase: str) -> re.Pattern[str]:
    """Word-start match; short phrases also need a word end so 'tea' does not hit 'teal'."""
    escaped = re.escape(phrase)
    pattern = rf"\b{escaped}" if len(phrase) >= 6 else rf"\b{escaped}s?\b"
    return re.compile(pattern)


def has_phrase(text: str, phrase: str) -> bool:
    return _phrase_re(phrase).search(text) is not None


def infer_category_labels(products: list[Product]) -> dict[str, str]:
    """Name each ``vendor_category`` group by keyword voting over its products' text."""
    groups: dict[str, list[Product]] = defaultdict(list)
    for p in products:
        groups[p.vendor_category or "unknown"].append(p)

    labels: dict[str, str] = {}
    for category, members in groups.items():
        best_label, best_score = DEFAULT_CATEGORY, 0
        for label, phrases in CATEGORY_RULES:
            score = 0
            for p in members:
                body = f"{p.description} {p.extra_description} {p.category_blurb}".lower()
                title = p.title.lower()
                score += sum(2 * has_phrase(title, ph) + has_phrase(body, ph) for ph in phrases)
            if score > best_score:
                best_label, best_score = label, score
        labels[category] = best_label
    return labels


def _occasion_score(occasion: Occasion, title: str, body: str, shop: str) -> float:
    """Noisy-OR of keyword evidence and the vendor prior; 1.0 when a name term is in the title."""
    if any(has_phrase(title, term) for term in occasion.name_terms):
        return 1.0
    rule = 0.0
    for phrase, weight in occasion.keywords.items():
        if has_phrase(title, phrase):
            rule += weight * _TITLE_MULTIPLIER
        elif has_phrase(body, phrase):
            rule += weight
    rule = min(rule, _RULE_CAP)
    prior = max(
        (scores.get(occasion.key, 0.0) for name, scores in SHOP_PRIORS.items() if name in shop),
        default=0.0,
    )
    return 1.0 - (1.0 - rule) * (1.0 - prior)


def _recipients(text: str) -> list[str]:
    found = [name for name, phrases in _RECIPIENT_RULES if any(has_phrase(text, ph) for ph in phrases)]
    return found or ["friends"]


def tag_product(product: Product, category_label: str) -> Enrichment:
    """Rule-based equivalent of the LLM tagging call for one product."""
    title = product.title.lower()
    body = f"{product.description} {product.extra_description}".lower()
    shop = product.shop.lower()

    scores: dict[str, float] = {}
    specific: tuple[float, str] | None = None
    for occasion in OCCASIONS:
        scores[occasion.key] = _occasion_score(occasion, title, body, shop)
        if occasion.specific and any(has_phrase(title, t) for t in occasion.name_terms):
            specific = max(specific or (0.0, ""), (scores[occasion.key], occasion.key))
    if specific:
        # A product named for one festival is not a fit for its sibling festivals.
        for occasion in OCCASIONS:
            if occasion.specific and occasion.key != specific[1]:
                scores[occasion.key] = min(scores[occasion.key], SIBLING_FESTIVAL_CAP)
    occasions = {k: round(v, 2) for k, v in sorted(scores.items()) if v >= MIN_TAG_SCORE}
    return Enrichment(
        product_id=product.product_id,
        category_label=category_label,
        occasions=occasions,
        recipients=_recipients(f"{title} {body}"),
        occasion_specific_to=specific[1] if specific else None,
    )
