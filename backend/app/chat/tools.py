"""LangChain tools exposed to the chat model.

Each tool wraps a plain query function from ``queries.py``. The docstrings here
are deliberately descriptive: LangChain passes them to the LLM as the tool
description, so a clear docstring directly improves the model's ability to
decide when and how to call the tool.
"""

from langchain_core.tools import tool

from app.chat import queries


@tool
def get_platform_user_count() -> int:
    """Return the current number of registered users on the platform.

    Queries the ``users`` table in the platform's PostgreSQL database and
    returns the total count. Use this whenever the user asks how many people
    have signed up, how big the user base is, or for the current user total.
    """
    return queries.count_platform_users()


@tool
def get_recent_signins(limit: int = 5) -> list[dict]:
    """Return the most recent sign-in events, newest first.

    Args:
        limit: How many recent sign-ins to return (1–50, default 5).

    Queries the ``sessions`` table joined to ``users`` and returns, for each
    recent sign-in, the user's email, name, OAuth provider, and the sign-in
    timestamp. Use this when the user asks who signed in recently, for recent
    activity, or about the latest logins.
    """
    return queries.recent_signins(limit)


@tool
def get_user_provider_breakdown() -> dict:
    """Return a breakdown of registered users by OAuth provider.

    Queries the ``users`` table and returns a mapping of provider (e.g.
    ``google``, ``github``) to the number of users who signed up with it. Use
    this when the user asks how the user base splits across login providers, or
    how many users use a particular provider.
    """
    return queries.provider_breakdown()


# All tools bound to the chat model, plus a name->callable map used by the
# tool-execution loop in ``chain.py`` and by the MCP server.
TOOLS = [get_platform_user_count, get_recent_signins, get_user_provider_breakdown]

TOOL_FUNCTIONS = {
    "get_platform_user_count": queries.count_platform_users,
    "get_recent_signins": queries.recent_signins,
    "get_user_provider_breakdown": queries.provider_breakdown,
}
