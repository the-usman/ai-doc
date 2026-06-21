"""Tests for the worker nodes, exercised in isolation with a mock state.

The Anthropic-backed agent and chain factories are replaced with fakes so each
worker's node logic runs without a network call or a database — this is the
"test the worker before assembling the graph" step from ADR-007.
"""

import pytest

pytest.importorskip("langchain_core")

from app.agents import workers  # noqa: E402


class _FakeReactAgent:
    """Stands in for a compiled ReAct agent: returns a messages dict."""

    def __init__(self, messages) -> None:
        self._messages = messages

    def invoke(self, _inputs) -> dict:
        return {"messages": self._messages}


class _AIMsg:
    """Minimal AI message with a `type` and string content."""

    def __init__(self, content: str) -> None:
        self.type = "ai"
        self.content = content


def test_data_agent_node_appends_last_ai_text(monkeypatch) -> None:
    """DataAgent returns the final AI message text as a single appended result."""
    monkeypatch.setattr(
        workers,
        "get_data_agent",
        lambda: _FakeReactAgent([_AIMsg("There are 2 users.")]),
    )
    update = workers.data_agent_node({"task": "count users", "worker_results": []})
    assert update["worker_results"] == [{"worker": "DataAgent", "output": "There are 2 users."}]


def test_last_text_reads_anthropic_block_content() -> None:
    """`_last_text` handles Anthropic's list-of-blocks content shape."""
    messages = [_AIMsg([{"type": "text", "text": "hello "}, {"type": "text", "text": "world"}])]
    assert workers._last_text(messages) == "hello world"


def test_report_agent_node_synthesises_and_appends(monkeypatch) -> None:
    """ReportAgent feeds the rendered findings to its chain and appends a result."""
    captured = {}

    class _FakeChain:
        def invoke(self, inputs):
            captured["context"] = inputs["context"]
            return "A short summary."

    monkeypatch.setattr(workers, "get_report_chain", lambda: _FakeChain())
    state = {
        "task": "summarise",
        "worker_results": [{"worker": "DataAgent", "output": "2 users"}],
    }
    update = workers.report_agent_node(state)
    assert update["worker_results"] == [{"worker": "ReportAgent", "output": "A short summary."}]
    # The findings rendered into the prompt include the prior worker's output.
    assert "DataAgent: 2 users" in captured["context"]
