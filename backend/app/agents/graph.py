"""Assembly and execution of the supervisor/worker StateGraph.

Topology:

    START -> supervisor -> (conditional) -> DataAgent ---> supervisor
                                          -> ReportAgent -> supervisor
                                          -> END

The conditional edge routes on ``state["next"]``; each worker returns to the
supervisor, which decides the next step until it emits ``FINISH``.
"""

from typing import Any

from app.agents import supervisor, workers
from app.agents.state import PipelineState


def _route(state: PipelineState) -> str:
    """
    Map the supervisor's decision to the next graph node.

    Args:
        state: The current pipeline state.

    Returns:
        The next worker name, or the END sentinel.
    """
    from langgraph.graph import END

    nxt = state.get("next", "")
    if nxt in ("DataAgent", "ReportAgent"):
        return nxt
    return END


def build_graph() -> Any:
    """
    Build and compile the supervisor/worker graph.

    Node functions are looked up on their modules at call time, so tests can
    patch ``supervisor.supervisor_node`` / ``workers.*`` before building.

    Returns:
        A compiled LangGraph runnable.
    """
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(PipelineState)
    builder.add_node("supervisor", supervisor.supervisor_node)
    builder.add_node("DataAgent", workers.data_agent_node)
    builder.add_node("ReportAgent", workers.report_agent_node)

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        _route,
        {"DataAgent": "DataAgent", "ReportAgent": "ReportAgent", END: END},
    )
    builder.add_edge("DataAgent", "supervisor")
    builder.add_edge("ReportAgent", "supervisor")

    return builder.compile()


def run_pipeline(task: str) -> PipelineState:
    """
    Run the agent pipeline to completion for a task.

    Args:
        task: The task description.

    Returns:
        The final pipeline state (task, worker_results, status, final_output).
    """
    graph = build_graph()
    initial: PipelineState = {
        "task": task,
        "next": "",
        "worker_results": [],
        "status": "in_progress",
        "final_output": "",
    }
    final: PipelineState = graph.invoke(initial)
    if not final.get("status"):
        final["status"] = "completed"
    return final
