"""Database-backed tests for the chat query helpers."""

from uuid import uuid4

from app.chat import queries
from app.db import get_connection


def _seed_user_with_session() -> str:
    """Insert a user and a session, returning the user's email."""
    email = f"chat-{uuid4()}@example.com"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, %s, 'google', %s)
                RETURNING id
                """,
                (email, "Chat Tester", str(uuid4())),
            )
            user_id = cur.fetchone()["id"]
            cur.execute(
                """
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (%s, %s, NOW() + INTERVAL '1 day')
                """,
                (user_id, str(uuid4())),
            )
    return email


def test_count_platform_users_counts_rows() -> None:
    """count_platform_users reflects newly inserted users."""
    before = queries.count_platform_users()
    _seed_user_with_session()
    after = queries.count_platform_users()
    assert after == before + 1


def test_recent_signins_returns_newest_first() -> None:
    """recent_signins returns the seeded sign-in with expected fields."""
    email = _seed_user_with_session()
    rows = queries.recent_signins(limit=5)
    assert rows, "expected at least one recent sign-in"
    assert {"email", "name", "provider", "signed_in_at"} <= set(rows[0].keys())
    assert any(r["email"] == email for r in rows)


def test_recent_signins_clamps_limit() -> None:
    """recent_signins clamps the limit to a safe upper bound."""
    _seed_user_with_session()
    rows = queries.recent_signins(limit=10_000)
    assert len(rows) <= 50
