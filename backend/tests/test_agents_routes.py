"""Tests for the Agents HTTP surface.

`execute_pipeline` is patched everywhere so no graph or LLM runs; the route's own
behaviour — auth, serialisation, trigger-token handling — is what is under test.
The session-backed routes create a real user + session, matching the chat tests.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from app.agents import persistence, routes  # noqa: E402
from app.auth_routes import SESSION_COOKIE  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import get_connection  # noqa: E402
from app.sessions import create_session  # noqa: E402


def _logged_in() -> tuple[str, str]:
    """Create a user + session; return (user_id, session token)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, 'Agents Tester', 'google', %s)
                RETURNING id
                """,
                (f"agents-{uuid4()}@example.com", str(uuid4())),
            )
            user_id = cur.fetchone()["id"]
    return str(user_id), create_session(user_id)["token"]


def _fake_run(user_id: str, task: str = "a task") -> dict:
    """A persisted-run-shaped dict with real datetimes for serialisation."""
    now = datetime.now(UTC)
    return {
        "id": uuid4(),
        "user_id": user_id,
        "task": task,
        "status": "completed",
        "final_output": "done",
        "trace": [{"worker": "DataAgent", "output": "data"}],
        "started_at": now,
        "completed_at": now,
    }


def test_run_requires_auth(client) -> None:
    """Without a session cookie the run route returns 401."""
    response = client.post("/api/agents/run", json={"task": "hi"})
    assert response.status_code == 401


def test_run_returns_serialised_run(client, monkeypatch) -> None:
    """An authenticated run returns the serialised completed run with its trace."""
    user_id, token = _logged_in()
    monkeypatch.setattr(routes, "execute_pipeline", lambda uid, task: _fake_run(uid, task))
    response = client.post(
        "/api/agents/run",
        json={"task": "count users"},
        cookies={SESSION_COOKIE: token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["task"] == "count users"
    assert data["trace"] == [{"worker": "DataAgent", "output": "data"}]


def test_list_runs_returns_recent(client, monkeypatch) -> None:
    """The runs route returns the recent runs serialised under `runs`."""
    user_id, token = _logged_in()
    monkeypatch.setattr(persistence, "get_recent_runs", lambda limit=25: [_fake_run(user_id)])
    response = client.get("/api/agents/runs", cookies={SESSION_COOKIE: token})
    assert response.status_code == 200
    assert len(response.json()["runs"]) == 1


def test_trigger_disabled_without_token(client, monkeypatch) -> None:
    """With no configured secret the trigger endpoint is disabled (503)."""
    monkeypatch.setenv("AGENTS_TRIGGER_TOKEN", "")
    get_settings.cache_clear()
    response = client.post("/api/agents/trigger", json={"task": "go"})
    assert response.status_code == 503


def test_trigger_rejects_bad_token(client, monkeypatch) -> None:
    """A mismatched token is rejected with 401."""
    monkeypatch.setenv("AGENTS_TRIGGER_TOKEN", "right-secret")
    get_settings.cache_clear()
    response = client.post(
        "/api/agents/trigger",
        json={"task": "go"},
        headers={"X-Trigger-Token": "wrong-secret"},
    )
    assert response.status_code == 401


def test_trigger_runs_with_valid_token(client, monkeypatch) -> None:
    """A valid token starts a run and returns its id and status."""
    user_id, _ = _logged_in()
    monkeypatch.setenv("AGENTS_TRIGGER_TOKEN", "right-secret")
    get_settings.cache_clear()
    monkeypatch.setattr(persistence, "most_recent_user_id", lambda: user_id)
    monkeypatch.setattr(routes, "execute_pipeline", lambda uid, task: _fake_run(uid, task))
    response = client.post(
        "/api/agents/trigger",
        json={"task": "go"},
        headers={"X-Trigger-Token": "right-secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert "run_id" in body
