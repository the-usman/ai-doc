"""Database queries backing the chat tools and the MCP server.

These are plain functions with no LangChain dependency so they can be:

* wrapped as LangChain ``@tool`` callables (see ``tools.py``),
* exposed over the Model Context Protocol (see ``app.mcp_server``), and
* unit-tested directly against PostgreSQL without importing LangChain.

Every function queries the real database through ``app.db.get_connection`` —
there is no mock data anywhere in this module.
"""

from typing import Any

from app.db import get_connection


def count_platform_users() -> int:
    """
    Count the number of registered platform users.

    Returns:
        Total number of rows in the ``users`` table.

    Side effects:
        Executes a read-only ``SELECT COUNT(*)`` against PostgreSQL.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS count FROM users")
            row = cur.fetchone()
    return int(row["count"]) if row else 0


def recent_signins(limit: int = 5) -> list[dict[str, Any]]:
    """
    Return the most recent sign-in events from the sessions table.

    Args:
        limit: Maximum number of events to return. Values are clamped to the
            range 1–50 so a misbehaving caller cannot request an unbounded scan.

    Returns:
        A list of dicts (newest first) each containing ``email``, ``name``,
        ``provider`` and ``signed_in_at`` (ISO 8601 string).

    Side effects:
        Executes a read-only join of ``sessions`` and ``users``.
    """
    safe_limit = max(1, min(int(limit), 50))
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.email, u.name, u.provider, s.created_at AS signed_in_at
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                ORDER BY s.created_at DESC
                LIMIT %s
                """,
                (safe_limit,),
            )
            rows = cur.fetchall()
    return [
        {
            "email": r["email"],
            "name": r["name"],
            "provider": r["provider"],
            "signed_in_at": r["signed_in_at"].isoformat(),
        }
        for r in rows
    ]


def provider_breakdown() -> dict[str, int]:
    """
    Count registered users grouped by OAuth provider.

    Returns:
        A mapping of provider key (e.g. ``google``, ``github``) to user count.

    Side effects:
        Executes a read-only grouped ``SELECT`` against PostgreSQL.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT provider, COUNT(*) AS count
                FROM users
                GROUP BY provider
                ORDER BY provider
                """
            )
            rows = cur.fetchall()
    return {r["provider"]: int(r["count"]) for r in rows}
