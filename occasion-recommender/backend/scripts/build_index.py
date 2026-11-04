"""Offline index build: search documents -> embeddings (FAISS), BM25 and TF-IDF artifacts.

Run after ``scripts/enrich.py``; writes ``index.faiss``, ``bm25.pkl``, ``tfidf.pkl`` and
``id_map.json`` into the data directory.
"""

from __future__ import annotations

import json
import logging
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import faiss  # noqa: E402
from rank_bm25 import BM25Okapi  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

from app.adapter import load_products, published  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.enrichment import load_enrichment  # noqa: E402
from app.retriever import preprocess, search_document, tokenize  # noqa: E402

log = logging.getLogger("build_index")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    # Sorted by id so the index order (and therefore all tie-breaks) is deterministic.
    products = sorted(published(load_products(settings.products_path, settings)), key=lambda p: p.product_id)
    _, enrichments = load_enrichment(settings.enriched_path)
    missing = [p.product_id for p in products if p.product_id not in enrichments]
    if missing:
        raise SystemExit(f"{len(missing)} products lack enrichment; run scripts/enrich.py first")

    docs = [search_document(p, enrichments[p.product_id]) for p in products]
    log.info("embedding %d documents with %s", len(docs), settings.embedding_model)
    model = SentenceTransformer(settings.embedding_model, device="cpu")
    embeddings = model.encode(docs, normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    index = faiss.IndexFlatIP(embeddings.shape[1])  # inner product == cosine on unit vectors
    index.add(embeddings)
    faiss.write_index(index, str(settings.faiss_path))

    bm25 = BM25Okapi([tokenize(d) for d in docs])
    with settings.bm25_path.open("wb") as fh:
        pickle.dump(bm25, fh)

    tfidf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
    matrix = tfidf.fit_transform([preprocess(d) for d in docs])
    with settings.tfidf_path.open("wb") as fh:
        pickle.dump((tfidf, matrix), fh)

    settings.id_map_path.write_text(
        json.dumps([p.product_id for p in products], indent=1) + "\n", encoding="utf-8"
    )
    log.info(
        "index built: %d products, dim=%d, tfidf vocab=%d",
        len(products),
        embeddings.shape[1],
        len(tfidf.vocabulary_),
    )


if __name__ == "__main__":
    main()
