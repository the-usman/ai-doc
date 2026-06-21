"""Persistence for agent pipeline runs.

Writes to the ``pipeline_runs`` table defined in ``schema/schema.sql``. Plain
psycopg, no LangChain dependency, so it is unit-tested directly against
PostgreSQL.
"""

from typing import Any
from uuid import UUID

from psycopg.types.json import Json

from app.db import get_connection


def create_pipeline_run(user_id: UUID | str, task: str) -> dict[str, Any]:
    """
    Insert a new pipeline run in the ``running`` state.

    Args:
        user_id: The user who triggered the run.
        task: The task description.

    Returns:
        The inserted run row.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipeline_runs (user_id, task, status)
                VALUES (%s, %s, 'running')
                RETURNING id, user_id, task, status, final_output, trace,
                          started_at, completed_at
                """,
                (str(user_id), task),
            )
            row = cur.fetchone()
    if row is None:
        raise RuntimeError("create_pipeline_run did not return a row")
    return dict(row)


def complete_pipeline_run(
    run_id: UUID | str,
    final_output: str,
    trace: list[dict[str, Any]],
    status: str = "completed",
) -> dict[str, Any]:
    """
    Mark a run finished and store its output and trace.

    Args:
        run_id: The run to update.
        final_output: The synthesised final answer.
        trace: The accumulated worker results, stored as JSON.
        status: Terminal status (``completed`` or ``failed``).

    Returns:
        The updated run row.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE pipeline_runs
                SET status = %s,
                    final_output = %s,
                    trace = %s,
                    completed_at = NOW()
                WHERE id = %s
                RETURNING id, user_id, task, status, final_output, trace,
                          started_at, completed_at
                """,
                (status, final_output, Json(trace), str(run_id)),
            )
            row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"pipeline run {run_id} not found")
    return dict(row)


def fail_pipeline_run(run_id: UUID | str, error: str) -> dict[str, Any]:
    """
    Mark a run failed, recording the error in the trace.

    Args:
        run_id: The run to update.
        error: A short description of the failure.

    Returns:
        The updated run row.
    """
    return complete_pipeline_run(run_id, final_output="", trace=[{"error": error}], status="failed")


def get_recent_runs(limit: int = 20) -> list[dict[str, Any]]:
    """
    Return recent runs in reverse chronological order.

    Args:
        limit: Maximum number of runs to return (clamped to 1–100).

    Returns:
        A list of run rows, newest first.
    """
    safe_limit = max(1, min(int(limit), 100))
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, task, status, final_output, trace,
                       started_at, completed_at
                FROM pipeline_runs
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (safe_limit,),
            )
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_run(run_id: UUID | str) -> dict[str, Any] | None:
    """
    Load a single run by id.

    Args:
        run_id: The run id.

    Returns:
        The run row, or None if not found.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, task, status, final_output, trace,
                       started_at, completed_at
                FROM pipeline_runs
                WHERE id = %s
                """,
                (str(run_id),),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def most_recent_user_id() -> str | None:
    """
    Return the id of the most recently created user, or None if there are none.

    Used to attribute autonomous (n8n-triggered) runs to a real user, since
    ``pipeline_runs.user_id`` is a required foreign key.

    Returns:
        A user id string, or None.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users ORDER BY created_at DESC LIMIT 1")
            row = cur.fetchone()
    return str(row["id"]) if row else None
