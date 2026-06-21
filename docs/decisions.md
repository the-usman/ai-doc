# Architecture Decision Records

This file is the living log of every significant architectural decision made during the development of AI-Doc. A decision belongs here if it involved a genuine choice between alternatives, if the reasoning is not visible from the code alone, or if someone reading the codebase six months from now would reasonably wonder why a particular approach was taken.

The goal is not to document every line of code. It is to capture the context and reasoning behind choices that are difficult to reverse or that carry meaningful tradeoffs — so that future contributors, including yourself, can understand and build on the decisions rather than inadvertently undoing them.

---

## Template

Copy this template for each new ADR. Number them sequentially.

```
## ADR-XXX — [Short descriptive title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded by ADR-XXX

### Context
One paragraph. What problem were you solving? What constraints were in play?
What made this a non-trivial decision rather than an obvious one?

### Options considered
A brief description of two or more approaches you evaluated.

### Decision
What did you choose and why? Reference the options above by name.

### Consequences
What becomes easier as a result of this decision?
What becomes harder or more constrained?
What are the known risks or tradeoffs you are accepting?
```

---

## ADR-001 — Stack choice

**Date:** 2026-06-04  
**Status:** Accepted  
**Full text:** [docs/adr/001-stack-choice.md](adr/001-stack-choice.md)

React (Vite) + FastAPI with PostgreSQL. Production serves the built SPA from the API container on port 3000.

---

## ADR-002 — OAuth provider and flow design

**Date:** 2026-06-04  
**Status:** Accepted  
**Full text:** [docs/adr/002-oauth-flow.md](adr/002-oauth-flow.md)

Google OAuth authorization code flow with server-side token exchange and signed `state` for CSRF protection.

---

## ADR-003 — Database migration strategy

**Date:** 2026-06-04  
**Status:** Accepted  
**Full text:** [docs/adr/003-migration-strategy.md](adr/003-migration-strategy.md)

Idempotent `schema/schema.sql` applied via Docker init and CI `psql -f`.

---

## ADR-004 — Multi-application shell architecture

**Date:** 2026-06-04  
**Status:** Accepted  
**Full text:** [docs/adr/004-multi-app-shell.md](adr/004-multi-app-shell.md)

Central `appRegistry.ts`; shell owns SSO and top-level navigation; apps own sub-routes under `/` and `/docs`.

---

## ADR-005 — LangChain chat architecture

**Date:** 2026-06-16  
**Status:** Accepted  
**Full text:** [docs/adr/005-langchain.md](adr/005-langchain.md)

LCEL chain with structured output; bound database tools; sliding-window memory keyed by session; served via LangServe; tools also exposed over MCP.

---

## ADR-006 — LangGraph agent state design

**Date:** 2026-06-16  
**Status:** Accepted  
**Full text:** [docs/adr/006-agent-state-design.md](adr/006-agent-state-design.md)

Five-field `PipelineState` TypedDict; `worker_results` uses an additive reducer so workers append rather than overwrite; field-by-field reasoning recorded.

---

## ADR-007 — Supervisor routing and worker responsibilities

**Date:** 2026-06-16  
**Status:** Accepted  
**Full text:** [docs/adr/007-supervisor-workers.md](adr/007-supervisor-workers.md)

Supervisor is an LCEL chain emitting a structured `RouteDecision`; DataAgent (ReAct + DB tools) gathers, ReportAgent (tool-free) synthesises; conditional edge routes on `state["next"]` with a `MAX_WORKER_STEPS` safety cap.

---

*Add new ADRs below this line as the project progresses. Each phase requires at least one new ADR. By Phase 5, the ADR log should contain a minimum of ten records covering all major decisions across the system.*
