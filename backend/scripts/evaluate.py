"""Evaluate five ranking variants on the hand-labelled gold set (Precision@5, nDCG@10).

All variants share the same query parsing/expansion and the same final MMR + per-group cap
stage (no relevance threshold), so the comparison isolates the scoring signal.
Prints a markdown table and writes it to ``data/evaluation.md``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import KeywordMethod, Weights, get_settings  # noqa: E402
from app.query import parse_query  # noqa: E402
from app.ranker import Recommender  # noqa: E402
from app.retriever import Retriever  # noqa: E402

NO_PENALTIES: dict[str, float] = {}


def _only(**kw: float) -> Weights:
    base = dict(semantic=0.0, tag=0.0, keyword=0.0, name_boost=0.0, conflict_penalty=0.0)
    return Weights(**{**base, **kw}, quality_penalty=NO_PENALTIES)


VARIANTS: dict[str, tuple[Weights, KeywordMethod]] = {
    "TF-IDF only": (_only(keyword=1.0), "tfidf"),
    "BM25 only": (_only(keyword=1.0), "bm25"),
    "Semantic only": (_only(semantic=1.0), "bm25"),
    "Hybrid (TF-IDF)": (Weights(), "tfidf"),
    "Hybrid (BM25)": (Weights(), "bm25"),
}


def precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return sum(pid in relevant for pid in ranked[:k]) / k


def ndcg_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log2(i + 2) for i, pid in enumerate(ranked[:k]) if pid in relevant)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / ideal if ideal else 0.0


def evaluate(recommender: Recommender, gold: list[dict]) -> dict[str, dict[str, tuple[float, float]]]:
    """Return ``{variant: {query: (P@5, nDCG@10)}}``."""
    results: dict[str, dict[str, tuple[float, float]]] = {}
    for name, (weights, method) in VARIANTS.items():
        per_query = {}
        for entry in gold:
            parsed = parse_query(entry["query"], recommender.settings.fuzzy_cutoff)
            picked, _ = recommender.rank(parsed, 10, method=method, weights=weights, threshold=-math.inf)
            ranked = [recommender.retriever.products[i].product_id for i in picked]
            relevant = {r["id"] for r in entry["relevant"]}
            per_query[entry["query"]] = (precision_at_k(ranked, relevant, 5), ndcg_at_k(ranked, relevant, 10))
        results[name] = per_query
    return results


def to_markdown(results: dict[str, dict[str, tuple[float, float]]], queries: list[str]) -> str:
    names = list(results)
    lines = ["| Occasion | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for q in queries:
        cells = [f"{results[n][q][0]:.2f} / {results[n][q][1]:.2f}" for n in names]
        lines.append(f"| {q} | " + " | ".join(cells) + " |")
    means = []
    for n in names:
        p = sum(v[0] for v in results[n].values()) / len(queries)
        g = sum(v[1] for v in results[n].values()) / len(queries)
        means.append(f"**{p:.3f} / {g:.3f}**")
    lines.append("| **Mean** | " + " | ".join(means) + " |")
    return "\n".join(lines)


def main() -> None:
    settings = get_settings()
    gold = json.loads(settings.gold_path.read_text(encoding="utf-8"))["occasions"]
    recommender = Recommender(Retriever.load(settings))
    results = evaluate(recommender, gold)
    table = "Cells are Precision@5 / nDCG@10.\n\n" + to_markdown(results, [g["query"] for g in gold])
    print(table)
    (settings.data_dir / "evaluation.md").write_text(table + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
