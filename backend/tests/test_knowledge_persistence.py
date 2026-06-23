"""Database-backed tests for document and chunk persistence.

These require the Postgres test database with the pgvector extension and the
Phase 4 tables (as in CI). They exercise the real SQL: insert, list with chunk
counts, cosine similarity search, and cascade delete.
"""

from uuid import uuid4

from app.db import get_connection
from app.knowledge import persistence


def _seed_user() -> str:
    """Insert a user and return its id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, 'Knowledge Tester', 'google', %s)
                RETURNING id
                """,
                (f"kb-{uuid4()}@example.com", str(uuid4())),
            )
            return str(cur.fetchone()["id"])


def _unit_vector(hot: int = 0) -> list[float]:
    """A 1536-dim vector with a single non-zero component."""
    vec = [0.0] * 1536
    vec[hot] = 1.0
    return vec


def test_create_and_list_document_with_chunk_count() -> None:
    """A created document is listed for its owner with the right chunk count."""
    user_id = _seed_user()
    doc = persistence.create_document(user_id, "Onboarding Guide", "guide.txt", "full text")
    assert doc["title"] == "Onboarding Guide"

    persistence.insert_chunks(
        doc["id"],
        [
            {"chunk_index": 0, "chunk_text": "chunk zero", "embedding": _unit_vector(0)},
            {"chunk_index": 1, "chunk_text": "chunk one", "embedding": _unit_vector(1)},
        ],
    )

    listed = persistence.list_documents(user_id)
    assert len(listed) == 1
    assert listed[0]["chunk_count"] == 2


def test_list_documents_is_scoped_to_user() -> None:
    """A user only sees their own documents."""
    owner = _seed_user()
    other = _seed_user()
    persistence.create_document(owner, "Mine", "mine.txt", "text")
    assert [d["title"] for d in persistence.list_documents(owner)] == ["Mine"]
    assert persistence.list_documents(other) == []


def test_similarity_search_returns_nearest_chunk() -> None:
    """An identical query vector retrieves the chunk with similarity ~1.0."""
    user_id = _seed_user()
    doc = persistence.create_document(user_id, "Vectors", "vectors.txt", "text")
    persistence.insert_chunks(
        doc["id"],
        [{"chunk_index": 0, "chunk_text": "the only chunk", "embedding": _unit_vector(0)}],
    )

    rows = persistence.similarity_search(_unit_vector(0), k=5, user_id=user_id)
    assert rows
    top = rows[0]
    assert top["chunk_text"] == "the only chunk"
    assert top["document_title"] == "Vectors"
    assert top["similarity"] > 0.99


def test_delete_document_cascades_and_is_owner_scoped() -> None:
    """Deleting removes the document; a non-owner cannot delete it."""
    owner = _seed_user()
    other = _seed_user()
    doc = persistence.create_document(owner, "Doomed", "doomed.txt", "text")
    persistence.insert_chunks(
        doc["id"],
        [{"chunk_index": 0, "chunk_text": "c", "embedding": _unit_vector(0)}],
    )

    # A different user cannot delete it.
    assert persistence.delete_document(doc["id"], other) is False
    # The owner can, and the chunks cascade away.
    assert persistence.delete_document(doc["id"], owner) is True
    assert persistence.list_documents(owner) == []
