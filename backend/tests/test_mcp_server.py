"""Tests for the minimal MCP server."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db import get_connection
from app.mcp_server import app

mcp_client = TestClient(app)


def _seed_user_with_session() -> None:
    """Insert a user and session so the tools return data."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, 'MCP Tester', 'google', %s)
                RETURNING id
                """,
                (f"mcp-{uuid4()}@example.com", str(uuid4())),
            )
            user_id = cur.fetchone()["id"]
            cur.execute(
                """
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (%s, %s, NOW() + INTERVAL '1 day')
                """,
                (user_id, str(uuid4())),
            )


def test_manifest_lists_both_tools() -> None:
    """The manifest advertises both database-backed tools with schemas."""
    response = mcp_client.get("/mcp/tools")
    assert response.status_code == 200
    names = {t["name"] for t in response.json()["tools"]}
    assert names == {"get_platform_user_count", "get_recent_signins"}
    for tool in response.json()["tools"]:
        assert "input_schema" in tool


def test_call_user_count_executes_query() -> None:
    """Calling get_platform_user_count runs the real query."""
    _seed_user_with_session()
    response = mcp_client.post(
        "/mcp/call", json={"name": "get_platform_user_count", "arguments": {}}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool"] == "get_platform_user_count"
    assert isinstance(body["result"], int)
    assert body["result"] >= 1


def test_call_recent_signins_respects_limit() -> None:
    """Calling get_recent_signins returns at most `limit` rows."""
    _seed_user_with_session()
    response = mcp_client.post(
        "/mcp/call", json={"name": "get_recent_signins", "arguments": {"limit": 2}}
    )
    assert response.status_code == 200
    assert len(response.json()["result"]) <= 2


def test_unknown_tool_returns_404() -> None:
    """An unknown tool name is rejected."""
    response = mcp_client.post("/mcp/call", json={"name": "nope", "arguments": {}})
    assert response.status_code == 404
