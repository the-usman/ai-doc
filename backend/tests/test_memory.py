"""Tests for the shared, scope-partitioned conversation memory.

Redis is not available in the test environment, so these exercise the in-process
fallback — which is the behaviour the app degrades to when Redis is down.
"""

from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from app import memory  # noqa: E402


def test_history_is_isolated_per_scope() -> None:
    """The same session id under two scopes keeps two independent histories."""
    sid = str(uuid4())
    memory.append_turn("chat", sid, "chat question", "chat answer")
    assert memory.get_history("chat", sid)
    assert memory.get_history("knowledge", sid) == []
    memory.clear("chat", sid)


def test_history_is_isolated_per_session() -> None:
    """Within a scope, each session id is independent."""
    a, b = str(uuid4()), str(uuid4())
    memory.append_turn("knowledge", a, "hi", "hello")
    assert memory.get_history("knowledge", a)
    assert memory.get_history("knowledge", b) == []
    memory.clear("knowledge", a)


def test_append_and_read_back_turn() -> None:
    """A recorded turn reads back as human-then-ai messages."""
    sid = str(uuid4())
    memory.append_turn("knowledge", sid, "what is RAG?", "Retrieval-augmented generation.")
    history = memory.get_history("knowledge", sid)
    assert history[0].content == "what is RAG?"
    assert history[1].content == "Retrieval-augmented generation."
    memory.clear("knowledge", sid)


def test_window_trims_old_turns() -> None:
    """History is capped at WINDOW_TURNS turns (two messages per turn)."""
    sid = str(uuid4())
    for i in range(memory.WINDOW_TURNS + 5):
        memory.append_turn("chat", sid, f"q{i}", f"a{i}")
    history = memory.get_history("chat", sid)
    assert len(history) == memory.WINDOW_TURNS * 2
    assert history[0].content == "q5"
    memory.clear("chat", sid)


def test_clear_forgets_history() -> None:
    """Clearing a scoped session empties its history."""
    sid = str(uuid4())
    memory.append_turn("chat", sid, "remember this", "ok")
    memory.clear("chat", sid)
    assert memory.get_history("chat", sid) == []


def test_chat_adapter_delegates_with_chat_scope() -> None:
    """The chat memory adapter writes under the 'chat' scope of the shared store."""
    from app.chat import memory as chat_memory

    sid = str(uuid4())
    chat_memory.append_turn(sid, "via adapter", "adapter reply")
    # Visible through the adapter and through the shared store's chat scope...
    assert chat_memory.get_history(sid)
    assert memory.get_history("chat", sid)
    # ...but not under a different scope.
    assert memory.get_history("knowledge", sid) == []
    chat_memory.clear(sid)
