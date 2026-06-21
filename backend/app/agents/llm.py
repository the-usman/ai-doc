"""Lazy Anthropic model factory for the agent pipeline.

Kept separate from the chat application's factory so the agents can be tuned
(model, token budget) independently, and so the model is only constructed when a
pipeline actually runs — tests patch this and never hit the network.
"""

from typing import Any

from app.config import get_settings


def get_chat_model() -> Any:
    """
    Build the base Anthropic chat model used by the agents.

    Returns:
        A ``ChatAnthropic`` instance configured from agent settings.

    Raises:
        RuntimeError: If no Anthropic API key is configured.
    """
    from langchain_anthropic import ChatAnthropic

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured; the agent pipeline is unavailable."
        )
    return ChatAnthropic(
        model=settings.agents_model,
        api_key=settings.anthropic_api_key,
        max_tokens=settings.agents_max_tokens,
    )
