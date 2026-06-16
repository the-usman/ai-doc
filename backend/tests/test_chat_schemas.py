"""Tests for the chat structured-output schema."""

import pytest

from app.chat.schemas import ChatInput, ChatResponse


def test_chat_response_defaults() -> None:
    """A minimal ChatResponse fills sensible defaults."""
    resp = ChatResponse(response="hello")
    assert resp.confidence == "medium"
    assert resp.sources == []


def test_chat_response_rejects_bad_confidence() -> None:
    """Confidence is restricted to the allowed literals."""
    with pytest.raises(ValueError):
        ChatResponse(response="x", confidence="certain")


def test_chat_input_defaults_session() -> None:
    """ChatInput defaults the session id for the playground."""
    payload = ChatInput(message="hi")
    assert payload.session_id == "playground"
