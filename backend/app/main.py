"""FastAPI application entrypoint."""

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

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

app = FastAPI(title="AI-Doc API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


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


def _mount_frontend() -> None:
    """Serve built React assets when dist exists (production)."""
    if STATIC_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str) -> FileResponse:
            """
            Serve index.html for client-side routes.

            Args:
                full_path: Request path segment after leading slash.

            Returns:
                index.html for SPA navigation paths.

            Raises:
                HTTPException: When index.html is missing.
            """
            index = STATIC_DIR / "index.html"
            if index.exists():
                return FileResponse(index)
            raise HTTPException(status_code=404)


_mount_frontend()
