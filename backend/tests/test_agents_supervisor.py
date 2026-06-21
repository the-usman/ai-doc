"""Tests for the supervisor node and its routing decisions."""

import pytest

pytest.importorskip("langchain_core")

from app.agents import supervisor  # noqa: E402
from app.agents.supervisor import RouteDecision  # noqa: E402


class _FakeRouter:
    """Returns a fixed routing decision."""

    def __init__(self, decision: RouteDecision) -> None:
        self.decision = decision

    def invoke(self, messages) -> RouteDecision:
        return self.decision


def test_supervisor_routes_to_worker(monkeypatch) -> None:
    """A non-FINISH decision is returned as the next node."""
    monkeypatch.setattr(
        supervisor,
        "get_router",
        lambda: _FakeRouter(RouteDecision(next="DataAgent")),
    )
    update = supervisor.supervisor_node({"task": "count users", "worker_results": []})
    assert update["next"] == "DataAgent"


def test_supervisor_finishes_and_synthesises(monkeypatch) -> None:
    """FINISH yields final_output from the ReportAgent result and completes."""
    monkeypatch.setattr(
        supervisor,
        "get_router",
        lambda: _FakeRouter(RouteDecision(next="FINISH")),
    )
    state = {
        "task": "summarise",
        "worker_results": [
            {"worker": "DataAgent", "output": "10 users"},
            {"worker": "ReportAgent", "output": "There are 10 users."},
        ],
    }
    update = supervisor.supervisor_node(state)
    assert update["next"] == "FINISH"
    assert update["status"] == "completed"
    assert update["final_output"] == "There are 10 users."


def test_supervisor_caps_iterations(monkeypatch) -> None:
    """Once the step cap is reached the supervisor finishes without routing."""

    def _boom():
        raise AssertionError("router should not be called past the cap")

    monkeypatch.setattr(supervisor, "get_router", _boom)
    state = {
        "task": "x",
        "worker_results": [
            {"worker": "DataAgent", "output": str(i)} for i in range(supervisor.MAX_WORKER_STEPS)
        ],
    }
    update = supervisor.supervisor_node(state)
    assert update["next"] == "FINISH"
