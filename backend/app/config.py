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

    # Phase 3 — LangGraph agents
    agents_model: str = "claude-opus-4-8"
    agents_max_tokens: int = 2048
    # Shared secret required on the n8n trigger endpoint. When empty the trigger
    # endpoint is disabled (returns 503) so it is never unintentionally open.
    agents_trigger_token: str = ""

    # Phase 4 — Knowledge (RAG)
    # OpenAI is used only for embeddings; the chat/answer model stays Anthropic.
    openai_api_key: str = ""
    # Must match the VECTOR(1536) column in schema.sql. Changing the model means
    # changing the dimension, which requires re-indexing every document. See ADR-008.
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    # RecursiveCharacterTextSplitter parameters (tokens). See ADR-009.
    chunk_size: int = 512
    chunk_overlap: int = 64
    # Number of chunks the retriever returns for each query. See ADR-010.
    rag_top_k: int = 5
    rag_system_prompt: str = (
        "You are AI-Doc's knowledge assistant. Answer the user's question using "
        "ONLY the context passages provided below. Each passage is labelled with "
        "the document title it came from. When you use information from a passage, "
        "cite the document title in parentheses, e.g. (Onboarding Guide). If the "
        "answer is not contained in the provided context, say plainly that you "
        "could not find it in the uploaded documents — do not use outside "
        "knowledge and do not invent an answer."
    )
    # Redis connection for persistent conversation memory (Phase 4, Step 6).
    redis_url: str = "redis://localhost:6379"
    # Window of recent turns kept in conversation memory.
    memory_window_turns: int = 10

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
