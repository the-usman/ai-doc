"""OAuth callback integration tests."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from itsdangerous import URLSafeSerializer

from app.auth_routes import STATE_COOKIE
from app.config import get_settings
from app.db import get_connection


def _signed_state_cookie(provider: str = "google") -> dict[str, str]:
    """Build OAuth state cookie matching callback query."""
    settings = get_settings()
    state = "test-state-value"
    signed = URLSafeSerializer(settings.app_secret, salt="oauth-state").dumps(
        {"state": state, "provider": provider}
    )
    return {STATE_COOKIE: signed, "state_query": state}


def test_list_providers_returns_google_and_github(client) -> None:
    """Providers endpoint lists configured OAuth providers."""
    response = client.get("/api/auth/providers")
    assert response.status_code == 200
    data = response.json()
    assert "google" in data["providers"]
    assert "github" in data["providers"]


def test_login_google_redirects(client) -> None:
    """Google login route redirects to Google authorize URL."""
    response = client.get("/api/auth/login/google", follow_redirects=False)
    assert response.status_code == 302
    assert "accounts.google.com" in response.headers["location"]
    assert STATE_COOKIE in response.cookies


def test_login_github_redirects(client) -> None:
    """GitHub login route redirects to GitHub authorize URL."""
    response = client.get("/api/auth/login/github", follow_redirects=False)
    assert response.status_code == 302
    assert "github.com/login/oauth/authorize" in response.headers["location"]
    assert STATE_COOKIE in response.cookies


def test_oauth_callback_valid_code_creates_user_and_session(client) -> None:
    """Valid OAuth code upserts user and sets session cookie."""
    cookies = _signed_state_cookie("google")
    state = cookies.pop("state_query")
    profile = {
        "email": f"user-{uuid4()}@example.com",
        "name": "Test User",
        "provider_user_id": str(uuid4()),
        "avatar_url": "https://example.com/a.png",
    }

    with patch(
        "app.auth_routes.exchange_code_and_fetch_profile",
        new_callable=AsyncMock,
        return_value=profile,
    ):
        response = client.get(
            f"/api/auth/callback/google?code=valid-code&state={state}",
            cookies={STATE_COOKIE: cookies[STATE_COOKIE]},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert "ai_doc_session" in response.cookies

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS c FROM users WHERE email = %s",
                (profile["email"],),
            )
            assert cur.fetchone()["c"] == 1
            cur.execute("SELECT COUNT(*) AS c FROM sessions")
            assert cur.fetchone()["c"] >= 1


def test_oauth_callback_github_creates_user(client) -> None:
    """GitHub callback creates user with provider github."""
    cookies = _signed_state_cookie("github")
    state = cookies.pop("state_query")
    profile = {
        "email": f"github-{uuid4()}@example.com",
        "name": "GitHub User",
        "provider_user_id": str(uuid4()),
        "avatar_url": None,
    }

    with patch(
        "app.auth_routes.exchange_code_and_fetch_profile",
        new_callable=AsyncMock,
        return_value=profile,
    ):
        response = client.get(
            f"/api/auth/callback/github?code=valid-code&state={state}",
            cookies={STATE_COOKIE: cookies[STATE_COOKIE]},
            follow_redirects=False,
        )

    assert response.status_code == 302

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT provider FROM users WHERE email = %s",
                (profile["email"],),
            )
            assert cur.fetchone()["provider"] == "github"


def test_oauth_callback_invalid_code_returns_400(client) -> None:
    """Invalid authorization code returns HTTP 400."""
    cookies = _signed_state_cookie("google")
    state = cookies.pop("state_query")

    with patch(
        "app.auth_routes.exchange_code_and_fetch_profile",
        new_callable=AsyncMock,
        side_effect=ValueError("Invalid authorization code"),
    ):
        response = client.get(
            f"/api/auth/callback/google?code=bad&state={state}",
            cookies={STATE_COOKIE: cookies[STATE_COOKIE]},
        )

    assert response.status_code == 400


def test_oauth_callback_second_login_updates_not_duplicates(client) -> None:
    """Second login from same provider updates the same user row."""
    cookies = _signed_state_cookie("google")
    state = cookies.pop("state_query")
    provider_user_id = str(uuid4())
    email = f"dup-{uuid4()}@example.com"

    profile_v1 = {
        "email": email,
        "name": "Version One",
        "provider_user_id": provider_user_id,
        "avatar_url": None,
    }
    profile_v2 = {**profile_v1, "name": "Version Two"}

    with patch(
        "app.auth_routes.exchange_code_and_fetch_profile",
        new_callable=AsyncMock,
        return_value=profile_v1,
    ):
        client.get(
            f"/api/auth/callback/google?code=code1&state={state}",
            cookies={STATE_COOKIE: cookies[STATE_COOKIE]},
        )

    with patch(
        "app.auth_routes.exchange_code_and_fetch_profile",
        new_callable=AsyncMock,
        return_value=profile_v2,
    ):
        client.get(
            f"/api/auth/callback/google?code=code2&state={state}",
            cookies={STATE_COOKIE: cookies[STATE_COOKIE]},
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS c FROM users
                WHERE provider = 'google' AND provider_user_id = %s
                """,
                (provider_user_id,),
            )
            assert cur.fetchone()["c"] == 1
            cur.execute(
                "SELECT name FROM users WHERE provider_user_id = %s",
                (provider_user_id,),
            )
            assert cur.fetchone()["name"] == "Version Two"
