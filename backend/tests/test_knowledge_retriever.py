"""Tests for the pgvector-backed retriever.

Both the embedding step and the database search are patched, so the tests cover
the retriever's wiring (query → embed → search → Documents) without OpenAI or a
database.
"""

import pytest

pytest.importorskip("langchain_core")

from app.knowledge import persistence, retriever  # noqa: E402


def _row(title="Guide", index=0, similarity=0.9, text="a chunk") -> dict:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "document_id": "22222222-2222-2222-2222-222222222222",
        "chunk_index": index,
        "chunk_text": text,
        "document_title": title,
        "similarity": similarity,
    }


def test_search_chunks_embeds_then_searches(monkeypatch) -> None:
    """search_chunks embeds the query and forwards the vector to the DB search."""
    seen = {}

    def _fake_search(vector, k=5, user_id=None):
        seen["vector"] = vector
        seen["k"] = k
        return [_row()]

    monkeypatch.setattr(retriever.embeddings, "embed_query", lambda q: [0.1, 0.2])
    monkeypatch.setattr(persistence, "similarity_search", _fake_search)

    rows = retriever.search_chunks("how do I onboard?", k=3)
    assert rows == [_row()]
    assert seen["vector"] == [0.1, 0.2]
    assert seen["k"] == 3


def test_get_retriever_returns_documents_with_metadata(monkeypatch) -> None:
    """The BaseRetriever wraps chunk rows as Documents carrying source metadata."""
    monkeypatch.setattr(
        retriever,
        "search_chunks",
        lambda query, k=None, user_id=None: [_row(title="Onboarding", index=2, similarity=0.8)],
    )
    docs = retriever.get_retriever(k=5).invoke("onboarding steps")
    assert len(docs) == 1
    doc = docs[0]
    assert doc.page_content == "a chunk"
    assert doc.metadata["document_title"] == "Onboarding"
    assert doc.metadata["chunk_index"] == 2
    assert doc.metadata["similarity"] == 0.8
