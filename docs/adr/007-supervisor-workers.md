# ADR-007 — Supervisor routing and worker responsibilities

**Date:** 2026-06-16
**Status:** Accepted
**Phase:** 3 — Agents

### Context

With the state designed (ADR-006), Phase 3 implements the supervisor-and-worker
pattern: a supervisor that decides who acts next, specialised workers that do the
work, and a compiled `StateGraph` that wires them together. This ADR records how
the supervisor routes, what each worker is responsible for, and why the graph is
shaped the way it is.

### Decision

**Supervisor as an LCEL chain with structured output.** The supervisor
(`agents/supervisor.py`) is the graph's entry node and the node every worker
returns to. It is a LangChain chain — `get_chat_model().with_structured_output(
RouteDecision)` — prompted to act as an orchestrator: read the task and the
results gathered so far, then emit a single `RouteDecision` whose `next` field is
`"DataAgent"`, `"ReportAgent"`, or `"FINISH"`. Structured output (rather than
free-text parsing) is what makes the conditional edge trivial — the graph routes
purely on `state["next"]`. When the decision is `FINISH`, the supervisor
synthesises `final_output` (preferring the latest ReportAgent result) and sets
`status="completed"` in the same update.

**Safety bound on iterations.** A `MAX_WORKER_STEPS` cap (6) stops the run even
if the model never says `FINISH`, so a misbehaving LLM cannot loop the graph
forever. This is checked before the model is called, so the cap is enforced
without an extra LLM round-trip.

**Two workers, distinct responsibilities and tool access.**

- **DataAgent** — a ReAct agent built with `create_react_agent` and bound to the
  Phase 2 MCP-backed database tools (`get_platform_user_count`,
  `get_recent_signins`, `get_user_provider_breakdown`). Its job is to answer
  questions about platform users and sign-in activity by calling tools for real
  data rather than guessing. It is the only worker with tool access.
- **ReportAgent** — a tool-free LCEL synthesis chain (`prompt | model |
  StrOutputParser`). Its job is to turn the accumulated findings into a brief,
  plain-language summary for a non-technical reader. It has no database access by
  design: synthesis should work only from what previous workers gathered, never
  invent new data.

Each worker is a LangGraph node — a function taking the current state and
returning a partial update that *appends* one `WorkerResult`. Both are tested in
isolation with a mock state object before the graph is assembled, so a
misbehaving full graph can be debugged with the workers already ruled out.

**Graph topology.** `START → supervisor`; a conditional edge from the supervisor
routes to `DataAgent`, `ReportAgent`, or `END`; normal edges return each worker
to the supervisor. The node functions are resolved on their modules at call time
so tests can patch them before `build_graph()` compiles. This shape is infinitely
extensible: a new capability is a new node plus a new `next` literal, not a
restructuring.

### Consequences

- Routing logic is concentrated in one prompt and one Pydantic schema; the graph
  code stays declarative and the conditional edge is a one-line lookup.
- The DataAgent/ReportAgent split mirrors the gather-then-synthesise shape of the
  tasks, and the three-way test matrix (DataAgent only, ReportAgent only, both in
  sequence) exercises every routing path.
- Giving only the DataAgent tools keeps the trust boundary clear: exactly one
  worker touches the database, and the ReportAgent cannot fabricate figures.
- The step cap trades a small risk of truncating a legitimately long run for a
  hard guarantee that a run terminates — acceptable for the current two-worker
  pipeline.
