"""Tests for the LangChain tool wrappers."""

from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from app.chat import tools  # noqa: E402
from app.db import get_connection  # noqa: E402


def _seed_user_with_session() -> None:
    """Insert one user and session so the tools have data to return."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, 'Tool Tester', 'github', %s)
                RETURNING id
                """,
                (f"tool-{uuid4()}@example.com", str(uuid4())),
            )
            user_id = cur.fetchone()["id"]
            cur.execute(
                """
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (%s, %s, NOW() + INTERVAL '1 day')
                """,
                (user_id, str(uuid4())),
            )


def test_tools_have_descriptive_names() -> None:
    """Tool names match what the chain and MCP server reference."""
    names = {t.name for t in tools.TOOLS}
    assert names == {"get_platform_user_count", "get_recent_signins"}


def test_get_platform_user_count_tool_queries_db() -> None:
    """Invoking the count tool returns the live integer count."""
    _seed_user_with_session()
    result = tools.get_platform_user_count.invoke({})
    assert isinstance(result, int)
    assert result >= 1


def test_get_recent_signins_tool_returns_rows() -> None:
    """Invoking the recent-signins tool returns structured rows."""
    _seed_user_with_session()
    rows = tools.get_recent_signins.invoke({"limit": 3})
    assert isinstance(rows, list)
    assert len(rows) <= 3
    assert "provider" in rows[0]
