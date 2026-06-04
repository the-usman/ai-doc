"""Database constraint tests."""

from uuid import uuid4

import psycopg
import pytest

from app.db import get_connection


def test_users_unique_provider_and_provider_user_id() -> None:
    """users table rejects duplicate (provider, provider_user_id)."""
    provider_user_id = str(uuid4())
    email = f"constraint-{uuid4()}@example.com"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, provider, provider_user_id)
                VALUES (%s, %s, 'google', %s)
                """,
                (email, "First", provider_user_id),
            )

    with pytest.raises(psycopg.errors.UniqueViolation):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (email, name, provider, provider_user_id)
                    VALUES (%s, %s, 'google', %s)
                    """,
                    (f"other-{uuid4()}@example.com", "Second", provider_user_id),
                )
