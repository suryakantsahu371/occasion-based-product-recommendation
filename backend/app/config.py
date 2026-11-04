"""Central configuration: paths, model names and every ranking weight in one place."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

KeywordMethod = Literal["bm25", "tfidf"]

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _env_path(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, default))


@dataclass(frozen=True)
class Weights:
    """Hybrid score = semantic*w_sem + tag*w_tag + keyword*w_kw + name_boost - penalties."""

    semantic: float = 0.45
    tag: float = 0.35
    keyword: float = 0.20
    name_boost: float = 0.30
    conflict_penalty: float = 0.50
    # Quality-flag penalties, keyed by flag name (see app/quality.py).
    quality_penalty: dict[str, float] = field(
        default_factory=lambda: {
            "placeholder_text": 0.30,
            "junk_text": 0.30,
            "price_outlier": 0.15,
            "thin_description": 0.05,
        }
    )

    def open_ended(self) -> Weights:
        """Redistribute the tag weight proportionally when no occasion was matched."""
        rest = self.semantic + self.keyword
        return Weights(
            semantic=self.semantic + self.tag * self.semantic / rest,
            tag=0.0,
            keyword=self.keyword + self.tag * self.keyword / rest,
            name_boost=self.name_boost,
            conflict_penalty=self.conflict_penalty,
            quality_penalty=self.quality_penalty,
        )


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Paths and the keyword method can be overridden via env vars."""

    data_dir: Path = field(default_factory=lambda: _env_path("DATA_DIR", BACKEND_DIR / "data"))
    embedding_model: str = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    # bge models are trained with this instruction prefix on the *query* side only.
    query_instruction: str = "Represent this sentence for searching relevant passages: "
    keyword_method: KeywordMethod = "bm25"  # chosen from the gold-set evaluation, see README
    weights: Weights = field(default_factory=Weights)

    # Semantic similarity is rescaled with fixed, catalog-independent anchors so an
    # unrelated query scores ~0 instead of being stretched to fill [0, 1].
    cosine_floor: float = 0.40
    cosine_ceiling: float = 0.80

    relevance_threshold: float = 0.35  # results scoring below this are dropped
    # Unmatched queries need real evidence. Calibrated on bge-small: keyboard-mash queries
    # peak at cosine ~0.60 with no keyword hit; genuine product queries reach >= 0.64.
    open_ended_min_cosine: float = 0.62
    open_ended_rescue_cosine: float = 0.52  # minimum cosine for a keyword-only match
    max_per_group: int = 2  # max results per productGroupId
    default_top_k: int = 12
    max_top_k: int = 50
    max_query_len: int = 100
    fuzzy_cutoff: float = 80.0  # rapidfuzz ratio (0-100) needed to accept a typo'd synonym
    mmr_lambda: float = 0.85  # 1.0 = pure relevance, lower = more diversity

    # Price sanity bounds (INR) used by the junk detector.
    min_plausible_price: float = 20.0
    max_plausible_price: float = 50_000.0

    cors_origins: tuple[str, ...] = tuple(
        os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    )

    @property
    def products_path(self) -> Path:
        return self.data_dir / "products.json"

    @property
    def enriched_path(self) -> Path:
        return self.data_dir / "enriched_products.json"

    @property
    def faiss_path(self) -> Path:
        return self.data_dir / "index.faiss"

    @property
    def bm25_path(self) -> Path:
        return self.data_dir / "bm25.pkl"

    @property
    def tfidf_path(self) -> Path:
        return self.data_dir / "tfidf.pkl"

    @property
    def id_map_path(self) -> Path:
        return self.data_dir / "id_map.json"

    @property
    def gold_path(self) -> Path:
        return self.data_dir / "gold.json"


def get_settings() -> Settings:
    return Settings()
