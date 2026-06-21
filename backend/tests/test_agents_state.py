"""Tests for the agent pipeline state definition."""

import operator

from app.agents.state import PipelineState, WorkerResult


def test_worker_results_reducer_accumulates() -> None:
    """The worker_results reducer (operator.add) appends rather than replaces."""
    first: list[WorkerResult] = [{"worker": "DataAgent", "output": "10 users"}]
    second: list[WorkerResult] = [{"worker": "ReportAgent", "output": "summary"}]
    merged = operator.add(first, second)
    assert [r["worker"] for r in merged] == ["DataAgent", "ReportAgent"]


def test_pipeline_state_is_partial() -> None:
    """A node may return only the fields it changes."""
    update: PipelineState = {"next": "DataAgent"}
    assert update["next"] == "DataAgent"
