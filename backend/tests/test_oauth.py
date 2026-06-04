"""OAuth callback integration tests."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from itsdangerous import URLSafeSerializer

from app.auth_routes import STATE_COOKIE
from app.config import get_settings
from app.db import get_connection


def _signed_state_cookie() -> dict[str, str]:
    """Build OAuth state cookie matching callback query."""
    settings = get_settings()
    state = "test-state-value"
    signed = URLSafeSerializer(settings.app_secret, salt="oauth-state").dumps(
        {"state": state, "provider": "google"}
    )
    return {STATE_COOKIE: signed, "state_query": state}


def test_oauth_callback_valid_code_creates_user_and_session(client) -> None:
    """Valid OAuth code upserts user and sets session cookie."""
    cookies = _signed_state_cookie()
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


def test_oauth_callback_invalid_code_returns_400(client) -> None:
    """Invalid authorization code returns HTTP 400."""
    cookies = _signed_state_cookie()
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
    cookies = _signed_state_cookie()
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
