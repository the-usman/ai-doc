"""Tests for the orchestration layer that runs the graph and persists the run.

Persistence and the compiled graph are both patched, so this exercises the
create -> run -> complete (and the failure) code path without a database or an LLM.
"""

from app.agents import persistence, service


def test_execute_pipeline_persists_completed_run(monkeypatch) -> None:
    """A successful run records the graph's output and trace as completed."""
    recorded = {}

    monkeypatch.setattr(
        persistence,
        "create_pipeline_run",
        lambda user_id, task: {"id": "run-1", "task": task},
    )
    monkeypatch.setattr(
        service,
        "run_pipeline",
        lambda task: {
            "final_output": "All done.",
            "worker_results": [{"worker": "DataAgent", "output": "data"}],
            "status": "completed",
        },
    )

    def _complete(run_id, final_output, trace, status="completed"):
        recorded.update(run_id=run_id, final_output=final_output, trace=trace, status=status)
        return {"id": run_id, "status": status, "final_output": final_output}

    monkeypatch.setattr(persistence, "complete_pipeline_run", _complete)

    run = service.execute_pipeline("user-1", "do a thing")

    assert run["status"] == "completed"
    assert recorded["run_id"] == "run-1"
    assert recorded["final_output"] == "All done."
    assert recorded["trace"] == [{"worker": "DataAgent", "output": "data"}]


def test_execute_pipeline_marks_failure_when_graph_raises(monkeypatch) -> None:
    """If the graph raises, the run is marked failed rather than bubbling up."""
    failed = {}

    monkeypatch.setattr(
        persistence,
        "create_pipeline_run",
        lambda user_id, task: {"id": "run-2", "task": task},
    )

    def _boom(task):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(service, "run_pipeline", _boom)

    def _fail(run_id, error):
        failed.update(run_id=run_id, error=error)
        return {"id": run_id, "status": "failed"}

    monkeypatch.setattr(persistence, "fail_pipeline_run", _fail)

    run = service.execute_pipeline("user-1", "do a thing")

    assert run["status"] == "failed"
    assert failed["run_id"] == "run-2"
    assert "model exploded" in failed["error"]
