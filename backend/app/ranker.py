"""Hybrid scoring, thresholding, MMR diversification and human-readable reasons."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.config import KeywordMethod, Settings, Weights
from app.query import ParsedQuery, parse_query
from app.retriever import Retriever, tokenize
from app.schemas import (
    QueryInfo,
    RecommendedProduct,
    RecommendResponse,
    ScoreBreakdown,
)
from app.tagger import has_phrase
from app.taxonomy import BY_KEY

_SNIPPET_CHARS = 140
_GENERIC_TOKENS = {"gift", "gifting", "present"}  # too common to be a useful "Matches:" reason


@dataclass(frozen=True)
class ScoreMatrix:
    """Per-product score components for one query (arrays aligned with ``Retriever.products``)."""

    total: np.ndarray
    semantic: np.ndarray
    tag: np.ndarray
    keyword: np.ndarray
    name_boost: np.ndarray
    penalty: np.ndarray
    cosine: np.ndarray  # raw cosine, used for the open-ended relevance gate


def _minmax(values: np.ndarray) -> np.ndarray:
    lo, hi = float(values.min()), float(values.max())
    return np.zeros_like(values) if hi - lo < 1e-9 else (values - lo) / (hi - lo)


def snippet(text: str, limit: int = _SNIPPET_CHARS) -> str:
    """Cut ``text`` at a word boundary near ``limit`` characters, appending an ellipsis."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-—")
    return cut + "…"


class Recommender:
    """Scores the catalog for a query and returns a diversified top-K."""

    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever
        self.settings: Settings = retriever.settings

    # ------------------------------------------------------------------ scoring

    def score(self, parsed: ParsedQuery, weights: Weights, method: KeywordMethod) -> ScoreMatrix:
        """Compute ``w_sem*sem + w_tag*tag + w_kw*kw + name_boost - conflict - quality`` per product."""
        s, r = self.settings, self.retriever
        if parsed.occasion is None:
            weights = weights.open_ended()

        cosine = r.cosine(parsed.text)
        semantic = np.clip((cosine - s.cosine_floor) / (s.cosine_ceiling - s.cosine_floor), 0.0, 1.0)
        keyword = _minmax(r.keyword(parsed.text, method))

        n = len(r.products)
        tag, name_boost, penalty = np.zeros(n), np.zeros(n), np.zeros(n)
        query_terms = [t for t in parsed.normalized.split() if len(t) >= 4]
        for i, product in enumerate(r.products):
            enrichment = r.enrichments[product.product_id]
            title = product.title.lower()
            if parsed.occasion is not None:
                key = parsed.occasion.key
                tag[i] = enrichment.occasions.get(key, 0.0)
                if any(has_phrase(title, t) for t in parsed.occasion.name_terms):
                    name_boost[i] = 1.0
                if enrichment.occasion_specific_to not in (None, key):
                    penalty[i] += weights.conflict_penalty
            elif any(has_phrase(title, t) for t in query_terms):
                name_boost[i] = 1.0
            penalty[i] += sum(weights.quality_penalty.get(f, 0.0) for f in product.quality_flags)

        total = (
            weights.semantic * semantic
            + weights.tag * tag
            + weights.keyword * keyword
            + weights.name_boost * name_boost
            - penalty
        )
        return ScoreMatrix(total, semantic, tag, keyword, name_boost * weights.name_boost, penalty, cosine)

    # ------------------------------------------------------------------ ranking

    def _open_ended_evidence(self, scores: ScoreMatrix, i: int) -> bool:
        """Unmatched queries have no tag signal: demand a close embedding, or a keyword hit
        backed by a moderate one (so a stray word like "parties" cannot carry a result alone)."""
        s = self.settings
        if scores.cosine[i] >= s.open_ended_min_cosine:
            return True
        return scores.keyword[i] > 0 and scores.cosine[i] >= s.open_ended_rescue_cosine

    def _eligible(
        self, parsed: ParsedQuery, scores: ScoreMatrix, max_price: float | None, threshold: float
    ) -> list[int]:
        """Indices passing the relevance gate and the optional budget filter, best first."""
        products = self.retriever.products
        keep = []
        for i in np.argsort(-scores.total, kind="stable"):
            product = products[i]
            if scores.total[i] < threshold:
                break
            if max_price is not None and (
                "price_outlier" in product.quality_flags
                or product.final_price is None
                or product.final_price > max_price
            ):
                continue
            if parsed.occasion is None and not self._open_ended_evidence(scores, i):
                continue
            keep.append(int(i))
        return keep

    def _mmr(self, candidates: list[int], scores: ScoreMatrix, k: int) -> list[int]:
        """Greedy maximal-marginal-relevance selection with a hard per-product-group cap."""
        s, r = self.settings, self.retriever
        selected: list[int] = []
        per_group: dict[str, int] = {}
        pool = list(candidates)
        while pool and len(selected) < k:
            best, best_value = None, -np.inf
            for i in pool:
                if per_group.get(r.products[i].group_key, 0) >= s.max_per_group:
                    continue
                redundancy = max((float(r.embeddings[i] @ r.embeddings[j]) for j in selected), default=0.0)
                value = s.mmr_lambda * scores.total[i] - (1 - s.mmr_lambda) * redundancy
                if value > best_value:
                    best, best_value = i, value
            if best is None:
                break
            selected.append(best)
            per_group[r.products[best].group_key] = per_group.get(r.products[best].group_key, 0) + 1
            pool.remove(best)
        return selected

    def rank(
        self,
        parsed: ParsedQuery,
        top_k: int,
        max_price: float | None = None,
        method: KeywordMethod | None = None,
        weights: Weights | None = None,
        threshold: float | None = None,
    ) -> tuple[list[int], ScoreMatrix]:
        """Return the indices of the final results (best first) and the score matrix."""
        s = self.settings
        scores = self.score(parsed, weights or s.weights, method or s.keyword_method)
        gate = s.relevance_threshold if threshold is None else threshold
        return self._mmr(self._eligible(parsed, scores, max_price, gate), scores, top_k), scores

    # ------------------------------------------------------------------ presentation

    def _reasons(self, i: int, parsed: ParsedQuery, scores: ScoreMatrix) -> list[str]:
        r = self.retriever
        reasons: list[str] = []
        if parsed.occasion is not None and scores.tag[i] >= 0.5:
            reasons.append(f"Tagged: {parsed.occasion.label}")
        if scores.name_boost[i] > 0:
            reasons.append("Occasion in product name")
        if scores.keyword[i] > 0:
            hits = [
                t
                for t in dict.fromkeys(tokenize(parsed.text))
                if t in r.doc_tokens[i] and t not in _GENERIC_TOKENS
            ]
            if hits:
                reasons.append("Matches: " + ", ".join(hits[:3]))
        if scores.semantic[i] >= 0.6:
            reasons.append("Semantically similar")
        return reasons or ["Related to your search"]

    def to_result(self, i: int, parsed: ParsedQuery, scores: ScoreMatrix) -> RecommendedProduct:
        product = self.retriever.products[i]
        enrichment = self.retriever.enrichments[product.product_id]
        w = self.settings.weights if parsed.occasion else self.settings.weights.open_ended()
        return RecommendedProduct(
            product_id=product.product_id,
            title=product.title,
            category=enrichment.category_label,
            description=product.description,
            description_snippet=snippet(product.description or product.extra_description),
            image=product.files[0] if product.files else None,
            shop=product.shop,
            price=product.price,
            final_price=product.final_price,
            discount_pct=product.discount_pct,
            score=round(float(scores.total[i]), 4),
            breakdown=ScoreBreakdown(
                semantic=round(float(w.semantic * scores.semantic[i]), 4),
                tag=round(float(w.tag * scores.tag[i]), 4),
                keyword=round(float(w.keyword * scores.keyword[i]), 4),
                name_boost=round(float(scores.name_boost[i]), 4),
                penalty=round(float(scores.penalty[i]), 4),
            ),
            reasons=self._reasons(i, parsed, scores),
        )

    def recommend(
        self,
        occasion: str,
        top_k: int | None = None,
        max_price: float | None = None,
        method: KeywordMethod | None = None,
    ) -> RecommendResponse:
        """Full online path: parse -> score -> filter -> MMR -> response model."""
        s = self.settings
        parsed = parse_query(occasion, s.fuzzy_cutoff)
        method = method or s.keyword_method
        picked, scores = self.rank(parsed, top_k or s.default_top_k, max_price, method)
        results = [self.to_result(i, parsed, scores) for i in picked]
        return RecommendResponse(
            query=QueryInfo(
                raw=occasion,
                matched_occasion=parsed.occasion.key if parsed.occasion else None,
                matched_label=BY_KEY[parsed.occasion.key].label if parsed.occasion else None,
                match_type=parsed.match_type,
            ),
            results=results,
            total=len(results),
            keyword_method=method,
            latency_ms=0.0,  # filled in by the API layer, which owns the timer
        )
