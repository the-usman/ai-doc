# ADR-005 — LangChain chat architecture

**Date:** 2026-06-16
**Status:** Accepted
**Phase:** 2 — LangChain

### Context

Phase 2 adds a chat application backed by an LLM with access to real platform
data. The phase requires a bottom-up LangChain design — understand the core
abstractions (Runnable, LCEL, prompt templates, output parsers) before adding
agents — plus structured output, tool use, conversation memory, a LangServe API,
and an MCP server exposing the tools.

### Decisions

**LCEL over direct SDK calls.** The chain is composed with LangChain Expression
Language: `prompt | model | parser`. Every step is a `Runnable` with the same
`invoke` interface, which buys composability, streaming, consistent testing, and
tracing. A baseline `build_baseline_chain` (`ChatPromptTemplate` → `ChatAnthropic`
→ `StrOutputParser`) validates the wiring before any application logic; the
production path (`invoke_chat`) layers tools, memory, and structured output on
top.

**Model.** `claude-opus-4-8` via `langchain-anthropic`, configured through
`CHAT_MODEL` / `CHAT_MAX_TOKENS`. The model is constructed lazily so the module
imports without an API key and tests run by patching the model factories.

**Structured output.** Answers are validated against a Pydantic `ChatResponse`
(`response`, `confidence` ∈ low/medium/high, `sources`) using the model's
`with_structured_output`. When the model's output cannot be coerced to the
schema, LangChain raises rather than returning malformed data; the route maps
that to an HTTP 502 so the frontend degrades cleanly. `sources` is reconciled in
code against the tools actually executed, so it is always accurate regardless of
what the model reports.

**Tools.** Two `@tool` functions — `get_platform_user_count` and
`get_recent_signins` — wrap plain query functions in `chat/queries.py` and hit
the real PostgreSQL database. The plain functions carry no LangChain dependency
so they are shared with the MCP server and unit-tested directly. Tool docstrings
double as the LLM-facing descriptions. Tools are bound with `bind_tools`, and
`invoke_chat` runs a bounded tool-call loop, executing each requested tool and
feeding `ToolMessage` results back until the model produces a final answer.

**Memory.** The phase names `ConversationBufferWindowMemory` (10-turn window).
That class lives in the deprecated legacy `langchain` memory module; we implement
the same sliding-window behaviour on the stable `langchain_core` message
primitives, keyed by the Phase 1 auth session id. History is in-process; Redis
(already provisioned) is the seam for multi-process persistence in a later phase.

**LangServe.** The chain is served at `/api/chat` via `add_routes`, giving
`/invoke`, `/stream`, and `/playground` with input validation and schema
exposure for free. The frontend uses a thin authenticated `/api/chat/message`
route that derives the session key from the cookie; LangServe routes take the
session id in the request body for development and demos.

**MCP server.** A minimal FastAPI service exposes the same tools over the Model
Context Protocol: `GET /mcp/tools` returns a manifest, `POST /mcp/call` executes
a tool. It runs as its own Docker service and shares `chat/queries.py`, so the
tool logic has a single source of truth. This establishes the tool
infrastructure Phase 3's agents will call.

### Consequences

- The chat extras (`langchain-core`, `langchain-anthropic`, `langserve`) are
  heavy optional dependencies. The API guards their import so auth and health
  keep serving if they are absent; chat tests skip when the stack is missing.
- Memory is not durable across restarts — acceptable for Phase 2, revisited with
  Redis/persistence later.
- The MCP server duplicates a thin manifest definition, accepted in exchange for
  keeping the protocol surface explicit and the query logic shared.
