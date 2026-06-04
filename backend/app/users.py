"""User persistence for OAuth identities."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.db import get_connection


def upsert_oauth_user(
    *,
    email: str,
    name: str | None,
    provider: str,
    provider_user_id: str,
    avatar_url: str | None,
) -> dict[str, Any]:
    """
    Create or update a user keyed by provider and provider user id.

    Args:
        email: Email from the OAuth profile.
        name: Display name from the provider.
        provider: OAuth provider key (google or github).
        provider_user_id: Stable id from the provider.
        avatar_url: Profile image URL if available.

    Returns:
        User row as a dict including id and timestamps.

    Side effects:
        Inserts or updates a row in users.
    """
    now = datetime.now(UTC)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id, avatar_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (provider, provider_user_id)
                DO UPDATE SET
                  email = EXCLUDED.email,
                  name = EXCLUDED.name,
                  avatar_url = EXCLUDED.avatar_url,
                  updated_at = %s
                RETURNING id, email, name, provider, provider_user_id, avatar_url,
                          created_at, updated_at
                """,
                (email, name, provider, provider_user_id, avatar_url, now),
            )
            row = cur.fetchone()
    if row is None:
        raise RuntimeError("upsert_oauth_user did not return a row")
    return dict(row)


def get_user_by_id(user_id: UUID) -> dict[str, Any] | None:
    """
    Load a user by primary key.

    Args:
        user_id: UUID of the user.

    Returns:
        User dict or None if not found.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, name, provider, provider_user_id, avatar_url,
                       created_at, updated_at
                FROM users WHERE id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None
