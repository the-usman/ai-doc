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
SUPPORTED_PROVIDERS = frozenset({"google", "github"})


def _serializer(settings: Settings) -> URLSafeSerializer:
    """
    Build a signer for OAuth state cookies.

    Args:
        settings: Provides app_secret.

    Returns:
        URLSafeSerializer for state payloads.
    """
    return URLSafeSerializer(settings.app_secret, salt="oauth-state")


def _provider_configured(settings: Settings, provider: str) -> bool:
    """
    Return whether OAuth client credentials exist for a provider.

    Args:
        settings: Application settings.
        provider: google or github.

    Returns:
        True if the provider can be used for login.
    """
    if provider == "google":
        return bool(settings.google_client_id and settings.google_client_secret)
    if provider == "github":
        return bool(settings.github_client_id and settings.github_client_secret)
    return False


def _start_oauth(settings: Settings, provider: str) -> RedirectResponse:
    """
    Build redirect to the provider authorize URL with CSRF state cookie.

    Args:
        settings: Client ids, secrets, and redirect URIs.
        provider: google or github.

    Returns:
        Redirect response with signed state cookie set.

    Raises:
        HTTPException: If provider is unknown or not configured.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    if not _provider_configured(settings, provider):
        raise HTTPException(
            status_code=503,
            detail=f"{provider.title()} OAuth is not configured on this server",
        )

    state = secrets.token_urlsafe(16)
    signed = _serializer(settings).dumps({"state": state, "provider": provider})
    try:
        url = build_authorize_url(settings, provider, state)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

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


@router.get("/providers")
def list_providers() -> dict[str, list[str]]:
    """
    List OAuth providers that have credentials configured.

    Returns:
        JSON object with provider keys enabled for sign-in.
    """
    settings = get_settings()
    enabled = [p for p in sorted(SUPPORTED_PROVIDERS) if _provider_configured(settings, p)]
    return {"providers": enabled}


@router.get("/login")
async def login_default() -> RedirectResponse:
    """
    Start OAuth with the default provider (Google).

    Returns:
        Redirect to Google authorize URL.
    """
    settings = get_settings()
    default = (
        settings.oauth_provider if settings.oauth_provider in SUPPORTED_PROVIDERS else "google"
    )
    return _start_oauth(settings, default)


@router.get("/login/{provider}")
async def login_provider(provider: str) -> RedirectResponse:
    """
    Start OAuth for a specific provider.

    Args:
        provider: google or github.

    Returns:
        Redirect to that provider's authorize URL.
    """
    settings = get_settings()
    return _start_oauth(settings, provider)


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
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

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
