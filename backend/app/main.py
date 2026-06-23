"""FastAPI application entrypoint."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth_routes import SESSION_COOKIE
from app.auth_routes import router as auth_router
from app.config import get_settings
from app.sessions import get_active_session


def _resolve_static_dir() -> Path:
    """
    Locate the built React app (frontend/dist).

    In the production Docker image files live at /app/frontend/dist.
    When running from the backend/ folder locally, dist is at ../frontend/dist.

    Returns:
        Path to the dist directory (may not exist in dev API-only mode).
    """
    app_package = Path(__file__).resolve().parent
    backend_root = app_package.parent
    candidates = [
        backend_root / "frontend" / "dist",
        backend_root.parent / "frontend" / "dist",
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


STATIC_DIR = _resolve_static_dir()

app = FastAPI(title="AI-Doc API", version="0.1.0")

settings = get_settings()
_cors_origins = list(
    {
        settings.frontend_url.rstrip("/"),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


def _register_chat() -> bool:
    """
    Wire up the Phase 2 chat application if its dependencies are installed.

    The LangChain stack is an optional, heavy dependency set. Guarding the
    import keeps the rest of the API (auth, health) serving even when the chat
    extras are not present.

    Returns:
        True if the chat routes were registered.

    Side effects:
        Includes the chat router and mounts the LangServe routes on the app.
    """
    try:
        from app.chat.routes import register_langserve
        from app.chat.routes import router as chat_router

        app.include_router(chat_router)
        register_langserve(app)
        return True
    except Exception as exc:  # pragma: no cover - optional dependency path
        logging.getLogger(__name__).warning("Chat application unavailable: %s", exc)
        return False


CHAT_ENABLED = _register_chat()


def _register_agents() -> bool:
    """
    Wire up the Phase 3 agents application if its dependencies are installed.

    Like the chat extras, LangGraph is an optional heavy dependency; guarding the
    import keeps the rest of the API serving when it is absent.

    Returns:
        True if the agents routes were registered.

    Side effects:
        Includes the agents router on the app.
    """
    try:
        from app.agents.routes import router as agents_router

        app.include_router(agents_router)
        return True
    except Exception as exc:  # pragma: no cover - optional dependency path
        logging.getLogger(__name__).warning("Agents application unavailable: %s", exc)
        return False


AGENTS_ENABLED = _register_agents()


def _register_knowledge() -> bool:
    """
    Wire up the Phase 4 Knowledge (RAG) application if its dependencies are present.

    The RAG stack (embeddings, text splitter, pgvector, PDF extraction) is an
    optional heavy dependency set; guarding the import keeps the rest of the API
    serving when it is absent.

    Returns:
        True if the knowledge routes were registered.

    Side effects:
        Includes the knowledge router on the app.
    """
    try:
        from app.knowledge.routes import router as knowledge_router

        app.include_router(knowledge_router)
        return True
    except Exception as exc:  # pragma: no cover - optional dependency path
        logging.getLogger(__name__).warning("Knowledge application unavailable: %s", exc)
        return False


KNOWLEDGE_ENABLED = _register_knowledge()


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    """
    Liveness probe for Docker and CI.

    Returns:
        JSON status payload with HTTP 200.
    """
    return {"status": "ok", "service": "ai-doc-api"}


def get_current_session(request: Request) -> dict:
    """
    Resolve session from httpOnly cookie.

    Args:
        request: Incoming HTTP request.

    Returns:
        Session and user fields.

    Raises:
        HTTPException: 401 when cookie missing or session expired.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session


SessionDep = Annotated[dict, Depends(get_current_session)]


@app.get("/api/me")
def me(session: SessionDep) -> dict:
    """
    Return the authenticated user profile.

    Args:
        session: Resolved active session dependency.

    Returns:
        Public user fields for the shell UI.
    """
    return {
        "email": session["email"],
        "name": session["name"],
        "provider": session["provider"],
        "avatar_url": session.get("avatar_url"),
    }


def _serve_index() -> FileResponse:
    """
    Return the SPA shell (index.html).

    Returns:
        FileResponse for index.html.

    Raises:
        HTTPException: When the frontend was not built into the image.
    """
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(
            status_code=503,
            detail=(
                "Frontend not built. Run npm run build in frontend/ or "
                "redeploy the Docker image."
            ),
        )
    return FileResponse(index)


def _mount_frontend() -> None:
    """Serve built React assets when dist exists (production)."""
    if not STATIC_DIR.is_dir():
        return

    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def spa_root() -> FileResponse:
        """Serve the SPA entry page."""
        return _serve_index()

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        """
        Serve index.html for client-side routes (React Router).

        Args:
            full_path: Path after the leading slash.

        Returns:
            index.html for non-file SPA routes.
        """
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not Found")
        return _serve_index()


_mount_frontend()
