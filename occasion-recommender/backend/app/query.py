"""Query understanding: normalisation, taxonomy mapping (synonyms + typo tolerance), expansion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from rapidfuzz import fuzz, process

from app.taxonomy import OCCASIONS, Occasion

MatchType = Literal["exact", "fuzzy", "open_ended"]

_MIN_FUZZY_LEN = 4  # shorter strings produce too many accidental fuzzy matches


@dataclass(frozen=True)
class ParsedQuery:
    raw: str
    normalized: str
    occasion: Occasion | None
    match_type: MatchType
    text: str  # what gets embedded / keyword-searched (expansion sentence or the raw query)


def normalize(query: str) -> str:
    """Lowercase, drop possessives/punctuation: "Valentine's Day!" -> "valentine day"."""
    text = query.lower().replace("’", "'")
    text = re.sub(r"'s\b", "", text)
    text = re.sub(r"[^a-z0-9À-ɏ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _build_synonym_index() -> dict[str, Occasion]:
    """Map every normalised synonym, label and key to its occasion."""
    index: dict[str, Occasion] = {}
    for occasion in OCCASIONS:
        for phrase in (*occasion.synonyms, occasion.label, occasion.key.replace("_", " ")):
            index.setdefault(normalize(phrase), occasion)
    return index


SYNONYM_INDEX: dict[str, Occasion] = _build_synonym_index()
# Longest phrases first so "kids birthday" wins over "birthday" and "wedding anniversary" over "wedding".
_PHRASES_BY_LENGTH: tuple[str, ...] = tuple(sorted(SYNONYM_INDEX, key=lambda p: (-len(p), p)))


def _match_phrase(normalized: str) -> Occasion | None:
    """Exact synonym, or the longest synonym contained in the query as whole words."""
    if normalized in SYNONYM_INDEX:
        return SYNONYM_INDEX[normalized]
    padded = f" {normalized} "
    for phrase in _PHRASES_BY_LENGTH:
        if f" {phrase} " in padded:
            return SYNONYM_INDEX[phrase]
    return None


def _match_fuzzy(normalized: str, cutoff: float) -> Occasion | None:
    """Typo-tolerant match ("diwaali" -> diwali) on the whole query, then on each word."""
    candidates = [normalized, *normalized.split()]
    for candidate in candidates:
        if len(candidate) < _MIN_FUZZY_LEN:
            continue
        hit = process.extractOne(candidate, SYNONYM_INDEX.keys(), scorer=fuzz.ratio, score_cutoff=cutoff)
        if hit:
            return SYNONYM_INDEX[hit[0]]
    return None


def parse_query(raw: str, fuzzy_cutoff: float = 80.0) -> ParsedQuery:
    """Map ``raw`` to a taxonomy occasion (or treat it as an open-ended query) and expand it."""
    normalized = normalize(raw)
    occasion = _match_phrase(normalized)
    match_type: MatchType = "exact"
    if occasion is None:
        occasion = _match_fuzzy(normalized, fuzzy_cutoff)
        match_type = "fuzzy"
    if occasion is None:
        return ParsedQuery(raw, normalized, None, "open_ended", normalized)
    return ParsedQuery(raw, normalized, occasion, match_type, occasion.expansion)
