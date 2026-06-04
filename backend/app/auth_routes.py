"""OAuth and session HTTP routes."""

import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer

from app.config import Settings, get_settings
from app.oauth import build_authorize_url, exchange_code_and_fetch_profile
from app.sessions import create_session
from app.users import upsert_oauth_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE = "ai_doc_session"
STATE_COOKIE = "ai_doc_oauth_state"


def _serializer(settings: Settings) -> URLSafeSerializer:
    """
    Build a signer for OAuth state cookies.

    Args:
        settings: Provides app_secret.

    Returns:
        URLSafeSerializer for state payloads.
    """
    return URLSafeSerializer(settings.app_secret, salt="oauth-state")


@router.get("/login")
async def login() -> RedirectResponse:
    """
    Start OAuth by redirecting to the configured provider.

    Sets a signed state cookie for CSRF protection.

    Returns:
        Redirect to Google or GitHub authorize URL.
    """
    settings = get_settings()
    provider = settings.oauth_provider
    state = secrets.token_urlsafe(16)
    signed = _serializer(settings).dumps({"state": state, "provider": provider})
    url = build_authorize_url(settings, provider, state)
    response = RedirectResponse(url, status_code=302)
    response.set_cookie(
        STATE_COOKIE,
        signed,
        httponly=True,
        samesite="lax",
        max_age=600,
        secure=settings.app_env == "production",
    )
    return response


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> Response:
    """
    Handle OAuth provider callback: validate state, upsert user, set session.

    Args:
        provider: google or github from URL path.
        code: Authorization code query param.
        state: CSRF state query param.
        error: Provider error string if login was denied.

    Returns:
        Redirect to frontend home with session cookie, or HTTP 400 on failure.
    """
    settings = get_settings()

    if error or not code or not state:
        raise HTTPException(status_code=400, detail="OAuth authorization failed")

    signed_state = request.cookies.get(STATE_COOKIE)
    if not signed_state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")

    try:
        payload = _serializer(settings).loads(signed_state)
    except BadSignature as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc

    if payload.get("state") != state or payload.get("provider") != provider:
        raise HTTPException(status_code=400, detail="OAuth state mismatch")

    try:
        profile = await exchange_code_and_fetch_profile(settings, provider, code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = upsert_oauth_user(
        email=profile["email"],
        name=profile.get("name"),
        provider=provider,
        provider_user_id=profile["provider_user_id"],
        avatar_url=profile.get("avatar_url"),
    )
    session = create_session(user["id"])

    response = RedirectResponse(settings.frontend_url + "/", status_code=302)
    response.delete_cookie(STATE_COOKIE)
    response.set_cookie(
        SESSION_COOKIE,
        session["token"],
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        secure=settings.app_env == "production",
    )
    return response


@router.post("/logout")
async def logout() -> Response:
    """
    Clear the session cookie.

    Returns:
        JSON response with Set-Cookie clearing the session.
    """
    response = Response(content='{"message":"logged out"}', media_type="application/json")
    response.delete_cookie(SESSION_COOKIE)
    return response
