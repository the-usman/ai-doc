"""Tests for session-keyed sliding-window conversation memory."""

from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from app.chat import memory  # noqa: E402


def test_memory_is_isolated_per_session() -> None:
    """Each session id keeps an independent history."""
    a, b = str(uuid4()), str(uuid4())
    memory.append_turn(a, "hi from a", "reply a")
    assert memory.get_history(a)
    assert memory.get_history(b) == []
    memory.clear(a)


def test_memory_remembers_within_a_session() -> None:
    """A second turn can see the messages from the first."""
    sid = str(uuid4())
    memory.append_turn(sid, "how many users?", "There are 5 users.")
    history = memory.get_history(sid)
    assert history[0].content == "how many users?"
    assert history[1].content == "There are 5 users."
    memory.clear(sid)


def test_memory_window_trims_old_turns() -> None:
    """History is capped at WINDOW_TURNS turns (2 messages per turn)."""
    sid = str(uuid4())
    for i in range(memory.WINDOW_TURNS + 5):
        memory.append_turn(sid, f"q{i}", f"a{i}")
    history = memory.get_history(sid)
    assert len(history) == memory.WINDOW_TURNS * 2
    # Oldest retained message is from turn 5, not turn 0.
    assert history[0].content == "q5"
    memory.clear(sid)
