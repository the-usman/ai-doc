"""Persistent, per-application conversation memory.

Phase 2 kept chat history in a process-local dict, which is lost on restart.
Phase 4 moves it to Redis via LangChain's ``RedisChatMessageHistory`` so a user's
history survives restarts and is shared across API workers.

Memory is **scoped per application**: the Chat app and the Knowledge Chat page
each get their own history for a given session, because a conversation about
platform data and a conversation about uploaded documents are different contexts
and mixing them adds noise. The scope becomes part of the Redis key. See ADR-011.

If Redis (or ``langchain_community``) is unavailable the module falls back to an
in-process windowed store, so local development and tests work without Redis.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.config import get_settings

# One "turn" is a human message plus the assistant reply.
WINDOW_TURNS = 10

_KEY_PREFIX = "aidoc:history:"

# Process-local fallback store, keyed by "scope:session_id".
_FALLBACK: dict[str, list[BaseMessage]] = {}

# Cached probe result: None = not yet probed, True/False = Redis usable or not.
_redis_ok: bool | None = None


def _scoped_key(scope: str, session_id: str) -> str:
    """Combine an application scope and a session id into one history key."""
    return f"{scope}:{session_id}"


def _window() -> int:
    """Return the configured sliding-window size in turns."""
    return get_settings().memory_window_turns


def _get_redis_history(key: str):
    """
    Return a ``RedisChatMessageHistory`` for ``key``, or None if Redis is down.

    The first call probes connectivity and caches the result so a missing Redis
    does not cost a connection attempt on every message.
    """
    global _redis_ok
    if _redis_ok is False:
        return None
    try:
        from langchain_community.chat_message_histories import RedisChatMessageHistory

        history = RedisChatMessageHistory(
            session_id=key,
            url=get_settings().redis_url,
            key_prefix=_KEY_PREFIX,
        )
        # Touch the connection so an unreachable Redis fails fast and we fall back.
        if _redis_ok is None:
            history.redis_client.ping()
            _redis_ok = True
        return history
    except Exception:
        _redis_ok = False
        return None


def get_history(scope: str, session_id: str) -> list[BaseMessage]:
    """
    Return the windowed message history for a scope and session.

    Args:
        scope: Application scope, e.g. ``"chat"`` or ``"knowledge"``.
        session_id: Conversation key (the auth session id in the app).

    Returns:
        Stored messages oldest-first, trimmed to the sliding window.
    """
    key = _scoped_key(scope, session_id)
    history = _get_redis_history(key)
    if history is not None:
        messages = list(history.messages)
    else:
        messages = list(_FALLBACK.get(key, []))
    max_messages = _window() * 2
    return messages[-max_messages:]


def append_turn(scope: str, session_id: str, human_message: str, ai_message: str) -> None:
    """
    Record one completed turn.

    Args:
        scope: Application scope.
        session_id: Conversation key.
        human_message: The user's message for this turn.
        ai_message: The assistant's final answer for this turn.

    Side effects:
        Appends to Redis (or the in-process fallback) for the scoped key.
    """
    key = _scoped_key(scope, session_id)
    history = _get_redis_history(key)
    if history is not None:
        history.add_user_message(human_message)
        history.add_ai_message(ai_message)
        return
    store = _FALLBACK.setdefault(key, [])
    store.append(HumanMessage(content=human_message))
    store.append(AIMessage(content=ai_message))
    max_messages = _window() * 2
    if len(store) > max_messages:
        del store[:-max_messages]


def clear(scope: str, session_id: str) -> None:
    """
    Forget a scoped session's history.

    Args:
        scope: Application scope.
        session_id: Conversation key to drop.

    Side effects:
        Clears the history in Redis (or the in-process fallback).
    """
    key = _scoped_key(scope, session_id)
    history = _get_redis_history(key)
    if history is not None:
        history.clear()
    _FALLBACK.pop(key, None)
