"""OAuth provider clients and profile normalization."""

from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import Settings


def build_authorize_url(settings: Settings, provider: str, state: str) -> str:
    """
    Build the provider authorization URL for the authorization code flow.

    Args:
        settings: Application settings with client ids and redirect URIs.
        provider: google or github.
        state: CSRF state token.

    Returns:
        URL to redirect the browser to.

    Raises:
        ValueError: If provider is unsupported or not configured.
    """
    if provider == "google":
        if not settings.google_client_id:
            raise ValueError("Google OAuth is not configured")
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    if provider == "github":
        if not settings.github_client_id:
            raise ValueError("GitHub OAuth is not configured")
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    raise ValueError(f"Unsupported provider: {provider}")


async def exchange_code_and_fetch_profile(
    settings: Settings, provider: str, code: str
) -> dict[str, Any]:
    """
    Exchange an authorization code for tokens and fetch the user profile.

    Args:
        settings: Client secrets and redirect URIs.
        provider: google or github.
        code: Authorization code from callback query.

    Returns:
        Normalized profile dict with email, name, provider_user_id, avatar_url.

    Raises:
        httpx.HTTPError: On network failure.
        ValueError: If provider rejects the code or profile is incomplete.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        if provider == "google":
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise ValueError("Invalid authorization code")
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise ValueError("Missing access token from Google")

            profile_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_resp.raise_for_status()
            data = profile_resp.json()
            return {
                "email": data["email"],
                "name": data.get("name"),
                "provider_user_id": data["id"],
                "avatar_url": data.get("picture"),
            }

        if provider == "github":
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "code": code,
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "redirect_uri": settings.github_redirect_uri,
                },
            )
            if token_resp.status_code != 200:
                raise ValueError("Invalid authorization code")
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise ValueError("Missing access token from GitHub")

            user_resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            user_resp.raise_for_status()
            user_data = user_resp.json()

            email = user_data.get("email")
            if not email:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                emails_resp.raise_for_status()
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary")), None)
                email = primary["email"] if primary else emails[0]["email"]

            return {
                "email": email,
                "name": user_data.get("name") or user_data.get("login"),
                "provider_user_id": str(user_data["id"]),
                "avatar_url": user_data.get("avatar_url"),
            }

    raise ValueError(f"Unsupported provider: {provider}")
