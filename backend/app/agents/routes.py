"""HTTP surface for the Agents application.

* ``POST /api/agents/run`` — authenticated; runs the pipeline for the signed-in
  user and returns the completed run (task, status, final output, trace).
* ``GET  /api/agents/runs`` — authenticated; recent runs for the Run History page.
* ``GET  /api/agents/runs/{id}`` — authenticated; a single run with its trace.
* ``POST /api/agents/trigger`` — token-protected; the endpoint n8n calls to start
  a run autonomously. Returns the run id immediately-style payload.
"""

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.agents import persistence
from app.agents.service import execute_pipeline
from app.auth_routes import SESSION_COOKIE
from app.config import get_settings
from app.sessions import get_active_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


class RunRequest(BaseModel):
    """Body for starting a pipeline run."""

    task: str = Field(min_length=1, description="The task for the agent pipeline.")


def _require_session(request: Request) -> dict:
    """
    Resolve the active session from the cookie.

    Args:
        request: Incoming HTTP request.

    Returns:
        Joined session and user fields.

    Raises:
        HTTPException: 401 when unauthenticated or expired.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session


def _serialize(run: dict[str, Any]) -> dict[str, Any]:
    """Convert a run row into a JSON-friendly dict."""
    return {
        "id": str(run["id"]),
        "user_id": str(run["user_id"]),
        "task": run["task"],
        "status": run["status"],
        "final_output": run.get("final_output"),
        "trace": run.get("trace") or [],
        "started_at": run["started_at"].isoformat() if run.get("started_at") else None,
        "completed_at": (run["completed_at"].isoformat() if run.get("completed_at") else None),
    }


@router.post("/run")
def run_agents(request: Request, payload: RunRequest) -> dict[str, Any]:
    """
    Run the pipeline for the signed-in user and return the completed run.

    Args:
        request: Incoming request (provides the session cookie).
        payload: The task to run.

    Returns:
        The serialised run.

    Raises:
        HTTPException: 401 if unauthenticated, 503 if the model is unconfigured.
    """
    session = _require_session(request)
    try:
        run = execute_pipeline(session["user_id"], payload.task)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _serialize(run)


@router.get("/runs")
def list_runs(request: Request) -> dict[str, list[dict[str, Any]]]:
    """
    List recent pipeline runs for the Run History page.

    Args:
        request: Incoming request (provides the session cookie).

    Returns:
        A JSON object with a ``runs`` list, newest first.
    """
    _require_session(request)
    runs = persistence.get_recent_runs(limit=25)
    return {"runs": [_serialize(r) for r in runs]}


@router.get("/runs/{run_id}")
def get_run(request: Request, run_id: str) -> dict[str, Any]:
    """
    Return a single run with its trace.

    Args:
        request: Incoming request (provides the session cookie).
        run_id: The run id.

    Returns:
        The serialised run.

    Raises:
        HTTPException: 404 if the run does not exist.
    """
    _require_session(request)
    run = persistence.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _serialize(run)


@router.post("/trigger")
def trigger_run(
    payload: RunRequest,
    x_trigger_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """
    Start a pipeline run autonomously (called by n8n).

    Authenticated with a shared secret header rather than a session cookie, so a
    scheduler can call it without a browser. The run is attributed to the most
    recently created user.

    Args:
        payload: The task to run.
        x_trigger_token: Shared secret in the ``X-Trigger-Token`` header.

    Returns:
        A small payload with the run id and status.

    Raises:
        HTTPException: 503 if the trigger is disabled, 401 on a bad token,
            409 if there is no user to attribute the run to.
    """
    settings = get_settings()
    if not settings.agents_trigger_token:
        raise HTTPException(status_code=503, detail="Trigger endpoint is disabled")
    if x_trigger_token != settings.agents_trigger_token:
        raise HTTPException(status_code=401, detail="Invalid trigger token")

    user_id = persistence.most_recent_user_id()
    if not user_id:
        raise HTTPException(status_code=409, detail="No user to attribute the run to")

    run = execute_pipeline(user_id, payload.task)
    return {"run_id": str(run["id"]), "status": run["status"]}
