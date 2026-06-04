"""Pytest fixtures for API and database tests."""

import os

import pytest
from fastapi.testclient import TestClient

# Ensure test settings before app import side effects
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET", "test-secret-for-ci-only")
os.environ.setdefault("DB_HOST", os.environ.get("DB_HOST", "localhost"))
os.environ.setdefault("DB_PORT", os.environ.get("DB_PORT", "5432"))
os.environ.setdefault("DB_NAME", os.environ.get("DB_NAME", "ai_doc_test"))
os.environ.setdefault("DB_USER", os.environ.get("DB_USER", "test_user"))
os.environ.setdefault("DB_PASSWORD", os.environ.get("DB_PASSWORD", "test_password"))
os.environ.setdefault(
    "DATABASE_URL",
    f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}",
)
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://testserver/api/auth/callback/google")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("OAUTH_PROVIDER", "google")

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Reset settings cache between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """
    HTTP client against the FastAPI app.

    Yields:
        TestClient with cookie jar support.
    """
    return TestClient(app)
