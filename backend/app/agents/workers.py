"""Worker nodes for the agent pipeline.

* **DataAgent** — a ReAct agent (``create_react_agent``) wired to the Phase 2
  database tools. It answers questions about users and sign-in activity.
* **ReportAgent** — an LCEL synthesis chain that turns the accumulated results
  into a short written summary.

Both are exposed as LangGraph nodes: functions that take the current state and
return a partial state update appending their result. They are tested in
isolation with a mock state before the graph is assembled (see ADR-007).
"""

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agents.llm import get_chat_model
from app.agents.state import PipelineState
from app.chat.tools import TOOLS

_DATA_AGENT_PROMPT = (
    "You are DataAgent. Answer questions about the platform's users and sign-in "
    "activity using the available tools. Always call a tool to get real data "
    "rather than guessing, then state the answer plainly."
)

_REPORT_SYSTEM_PROMPT = (
    "You are ReportAgent. Write a brief, clear summary (a few sentences) of the "
    "findings below for a non-technical reader. Lead with the key result. Do not "
    "invent facts that are not in the findings."
)


def get_data_agent() -> Any:
    """
    Build the DataAgent ReAct agent bound to the platform tools.

    Returns:
        A compiled ReAct agent runnable.
    """
    from langgraph.prebuilt import create_react_agent

    # langgraph 0.2.x uses ``state_modifier`` for the system prompt; the ``prompt``
    # keyword was only introduced in 0.3.0. A plain string is accepted here and
    # applied as the agent's system message.
    return create_react_agent(get_chat_model(), TOOLS, state_modifier=_DATA_AGENT_PROMPT)


def get_report_chain() -> Any:
    """
    Build the ReportAgent synthesis chain (prompt -> model -> string).

    Returns:
        A runnable producing a summary string.
    """
    prompt = ChatPromptTemplate.from_messages(
        [("system", _REPORT_SYSTEM_PROMPT), ("human", "{context}")]
    )
    return prompt | get_chat_model() | StrOutputParser()


def _last_text(messages: list[BaseMessage]) -> str:
    """Return the text of the last AI message in a ReAct agent result."""
    for message in reversed(messages):
        if getattr(message, "type", None) == "ai":
            content = message.content
            if isinstance(content, str):
                return content.strip()
            parts = [
                str(block.get("text", ""))
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            text = "".join(parts).strip()
            if text:
                return text
    return ""


def data_agent_node(state: PipelineState) -> dict:
    """
    Run the DataAgent on the task and append its result.

    Args:
        state: The current pipeline state.

    Returns:
        A state update appending the DataAgent's result.
    """
    agent = get_data_agent()
    result = agent.invoke({"messages": [HumanMessage(content=state["task"])]})
    output = _last_text(result["messages"])
    return {"worker_results": [{"worker": "DataAgent", "output": output}]}


def _render_findings(state: PipelineState) -> str:
    """Render the task and gathered results as context for the report."""
    lines = [f"Task: {state.get('task', '')}", "", "Findings:"]
    for item in state.get("worker_results", []):
        lines.append(f"- {item['worker']}: {item['output']}")
    return "\n".join(lines)


def report_agent_node(state: PipelineState) -> dict:
    """
    Synthesise accumulated results into a summary and append it.

    Args:
        state: The current pipeline state.

    Returns:
        A state update appending the ReportAgent's summary.
    """
    summary = get_report_chain().invoke({"context": _render_findings(state)})
    return {"worker_results": [{"worker": "ReportAgent", "output": summary}]}
