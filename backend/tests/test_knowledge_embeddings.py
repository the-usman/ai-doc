"""Tests for the embedding factory and helpers.

The OpenAI client is never constructed for real; ``get_embeddings`` is patched so
no network call or API key is required.
"""

import pytest

from app.config import get_settings
from app.knowledge import embeddings


def test_get_embeddings_requires_api_key(monkeypatch) -> None:
    """With no OpenAI key configured, building the client raises RuntimeError."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        embeddings.get_embeddings()


def test_embed_texts_empty_returns_empty() -> None:
    """Embedding an empty batch short-circuits without touching the model."""
    assert embeddings.embed_texts([]) == []


def test_embed_texts_delegates_to_client(monkeypatch) -> None:
    """embed_texts forwards to the client's embed_documents."""

    class _FakeClient:
        def embed_documents(self, texts):
            return [[float(len(t))] for t in texts]

    monkeypatch.setattr(embeddings, "get_embeddings", lambda: _FakeClient())
    assert embeddings.embed_texts(["ab", "abcd"]) == [[2.0], [4.0]]


def test_embed_query_delegates_to_client(monkeypatch) -> None:
    """embed_query forwards to the client's embed_query."""

    class _FakeClient:
        def embed_query(self, text):
            return [1.0, 2.0, 3.0]

    monkeypatch.setattr(embeddings, "get_embeddings", lambda: _FakeClient())
    assert embeddings.embed_query("hello") == [1.0, 2.0, 3.0]
