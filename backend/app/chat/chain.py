"""LCEL chat chain: prompt -> model -> tools -> structured output, with memory.

Built bottom-up, as Phase 2 prescribes:

1. ``build_baseline_chain`` is the minimal ``prompt | model | parser`` LCEL chain
   used to validate the model wiring before any application logic.
2. ``invoke_chat`` is the full application path: it binds tools, runs the
   tool-call loop against the real database, keeps per-session memory, and
   returns a validated :class:`ChatResponse`.

The Anthropic model (``claude-opus-4-8`` by default) is constructed lazily so
the module imports cleanly without an API key — tests patch the model factories
and never hit the network. See ADR-005 for the design rationale.
"""

import json
from typing import Any

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda

from app.chat import memory
from app.chat.schemas import ChatInput, ChatResponse
from app.chat.tools import TOOL_FUNCTIONS, TOOLS
from app.config import get_settings

# Cap the tool-call loop so a model that keeps requesting tools cannot spin
# forever.
MAX_TOOL_ITERATIONS = 5

_FORMAT_INSTRUCTION = (
    "Using the conversation above, produce the final answer. Set `response` to "
    "the answer text, `confidence` to low, medium, or high, and `sources` to "
    "the names of any tools that were called."
)


def get_chat_model() -> Any:
    """
    Build the base Anthropic chat model.

    Returns:
        A ``ChatAnthropic`` instance configured from settings.

    Raises:
        RuntimeError: If no Anthropic API key is configured.
    """
    from langchain_anthropic import ChatAnthropic

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured; the chat assistant is unavailable."
        )
    return ChatAnthropic(
        model=settings.chat_model,
        api_key=settings.anthropic_api_key,
        max_tokens=settings.chat_max_tokens,
    )


def get_tool_model() -> Any:
    """
    Return the base model with the platform tools bound to it.

    Returns:
        A runnable chat model that may emit tool calls.
    """
    return get_chat_model().bind_tools(TOOLS)


def get_structured_model() -> Any:
    """
    Return a model that emits a validated :class:`ChatResponse`.

    Returns:
        A runnable that parses the model output into ``ChatResponse``.
    """
    return get_chat_model().with_structured_output(ChatResponse)


def _system_message() -> SystemMessage:
    """Return the system message describing the assistant's purpose."""
    return SystemMessage(content=get_settings().chat_system_prompt)


def build_baseline_chain() -> Runnable:
    """
    Build the minimal LCEL chain: prompt template -> model -> string parser.

    This is the Phase 2 "baseline" chain — it takes a ``{"message": ...}`` dict,
    formats it with a system + human ``ChatPromptTemplate``, sends it to the
    model, and returns a plain string. It carries no tools or memory and exists
    to validate the model wiring independently of application logic.

    Returns:
        A runnable producing a string answer.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_settings().chat_system_prompt),
            ("human", "{message}"),
        ]
    )
    return prompt | get_chat_model() | StrOutputParser()


def _text_of(message: BaseMessage) -> str:
    """
    Extract plain text from a model message whose content may be blocks.

    Args:
        message: A LangChain message.

    Returns:
        The concatenated text content.
    """
    content = message.content
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "".join(parts).strip()


def invoke_chat(session_id: str, message: str) -> ChatResponse:
    """
    Run the full chat turn: memory + tool loop + structured output.

    Args:
        session_id: Conversation key (the Phase 1 auth session id in the app).
        message: The user's message.

    Returns:
        A validated :class:`ChatResponse` with the answer, a confidence rating,
        and the names of any tools that were called.

    Side effects:
        Executes database queries for any tools the model calls and appends the
        completed turn to the session's memory.
    """
    tool_model = get_tool_model()
    messages: list[BaseMessage] = [
        _system_message(),
        *memory.get_history(session_id),
        HumanMessage(content=message),
    ]

    sources: list[str] = []
    ai_message: BaseMessage = HumanMessage(content="")
    for _ in range(MAX_TOOL_ITERATIONS):
        ai_message = tool_model.invoke(messages)
        messages.append(ai_message)
        tool_calls = getattr(ai_message, "tool_calls", None) or []
        if not tool_calls:
            break
        for call in tool_calls:
            name = call["name"]
            args = call.get("args") or {}
            sources.append(name)
            func = TOOL_FUNCTIONS.get(name)
            try:
                result: Any = func(**args) if func else f"Unknown tool: {name}"
            except Exception as exc:  # surface tool failures back to the model
                result = f"Tool error: {exc}"
            messages.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=call.get("id", name),
                )
            )

    final_text = _text_of(ai_message)

    structured_model = get_structured_model()
    structured: ChatResponse = structured_model.invoke(
        messages + [HumanMessage(content=_FORMAT_INSTRUCTION)]
    )
    if not structured.response:
        structured.response = final_text
    # Guarantee `sources` reflects the tools actually executed, de-duplicated and
    # order-preserving, regardless of what the model reported.
    merged = list(dict.fromkeys(sources + list(structured.sources or [])))
    structured.sources = merged

    memory.append_turn(session_id, message, structured.response)
    return structured


def _run_for_langserve(payload: Any) -> dict:
    """
    Adapter so the chat turn can be served by LangServe.

    Args:
        payload: A ``ChatInput`` or an equivalent dict.

    Returns:
        The ``ChatResponse`` serialised to a dict.
    """
    data = payload if isinstance(payload, ChatInput) else ChatInput(**payload)
    return invoke_chat(data.session_id, data.message).model_dump()


# The runnable LangServe mounts at /api/chat. ``with_types`` gives the
# /playground page a typed input form and output schema.
chat_chain: Runnable = RunnableLambda(_run_for_langserve).with_types(
    input_type=ChatInput, output_type=ChatResponse
)
