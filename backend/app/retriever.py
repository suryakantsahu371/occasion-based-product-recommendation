"""Retrieval signals: FAISS semantic search plus BM25 / TF-IDF keyword scoring.

Everything expensive is built offline by ``scripts/build_index.py``; this module only loads
the artifacts and answers per-query similarity lookups in memory.
"""

from __future__ import annotations

import json
import pickle
import re
from functools import lru_cache
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from app.adapter import load_products, published
from app.config import KeywordMethod, Settings
from app.enrichment import load_enrichment
from app.schemas import Enrichment, Product
from app.taxonomy import BY_KEY

_TOKEN = re.compile(r"[a-z0-9]+")
_STRONG_TAG = 0.5  # tags at or above this are written into the search document


def stem(token: str) -> str:
    """Tiny plural stemmer: hampers -> hamper, candles -> candle (leaves 'glass' alone)."""
    if len(token) > 3 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def preprocess(text: str) -> str:
    """Shared by every keyword index and query: lowercase, drop stop words, stem."""
    tokens = (stem(t) for t in _TOKEN.findall(text.lower()) if t not in ENGLISH_STOP_WORDS)
    return " ".join(tokens)


def tokenize(text: str) -> list[str]:
    return preprocess(text).split()


def search_document(product: Product, enrichment: Enrichment) -> str:
    """``name | category | shop | description | occasion tags`` as specified in the design."""
    strong = sorted(
        (k for k, v in enrichment.occasions.items() if v >= _STRONG_TAG),
        key=lambda k: -enrichment.occasions[k],
    )
    parts = [
        product.title,
        enrichment.category_label,
        product.shop,
        f"{product.description} {product.extra_description}".strip(),
        " ".join(BY_KEY[k].label for k in strong),
    ]
    return " | ".join(p for p in parts if p)


class Retriever:
    """Loaded indexes plus per-query similarity lookups."""

    def __init__(
        self,
        settings: Settings,
        products: list[Product],
        enrichments: dict[str, Enrichment],
        faiss_index: faiss.Index,
        bm25: Any,
        tfidf: Any,
        tfidf_matrix: Any,
        model: SentenceTransformer,
    ) -> None:
        self.settings = settings
        self.products = products
        self.enrichments = enrichments
        self.index = faiss_index
        self.bm25 = bm25
        self.tfidf = tfidf
        self.tfidf_matrix = tfidf_matrix
        self.model = model
        # Unit-norm document embeddings, used by MMR to measure product-to-product similarity.
        self.embeddings: np.ndarray = faiss_index.reconstruct_n(0, faiss_index.ntotal)
        self.doc_tokens: list[set[str]] = [
            set(tokenize(search_document(p, enrichments[p.product_id]))) for p in products
        ]
        self._embed = lru_cache(maxsize=256)(self._embed_uncached)

    @classmethod
    def load(cls, settings: Settings) -> Retriever:
        """Load products, enrichments, FAISS/BM25/TF-IDF artifacts and the embedding model."""
        id_order: list[str] = json.loads(settings.id_map_path.read_text(encoding="utf-8"))
        by_id = {p.product_id: p for p in published(load_products(settings.products_path, settings))}
        products = [by_id[i] for i in id_order]
        _, enrichments = load_enrichment(settings.enriched_path)
        with settings.bm25_path.open("rb") as fh:
            bm25 = pickle.load(fh)  # trusted: produced by our own build step
        with settings.tfidf_path.open("rb") as fh:
            tfidf, tfidf_matrix = pickle.load(fh)
        return cls(
            settings,
            products,
            enrichments,
            faiss.read_index(str(settings.faiss_path)),
            bm25,
            tfidf,
            tfidf_matrix,
            SentenceTransformer(settings.embedding_model, device="cpu"),
        )

    def _embed_uncached(self, text: str) -> np.ndarray:
        vec = self.model.encode(
            [self.settings.query_instruction + text], normalize_embeddings=True, convert_to_numpy=True
        )
        return vec.astype("float32")

    def cosine(self, text: str) -> np.ndarray:
        """Cosine similarity of ``text`` to every product, via FAISS exact inner-product search."""
        scores, ids = self.index.search(self._embed(text), self.index.ntotal)
        out = np.zeros(self.index.ntotal, dtype="float32")
        out[ids[0]] = scores[0]
        return out

    def keyword(self, text: str, method: KeywordMethod) -> np.ndarray:
        """Raw keyword relevance of ``text`` to every product (BM25 or TF-IDF cosine)."""
        if method == "bm25":
            tokens = tokenize(text)
            return (
                np.asarray(self.bm25.get_scores(tokens), dtype="float32")
                if tokens
                else np.zeros(len(self.products), dtype="float32")
            )
        query_vec = self.tfidf.transform([preprocess(text)])
        return np.asarray((self.tfidf_matrix @ query_vec.T).todense()).ravel().astype("float32")
