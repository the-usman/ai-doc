"""Tests for the Knowledge HTTP surface.

Auth uses a real user + session (as in the chat/agents route tests). Ingestion,
the RAG chain, and retrieval are patched so no OpenAI/Anthropic call or embedding
happens; the routes' own behaviour — auth, validation, serialisation — is what is
under test.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from app.auth_routes import SESSION_COOKIE  # noqa: E402
from app.db import get_connection  # noqa: E402
from app.knowledge import chain, ingestion, persistence, retriever, routes  # noqa: E402
from app.knowledge.schemas import KnowledgeResponse, SourceChunk  # noqa: E402
from app.sessions import create_session  # noqa: E402


def _logged_in() -> tuple[str, str]:
    """Create a user + session; return (user_id, session token)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, 'KB Route Tester', 'google', %s)
                RETURNING id
                """,
                (f"kbroute-{uuid4()}@example.com", str(uuid4())),
            )
            user_id = cur.fetchone()["id"]
    return str(user_id), create_session(user_id)["token"]


def test_list_documents_requires_auth(client) -> None:
    """Without a session cookie, listing documents is unauthorized."""
    assert client.get("/api/knowledge/documents").status_code == 401


def test_upload_rejects_unsupported_type(client) -> None:
    """An unsupported file type is rejected with 400 before any ingestion."""
    _, token = _logged_in()
    response = client.post(
        "/api/knowledge/documents",
        data={"title": "Pic"},
        files={"file": ("photo.png", b"\x89PNG", "image/png")},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file(client) -> None:
    """An empty file is rejected with 400."""
    _, token = _logged_in()
    response = client.post(
        "/api/knowledge/documents",
        data={"title": "Empty"},
        files={"file": ("empty.txt", b"", "text/plain")},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 400


def test_upload_indexes_document(client, monkeypatch) -> None:
    """A valid upload extracts text and returns the indexed document summary."""
    user_id, token = _logged_in()
    captured = {}

    def _fake_ingest(uid, title, source_name, text):
        captured.update(uid=uid, title=title, source_name=source_name, text=text)
        return {
            "id": uuid4(),
            "title": title,
            "source_name": source_name,
            "chunk_count": 3,
            "created_at": datetime.now(UTC),
        }

    monkeypatch.setattr(ingestion, "ingest_document", _fake_ingest)
    response = client.post(
        "/api/knowledge/documents",
        data={"title": "Notes"},
        files={"file": ("notes.txt", b"hello knowledge base", "text/plain")},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Notes"
    assert body["chunk_count"] == 3
    assert captured["text"] == "hello knowledge base"
    assert captured["uid"] == user_id


def test_upload_surfaces_missing_embeddings_as_503(client, monkeypatch) -> None:
    """A RuntimeError from ingestion (no API key) maps to 503."""
    _, token = _logged_in()

    def _boom(*args, **kwargs):
        raise RuntimeError("OPENAI_API_KEY is not configured")

    monkeypatch.setattr(ingestion, "ingest_document", _boom)
    response = client.post(
        "/api/knowledge/documents",
        data={"title": "Notes"},
        files={"file": ("notes.txt", b"some text", "text/plain")},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 503


def test_chat_returns_answer_and_sources(client, monkeypatch) -> None:
    """The chat route returns the grounded answer with its source chunks."""
    _, token = _logged_in()
    monkeypatch.setattr(
        chain,
        "answer_question",
        lambda session_id, question, user_id: KnowledgeResponse(
            answer="Onboarding takes a day (Guide).",
            answer_found=True,
            sources=[
                SourceChunk(
                    document_id="d1",
                    document_title="Guide",
                    chunk_index=0,
                    similarity=0.9,
                    snippet="onboarding...",
                )
            ],
        ),
    )
    response = client.post(
        "/api/knowledge/chat",
        json={"question": "how long is onboarding?"},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer_found"] is True
    assert body["sources"][0]["document_title"] == "Guide"


def test_chat_requires_auth(client) -> None:
    """The chat route requires a session."""
    response = client.post("/api/knowledge/chat", json={"question": "hi"})
    assert response.status_code == 401


def test_search_returns_ranked_chunks(client, monkeypatch) -> None:
    """The search route returns chunks with rounded similarity scores."""
    _, token = _logged_in()
    monkeypatch.setattr(
        retriever,
        "search_chunks",
        lambda query, user_id=None: [
            {
                "document_id": "d1",
                "document_title": "Spec",
                "chunk_index": 2,
                "chunk_text": "matched text",
                "similarity": 0.823456,
            }
        ],
    )
    response = client.post(
        "/api/knowledge/search",
        json={"query": "spec details"},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["document_title"] == "Spec"
    assert result["similarity"] == 0.8235
    assert result["text"] == "matched text"


def test_delete_unknown_document_returns_404(client) -> None:
    """Deleting a non-existent document returns 404."""
    _, token = _logged_in()
    response = client.delete(
        f"/api/knowledge/documents/{uuid4()}", cookies={SESSION_COOKIE: token}
    )
    assert response.status_code == 404
