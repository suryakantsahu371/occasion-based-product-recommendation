"""FastAPI application: loads indexes once at startup and serves the recommendation API."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.ranker import Recommender
from app.retriever import Retriever
from app.schemas import HealthResponse, OccasionOut, RecommendRequest, RecommendResponse
from app.taxonomy import OCCASIONS

log = logging.getLogger("occasion_recommender")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory (the settings override keeps tests independent of the environment)."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        started = time.perf_counter()
        retriever = Retriever.load(settings)
        app.state.recommender = Recommender(retriever)
        log.info(
            "indexes loaded products=%d model=%s in %.1fs",
            len(retriever.products),
            settings.embedding_model,
            time.perf_counter() - started,
        )
        yield

    app = FastAPI(title="Occasion-Based Product Recommender", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        """Liveness plus whether the indexes finished loading."""
        recommender: Recommender | None = getattr(request.app.state, "recommender", None)
        return HealthResponse(
            status="ok" if recommender else "loading",
            indexes_loaded=recommender is not None,
            products=len(recommender.retriever.products) if recommender else 0,
        )

    @app.get("/api/occasions", response_model=list[OccasionOut])
    def occasions() -> list[OccasionOut]:
        """The occasion taxonomy, for autocomplete and quick-pick chips."""
        return [OccasionOut(key=o.key, label=o.label, icon=o.icon) for o in OCCASIONS]

    @app.post("/api/recommend", response_model=RecommendResponse)
    def recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
        """Rank catalog products for a free-text occasion."""
        recommender: Recommender | None = getattr(request.app.state, "recommender", None)
        if recommender is None:
            raise HTTPException(status_code=503, detail="indexes are still loading")
        started = time.perf_counter()
        response = recommender.recommend(body.occasion, body.top_k, body.max_price, body.keyword_method)
        response.latency_ms = round((time.perf_counter() - started) * 1000, 1)
        # The raw query is user input, so only derived, non-identifying fields are logged.
        log.info(
            "recommend matched=%s type=%s results=%d latency_ms=%.1f",
            response.query.matched_occasion,
            response.query.match_type,
            response.total,
            response.latency_ms,
        )
        return response

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = create_app()
