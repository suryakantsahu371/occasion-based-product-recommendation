"""Shared fixtures. Indexes and the embedding model load once per test session."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adapter import load_products  # noqa: E402
from app.config import Settings, get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.ranker import Recommender  # noqa: E402
from app.retriever import Retriever  # noqa: E402


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def all_products(settings):
    return load_products(settings.products_path, settings)


@pytest.fixture(scope="session")
def recommender(settings) -> Recommender:
    return Recommender(Retriever.load(settings))


@pytest.fixture(scope="session")
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


def titles(response, n: int | None = None) -> list[str]:
    """Result titles of a ``RecommendResponse`` (optionally the first ``n``)."""
    out = [r.title for r in response.results]
    return out[:n] if n else out
