"""Session-keyed conversation memory with a sliding window.

Phase 2 calls for ``ConversationBufferWindowMemory`` with a ten-turn window.
That class is part of the legacy ``langchain`` memory module and is deprecated
in current LangChain; this module implements the same behaviour on top of the
stable ``langchain_core`` message primitives — a sliding window of the last
``WINDOW_TURNS`` human/assistant turns, keyed by session id.

History lives in process memory. For multi-process deployments this is the seam
where Redis (already provisioned in docker-compose) would back the store; see
ADR-005.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

# One "turn" is a human message plus the assistant reply, so the window holds
# WINDOW_TURNS * 2 messages.
WINDOW_TURNS = 10

_HISTORIES: dict[str, list[BaseMessage]] = {}


def get_history(session_id: str) -> list[BaseMessage]:
    """
    Return the windowed message history for a session.

    Args:
        session_id: Conversation key (the Phase 1 auth session id in the app).

    Returns:
        The stored messages, oldest first (already trimmed to the window).
    """
    return list(_HISTORIES.get(session_id, []))


def append_turn(session_id: str, human_message: str, ai_message: str) -> None:
    """
    Record one completed turn and trim history to the sliding window.

    Args:
        session_id: Conversation key.
        human_message: The user's message for this turn.
        ai_message: The assistant's final answer text for this turn.

    Side effects:
        Mutates the in-process history store for ``session_id``.
    """
    history = _HISTORIES.setdefault(session_id, [])
    history.append(HumanMessage(content=human_message))
    history.append(AIMessage(content=ai_message))
    # Keep only the most recent WINDOW_TURNS turns.
    max_messages = WINDOW_TURNS * 2
    if len(history) > max_messages:
        del history[:-max_messages]


def clear(session_id: str) -> None:
    """
    Forget a session's history.

    Args:
        session_id: Conversation key to drop.

    Side effects:
        Removes the session from the in-process store.
    """
    _HISTORIES.pop(session_id, None)
