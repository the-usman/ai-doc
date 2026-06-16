"""Tests for the chat chain's tool loop, structured output, and memory.

The Anthropic model is replaced with fakes so the chain logic is exercised
end-to-end without a network call.
"""

from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from app.chat import chain, memory  # noqa: E402
from app.chat.schemas import ChatResponse  # noqa: E402


class _FakeAI:
    """Stands in for an AIMessage with optional tool calls."""

    def __init__(self, content: str = "", tool_calls=None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []


class _FakeToolModel:
    """Calls a tool on the first turn, then answers on the second."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            return _FakeAI(tool_calls=[{"name": "get_platform_user_count", "args": {}, "id": "t1"}])
        return _FakeAI(content="There are 2 users.")


class _FakeStructuredModel:
    """Returns a structured response, leaving sources for the chain to fill."""

    def invoke(self, messages) -> ChatResponse:
        return ChatResponse(response="There are 2 users.", confidence="high", sources=[])


def test_build_baseline_chain_pipes_prompt_model_parser(monkeypatch) -> None:
    """The baseline LCEL chain wires prompt -> model -> string parser."""
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    monkeypatch.setattr(
        chain,
        "get_chat_model",
        lambda: RunnableLambda(lambda _prompt_value: AIMessage(content="pong")),
    )
    baseline = chain.build_baseline_chain()
    assert baseline.invoke({"message": "ping"}) == "pong"


@pytest.fixture
def fake_models(monkeypatch):
    """Patch the model factories and the tool function to avoid network/DB."""
    monkeypatch.setattr(chain, "get_tool_model", lambda: _FakeToolModel())
    monkeypatch.setattr(chain, "get_structured_model", lambda: _FakeStructuredModel())
    monkeypatch.setitem(chain.TOOL_FUNCTIONS, "get_platform_user_count", lambda: 2)


def test_invoke_chat_runs_tool_loop_and_records_sources(fake_models) -> None:
    """The chain executes the tool and reports it in `sources`."""
    sid = str(uuid4())
    result = chain.invoke_chat(sid, "how many users are registered?")
    assert isinstance(result, ChatResponse)
    assert result.response == "There are 2 users."
    assert result.confidence == "high"
    assert result.sources == ["get_platform_user_count"]
    memory.clear(sid)


def test_invoke_chat_persists_turn_to_memory(fake_models) -> None:
    """After a turn, the session history contains the exchange."""
    sid = str(uuid4())
    chain.invoke_chat(sid, "how many users?")
    history = memory.get_history(sid)
    assert history[0].content == "how many users?"
    assert history[-1].content == "There are 2 users."
    memory.clear(sid)


def test_invoke_chat_no_tool_path(monkeypatch) -> None:
    """When the model calls no tools, the answer still flows through."""

    class _NoToolModel:
        def invoke(self, messages):
            return _FakeAI(content="Hello there.")

    monkeypatch.setattr(chain, "get_tool_model", lambda: _NoToolModel())
    monkeypatch.setattr(
        chain,
        "get_structured_model",
        lambda: type(
            "S",
            (),
            {"invoke": lambda self, m: ChatResponse(response="Hello there.")},
        )(),
    )
    sid = str(uuid4())
    result = chain.invoke_chat(sid, "hi")
    assert result.response == "Hello there."
    assert result.sources == []
    memory.clear(sid)
