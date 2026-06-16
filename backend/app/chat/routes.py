"""HTTP surface for the chat application.

Two entry points share the same chain and memory:

* ``POST /api/chat/message`` — the authenticated route the frontend calls. It
  derives the conversation key from the Phase 1 session cookie, so memory is
  isolated per signed-in user.
* The LangServe routes mounted at ``/api/chat`` (``/invoke``, ``/stream``,
  ``/playground``) — production-ready endpoints with input validation, schema
  exposure, and streaming, used for development and demonstration.
"""

import logging

from fastapi import APIRouter, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth_routes import SESSION_COOKIE
from app.chat.chain import chat_chain, invoke_chat
from app.chat.schemas import ChatResponse
from app.sessions import get_active_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Body for an authenticated chat message."""

    message: str = Field(min_length=1, description="The user's message.")


def _require_session(request: Request) -> dict:
    """
    Resolve the active session from the cookie.

    Args:
        request: Incoming HTTP request.

    Returns:
        Joined session and user fields.

    Raises:
        HTTPException: 401 when the cookie is missing or the session expired.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session


@router.post("/message", response_model=ChatResponse)
def chat_message(request: Request, payload: ChatMessageRequest) -> ChatResponse:
    """
    Send a message to the assistant within the caller's session.

    Args:
        request: Incoming request (provides the session cookie).
        payload: The user's message.

    Returns:
        The structured assistant response.

    Raises:
        HTTPException: 401 if unauthenticated, 503 if the model is not
            configured, 502 on a backend failure.
    """
    session = _require_session(request)
    session_id = str(session["session_id"])
    try:
        return invoke_chat(session_id, payload.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive backend guard
        logger.exception("Chat backend error")
        raise HTTPException(status_code=502, detail="Chat backend error") from exc


def register_langserve(app: FastAPI) -> bool:
    """
    Mount the LangServe routes for the chat chain at ``/api/chat``.

    Args:
        app: The FastAPI application.

    Returns:
        True if the routes were mounted, False if LangServe is unavailable.

    Side effects:
        Adds ``/api/chat/invoke``, ``/api/chat/stream`` and
        ``/api/chat/playground`` routes to the app.
    """
    try:
        from langserve import add_routes

        add_routes(app, chat_chain, path="/api/chat", playground_type="default")
        return True
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("LangServe routes not mounted: %s", exc)
        return False
