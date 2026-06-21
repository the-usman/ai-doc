"""Orchestration: run the pipeline and persist the result.

Sits between the HTTP routes and the graph so both the interactive and the
autonomous (n8n) entry points share one code path: create a run row, execute the
graph, then record the outcome.
"""

from typing import Any
from uuid import UUID

from app.agents import persistence
from app.agents.graph import run_pipeline


def execute_pipeline(user_id: UUID | str, task: str) -> dict[str, Any]:
    """
    Run the agent pipeline for a task and persist the run.

    Args:
        user_id: The user the run is attributed to.
        task: The task description.

    Returns:
        The persisted run row (completed or failed).

    Side effects:
        Inserts and updates a row in ``pipeline_runs`` and executes the graph.
    """
    run = persistence.create_pipeline_run(user_id, task)
    run_id = run["id"]
    try:
        final = run_pipeline(task)
    except Exception as exc:  # pragma: no cover - defensive; surfaced as failed
        return persistence.fail_pipeline_run(run_id, str(exc))
    return persistence.complete_pipeline_run(
        run_id,
        final_output=final.get("final_output", ""),
        trace=final.get("worker_results", []),
        status=final.get("status", "completed"),
    )
