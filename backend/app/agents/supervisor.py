"""Supervisor node: routes the task to a worker or finishes the run.

The supervisor is the entry node and the node the graph returns to after every
worker. It is implemented as an LCEL chain with structured output: the model
returns a :class:`RouteDecision` whose ``next`` field is a worker name or
``"FINISH"``, which makes the graph's conditional edge trivial (route on
``state["next"]``). See ADR-007.
"""

from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_chat_model
from app.agents.state import PipelineState, WorkerResult

WORKER_NAMES = ["DataAgent", "ReportAgent"]

# Safety bound: even if the model never says FINISH, stop after this many worker
# invocations so a run cannot loop forever.
MAX_WORKER_STEPS = 6

_SUPERVISOR_PROMPT = (
    "You are the supervisor of a small team of agents working on one task.\n"
    "Workers available:\n"
    "- DataAgent: answers questions about platform users and sign-in activity "
    "using database tools.\n"
    "- ReportAgent: synthesises the gathered results into a brief written "
    "summary.\n\n"
    "Read the task and the results gathered so far, then decide the single next "
    "step. Route to DataAgent to gather data, to ReportAgent to summarise once "
    "enough data is gathered, or FINISH when the task is complete. Do not repeat "
    "a worker that has already done its job."
)


class RouteDecision(BaseModel):
    """Structured routing decision produced by the supervisor."""

    next: Literal["DataAgent", "ReportAgent", "FINISH"] = Field(
        description="The next worker to run, or FINISH to end the run."
    )
    reason: str = Field(default="", description="Why this route was chosen.")


def get_router() -> Any:
    """
    Return the model constrained to emit a :class:`RouteDecision`.

    Returns:
        A runnable that parses the model output into ``RouteDecision``.
    """
    return get_chat_model().with_structured_output(RouteDecision)


def _describe(state: PipelineState) -> str:
    """Render the task and accumulated results for the supervisor prompt."""
    lines = [f"Task: {state.get('task', '')}", "", "Results so far:"]
    results = state.get("worker_results", [])
    if not results:
        lines.append("(none yet)")
    else:
        for item in results:
            lines.append(f"- {item['worker']}: {item['output']}")
    return "\n".join(lines)


def _synthesise(state: PipelineState) -> str:
    """Build the final output from accumulated worker results."""
    results: list[WorkerResult] = state.get("worker_results", [])
    for item in reversed(results):
        if item["worker"] == "ReportAgent":
            return item["output"]
    if results:
        return "\n".join(f"{i['worker']}: {i['output']}" for i in results)
    return "No results were produced."


def _finish(state: PipelineState) -> dict:
    """Return the state update that ends the run."""
    return {
        "next": "FINISH",
        "final_output": _synthesise(state),
        "status": "completed",
    }


def supervisor_node(state: PipelineState) -> dict:
    """
    Decide the next step for the pipeline.

    Args:
        state: The current pipeline state.

    Returns:
        A state update containing ``next`` (and, when finishing, the
        ``final_output`` and ``status``).
    """
    if len(state.get("worker_results", [])) >= MAX_WORKER_STEPS:
        return _finish(state)

    decision: RouteDecision = get_router().invoke(
        [SystemMessage(content=_SUPERVISOR_PROMPT), HumanMessage(content=_describe(state))]
    )
    if decision.next == "FINISH":
        return _finish(state)
    return {"next": decision.next}
