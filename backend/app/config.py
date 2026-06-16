"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_port: int = 8000
    app_env: str = "development"
    app_secret: str = "dev-secret-change-in-production"
    frontend_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ai-doc"
    db_user: str = "ai-doc_user"
    db_password: str = "password"
    database_url: str | None = None

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback/google"

    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/auth/callback/github"

    oauth_provider: str = "google"

    # Phase 2 — LangChain chat application
    anthropic_api_key: str = ""
    chat_model: str = "claude-opus-4-8"
    chat_max_tokens: int = 4096
    chat_system_prompt: str = (
        "You are AI-Doc's assistant, embedded in a developer platform. "
        "Answer questions about the platform clearly and concisely. "
        "When a question is about platform data — user counts or recent "
        "sign-ins — use the available tools rather than guessing, and base "
        "your answer on the tool results."
    )
    mcp_url: str = "http://localhost:8001"

    @property
    def dsn(self) -> str:
        """
        Build a PostgreSQL connection string.

        Returns:
            Connection URI for psycopg.
        """
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Return cached settings instance.

    Returns:
        Parsed Settings from environment.
    """
    return Settings()
