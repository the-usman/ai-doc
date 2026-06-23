"""Tests for the document ingestion pipeline.

Persistence, splitting, and embedding are patched so the test covers the
pipeline's wiring — persist, split, embed, store — without a database or OpenAI.
"""

import pytest

from app.knowledge import ingestion


def test_ingest_document_splits_embeds_and_stores(monkeypatch) -> None:
    """Each chunk is embedded and stored with its index, and the count returned."""
    created = {"id": "doc-1", "title": "Guide", "source_name": "guide.txt"}
    captured = {}

    monkeypatch.setattr(
        ingestion.persistence,
        "create_document",
        lambda user_id, title, source_name, raw_text: created,
    )
    monkeypatch.setattr(
        ingestion.splitter, "split_text", lambda text: ["chunk a", "chunk b"]
    )
    monkeypatch.setattr(
        ingestion.embeddings, "embed_texts", lambda texts: [[0.1], [0.2]]
    )

    def _insert(document_id, chunks):
        captured["document_id"] = document_id
        captured["chunks"] = chunks
        return len(chunks)

    monkeypatch.setattr(ingestion.persistence, "insert_chunks", _insert)

    result = ingestion.ingest_document("user-1", "Guide", "guide.txt", "raw text")

    assert result["chunk_count"] == 2
    assert result["id"] == "doc-1"
    assert captured["document_id"] == "doc-1"
    assert captured["chunks"][0] == {"chunk_index": 0, "chunk_text": "chunk a", "embedding": [0.1]}
    assert captured["chunks"][1] == {"chunk_index": 1, "chunk_text": "chunk b", "embedding": [0.2]}


def test_ingest_document_mismatched_lengths_raise(monkeypatch) -> None:
    """A chunk/vector count mismatch is caught by the strict zip."""
    monkeypatch.setattr(
        ingestion.persistence,
        "create_document",
        lambda user_id, title, source_name, raw_text: {"id": "doc-1"},
    )
    monkeypatch.setattr(ingestion.splitter, "split_text", lambda text: ["a", "b"])
    monkeypatch.setattr(ingestion.embeddings, "embed_texts", lambda texts: [[0.1]])
    monkeypatch.setattr(ingestion.persistence, "insert_chunks", lambda doc_id, chunks: len(chunks))

    with pytest.raises(ValueError):
        ingestion.ingest_document("user-1", "Guide", "guide.txt", "raw text")
