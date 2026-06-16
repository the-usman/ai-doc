"""Tests for the authenticated chat HTTP route."""

from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from app.auth_routes import SESSION_COOKIE  # noqa: E402
from app.chat.schemas import ChatResponse  # noqa: E402
from app.db import get_connection  # noqa: E402
from app.sessions import create_session  # noqa: E402


def _logged_in_token() -> str:
    """Create a user + session and return the session token."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, 'Route Tester', 'google', %s)
                RETURNING id
                """,
                (f"route-{uuid4()}@example.com", str(uuid4())),
            )
            user_id = cur.fetchone()["id"]
    return create_session(user_id)["token"]


def test_chat_message_requires_auth(client) -> None:
    """Without a session cookie the chat route returns 401."""
    response = client.post("/api/chat/message", json={"message": "hi"})
    assert response.status_code == 401


def test_chat_message_returns_structured_response(client, monkeypatch) -> None:
    """An authenticated message returns the structured answer."""
    monkeypatch.setattr(
        "app.chat.routes.invoke_chat",
        lambda session_id, message: ChatResponse(
            response="There are 3 users.",
            confidence="high",
            sources=["get_platform_user_count"],
        ),
    )
    token = _logged_in_token()
    response = client.post(
        "/api/chat/message",
        json={"message": "how many users?"},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "There are 3 users."
    assert data["confidence"] == "high"
    assert data["sources"] == ["get_platform_user_count"]


def test_chat_message_surfaces_unconfigured_model(client, monkeypatch) -> None:
    """A missing API key surfaces as a 503, not a 500."""

    def _raise(session_id, message):
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    monkeypatch.setattr("app.chat.routes.invoke_chat", _raise)
    token = _logged_in_token()
    response = client.post(
        "/api/chat/message",
        json={"message": "hi"},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 503
