"""Session token storage and validation."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.db import get_connection

SESSION_TTL_DAYS = 7


def create_session(user_id: UUID) -> dict[str, Any]:
    """
    Issue a new session token for a user.

    Args:
        user_id: Owner of the session.

    Returns:
        Session row including token and expires_at.

    Side effects:
        Inserts into sessions.
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=SESSION_TTL_DAYS)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, token, expires_at, created_at, updated_at
                """,
                (user_id, token, expires_at),
            )
            row = cur.fetchone()
    if row is None:
        raise RuntimeError("create_session did not return a row")
    return dict(row)


def get_active_session(token: str) -> dict[str, Any] | None:
    """
    Resolve a session token to user details if not expired.

    Args:
        token: Session token from cookie.

    Returns:
        Joined session and user fields, or None if invalid/expired.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id AS session_id, s.user_id, s.expires_at,
                       u.email, u.name, u.provider, u.avatar_url
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = %s AND s.expires_at > NOW()
                """,
                (token,),
            )
            row = cur.fetchone()
    return dict(row) if row else None
