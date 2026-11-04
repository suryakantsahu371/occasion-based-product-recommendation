"""Pydantic models: internal domain objects and the HTTP request/response contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.taxonomy import TAXONOMY_KEYS


class Product(BaseModel):
    """Normalised product, independent of the payload shape it was read from."""

    product_id: str
    vendor_id: str | None = None
    vendor_category: str | None = None
    vendor_category_desc: str | None = None  # inferred offline when absent from the payload
    title: str = ""
    description: str = ""
    extra_description: str = ""  # shortDescription, kept only when it adds new words
    category_blurb: str = ""  # shortDescription repeated across a shelf; used only to name categories
    files: list[str] = Field(default_factory=list)
    shop: str = ""
    price: float | None = None
    discount_pct: float = 0.0
    stock: int = 0
    status: str = "ACTIVE"
    is_approved: bool = True
    deleted: bool = False
    product_group_id: str | None = None
    quality_flags: list[str] = Field(default_factory=list)

    @property
    def quality_flag(self) -> str | None:
        """Comma-joined flags, or ``None`` for a clean product."""
        return ",".join(self.quality_flags) or None

    @property
    def final_price(self) -> float | None:
        if self.price is None:
            return None
        return round(self.price * (1 - self.discount_pct / 100), 2)

    @property
    def group_key(self) -> str:
        return self.product_group_id or self.product_id

    @property
    def is_published(self) -> bool:
        """True only for products that may ever be shown to a user."""
        return self.status == "ACTIVE" and self.is_approved and not self.deleted and self.stock > 0


class Enrichment(BaseModel):
    """Offline LLM (or rule-based) annotation of one product."""

    product_id: str
    category_label: str
    occasions: dict[str, float] = Field(default_factory=dict)
    recipients: list[str] = Field(default_factory=list)
    occasion_specific_to: str | None = None

    @field_validator("occasions")
    @classmethod
    def _taxonomy_only(cls, value: dict[str, float]) -> dict[str, float]:
        unknown = set(value) - set(TAXONOMY_KEYS)
        if unknown:
            raise ValueError(f"tags outside the taxonomy: {sorted(unknown)}")
        if any(not 0.0 <= score <= 1.0 for score in value.values()):
            raise ValueError("occasion scores must lie in [0, 1]")
        return value

    @field_validator("occasion_specific_to")
    @classmethod
    def _specific_in_taxonomy(cls, value: str | None) -> str | None:
        if value is not None and value not in TAXONOMY_KEYS:
            raise ValueError(f"occasion_specific_to outside the taxonomy: {value}")
        return value


# --------------------------------------------------------------------------- API models


class OccasionOut(BaseModel):
    key: str
    label: str
    icon: str


class RecommendRequest(BaseModel):
    occasion: str = Field(min_length=1, max_length=100)
    top_k: int = Field(default=12, ge=1, le=50)
    max_price: float | None = Field(default=None, gt=0)
    keyword_method: Literal["bm25", "tfidf"] | None = None

    @field_validator("occasion")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("occasion must not be blank")
        return value


class ScoreBreakdown(BaseModel):
    semantic: float
    tag: float
    keyword: float
    name_boost: float
    penalty: float


class RecommendedProduct(BaseModel):
    product_id: str
    title: str
    category: str
    description: str
    description_snippet: str
    image: str | None
    shop: str
    price: float | None
    final_price: float | None
    discount_pct: float
    score: float
    breakdown: ScoreBreakdown
    reasons: list[str]


class QueryInfo(BaseModel):
    raw: str
    matched_occasion: str | None
    matched_label: str | None
    match_type: Literal["exact", "fuzzy", "open_ended"]


class RecommendResponse(BaseModel):
    query: QueryInfo
    results: list[RecommendedProduct]
    total: int
    keyword_method: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    indexes_loaded: bool
    products: int
