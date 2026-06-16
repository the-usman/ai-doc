"""Structured-output schema for the chat chain.

The chain does not return free-form text. Every answer is validated against
``ChatResponse`` before it leaves the API, which gives the frontend a stable
shape to render and makes the assistant's confidence and tool usage explicit.
"""

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]


class ChatResponse(BaseModel):
    """Structured answer returned by the chat chain."""

    response: str = Field(description="The natural-language answer for the user.")
    confidence: Confidence = Field(
        default="medium",
        description="How confident the assistant is in the answer.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Names of any tools that were called to produce the answer.",
    )


class ChatInput(BaseModel):
    """Input payload accepted by the LangServe chat chain."""

    message: str = Field(description="The user's message to the assistant.")
    session_id: str = Field(
        default="playground",
        description="Conversation key; isolates memory between users.",
    )
