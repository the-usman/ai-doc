"""Chat conversation memory.

Phase 2 stored history in a process-local dict. Phase 4 moves persistence to
Redis; this module is now a thin adapter that binds the shared, Redis-backed
:mod:`app.memory` store to the chat application's scope, so the chat chain and
its existing tests keep the same ``get_history`` / ``append_turn`` / ``clear``
API while gaining persistence. See ADR-011.
"""

from langchain_core.messages import BaseMessage

from app import memory as _memory

# The application scope this module writes under in the shared store.
SCOPE = "chat"

# Re-exported so existing callers and tests can reference the window size.
WINDOW_TURNS = _memory.WINDOW_TURNS


def get_history(session_id: str) -> list[BaseMessage]:
    """
    Return the windowed chat history for a session.

    Args:
        session_id: Conversation key (the Phase 1 auth session id in the app).

    Returns:
        The stored messages, oldest first (already trimmed to the window).
    """
    return _memory.get_history(SCOPE, session_id)


def append_turn(session_id: str, human_message: str, ai_message: str) -> None:
    """
    Record one completed chat turn.

    Args:
        session_id: Conversation key.
        human_message: The user's message for this turn.
        ai_message: The assistant's final answer text for this turn.
    """
    _memory.append_turn(SCOPE, session_id, human_message, ai_message)


def clear(session_id: str) -> None:
    """
    Forget a chat session's history.

    Args:
        session_id: Conversation key to drop.
    """
    _memory.clear(SCOPE, session_id)
