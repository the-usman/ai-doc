"""Minimal Model Context Protocol (MCP) server for the platform tools.

MCP is a standard way for AI clients to *discover* and *call* tools through one
consistent interface, instead of every client hard-coding how to reach every
tool. This server exposes the same two database-backed tools the LangChain
chatbot uses (Phase 2, Step 4) so that Phase 3's agents can call them through a
shared, language-agnostic contract.

It runs as its own Docker service (see ``docker-compose.yml``) and speaks plain
JSON over HTTP:

* ``GET  /mcp/tools`` — the tool manifest: a JSON description of every tool,
  including its name, human description, and JSON-Schema input.
* ``POST /mcp/call``  — execute a tool by name with arguments and return the
  result.

Both handlers run the real database query — there is no mock data.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.chat import queries

app = FastAPI(title="AI-Doc MCP Server", version="0.1.0")

# The tool manifest. Each entry is self-describing so a client can render or
# validate calls without out-of-band knowledge.
TOOL_MANIFEST: list[dict[str, Any]] = [
    {
        "name": "get_platform_user_count",
        "description": "Return the current number of registered platform users.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_recent_signins",
        "description": "Return the N most recent sign-in events, newest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "How many events to return (1-50).",
                    "default": 5,
                }
            },
            "required": [],
        },
    },
]

# Maps a tool name to the plain query function that backs it.
_DISPATCH = {
    "get_platform_user_count": lambda args: queries.count_platform_users(),
    "get_recent_signins": lambda args: queries.recent_signins(int(args.get("limit", 5))),
}


class ToolCallRequest(BaseModel):
    """A request to execute one tool."""

    name: str = Field(description="The tool name from the manifest.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool.")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """
    Liveness probe for Docker.

    Returns:
        A small JSON status payload.
    """
    return {"status": "ok", "service": "ai-doc-mcp"}


@app.get("/mcp/tools")
def list_tools() -> dict[str, list[dict[str, Any]]]:
    """
    Return the MCP tool manifest.

    Returns:
        JSON describing every available tool and its input schema.
    """
    return {"tools": TOOL_MANIFEST}


@app.post("/mcp/call")
def call_tool(request: ToolCallRequest) -> dict[str, Any]:
    """
    Execute a tool by name and return its result.

    Args:
        request: The tool name and arguments.

    Returns:
        JSON with the tool name and its ``result``.

    Raises:
        HTTPException: 404 if the tool is unknown, 502 if the query fails.
    """
    handler = _DISPATCH.get(request.name)
    if handler is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {request.name}")
    try:
        result = handler(request.arguments)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=502, detail=f"Tool failed: {exc}") from exc
    return {"tool": request.name, "result": result}
