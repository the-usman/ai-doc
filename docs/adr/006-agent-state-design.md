# ADR-006 — LangGraph agent state design

**Date:** 2026-06-16
**Status:** Accepted
**Phase:** 3 — Agents

### Context

Phase 3 upgrades the single-call chat into an orchestrated multi-agent system
built on LangGraph. LangGraph's model is a directed graph of nodes that each read
from and write to a single shared, typed state object. The state object is the
backbone of the whole system: every node depends on it, and its shape determines
what the graph can and cannot do. A field missing from the state is a capability
the graph cannot have. Designing it before writing any node — rather than growing
it reactively as each node needs something — is the discipline this phase teaches,
because a poorly shaped state causes constant friction as the graph grows.

The state lives in `backend/app/agents/state.py` as a `TypedDict`
(`PipelineState`) with `total=False`, so a node may return *only* the fields it
changed and LangGraph merges the partial update into the running state using each
field's reducer.

### Decision

`PipelineState` holds exactly five fields, each justified below.

**`task: str`** — the incoming task description. Set once when the run starts;
every node reads it to know what is being asked. Without it a worker would have no
input and the supervisor nothing to route on.

**`next: str`** — the supervisor's routing decision: a worker name
(`"DataAgent"` / `"ReportAgent"`) or `"FINISH"`. The graph's conditional edge
reads this single field to decide where to go next, which keeps the routing
function trivial. Last write wins (no reducer) — each supervisor visit overwrites
the previous decision, which is exactly what routing needs.

**`worker_results: Annotated[list[WorkerResult], operator.add]`** — the list of
results accumulated so far, one entry (`{worker, output}`) per worker invocation.
This is the only field with an **additive reducer**: each worker returns a
single-element list and LangGraph *appends* it rather than overwriting. Without
the reducer, only the last worker's output would survive, the supervisor would
lose the history it routes on, and the ReportAgent would have nothing to
synthesise. This field is also persisted as the run trace.

**`status: str`** — `in_progress` | `completed` | `failed`. Drives persistence
(which terminal row is written) and the UI badge. Without it the service layer
could not tell a finished run from one that died mid-flight.

**`final_output: str`** — the synthesised answer the supervisor produces when it
decides the run is finished. Kept separate from `worker_results` so the UI and
the database have one canonical answer to show without re-deriving it from the
trace.

### Consequences

- A node returning a partial update is safe because `total=False` plus per-field
  reducers define the merge precisely; there is no read-modify-write race on the
  accumulating `worker_results` list.
- Adding a new worker capability later means adding a node and a `next` literal —
  not reshaping the state. The state is forward-compatible by design.
- The trace stored in `pipeline_runs.trace` is exactly `worker_results`, so the
  Run History page reconstructs the run from the same structure the graph used.
