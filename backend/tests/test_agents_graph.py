"""Tests for graph assembly, routing, and end-to-end execution.

The supervisor and worker nodes are patched with deterministic fakes so the graph
topology and the conditional edge are exercised without an LLM. This covers the
three routing paths from the phase brief: DataAgent only, ReportAgent only, and
both in sequence.
"""

import pytest

pytest.importorskip("langgraph")

from app.agents import graph, supervisor, workers  # noqa: E402


def test_route_maps_next_to_node_or_end() -> None:
    """`_route` returns a worker name for a worker, else the END sentinel."""
    from langgraph.graph import END

    assert graph._route({"next": "DataAgent"}) == "DataAgent"
    assert graph._route({"next": "ReportAgent"}) == "ReportAgent"
    assert graph._route({"next": "FINISH"}) == END
    assert graph._route({}) == END


def _scripted_supervisor(route_sequence):
    """Build a supervisor_node that emits the given routes, then FINISH."""
    calls = {"n": 0}

    def _node(state):
        i = calls["n"]
        calls["n"] += 1
        if i < len(route_sequence):
            return {"next": route_sequence[i]}
        return {
            "next": "FINISH",
            "status": "completed",
            "final_output": state.get("worker_results", [{}])[-1].get("output", ""),
        }

    return _node


@pytest.mark.parametrize(
    "route_sequence, expected_workers",
    [
        (["DataAgent"], ["DataAgent"]),
        (["ReportAgent"], ["ReportAgent"]),
        (["DataAgent", "ReportAgent"], ["DataAgent", "ReportAgent"]),
    ],
)
def test_run_pipeline_routes_and_accumulates(monkeypatch, route_sequence, expected_workers) -> None:
    """The graph visits the routed workers in order and accumulates their results."""
    monkeypatch.setattr(supervisor, "supervisor_node", _scripted_supervisor(route_sequence))
    monkeypatch.setattr(
        workers,
        "data_agent_node",
        lambda state: {"worker_results": [{"worker": "DataAgent", "output": "data"}]},
    )
    monkeypatch.setattr(
        workers,
        "report_agent_node",
        lambda state: {"worker_results": [{"worker": "ReportAgent", "output": "report"}]},
    )

    final = graph.run_pipeline("a task")

    assert [r["worker"] for r in final["worker_results"]] == expected_workers
    assert final["status"] == "completed"
    assert final["task"] == "a task"
