# ADR-011 — Redis-backed conversation memory and per-application scope

**Date:** 2026-06-23
**Status:** Accepted
**Phase:** 4 — Knowledge (RAG)

### Context

Phase 1's chat kept conversation history in an in-process dictionary — fine for a
single process, but it evaporates on restart and is not shared across workers or
replicas. Phase 4 adds a second conversational surface (Knowledge Chat) that also
needs memory, which forces two questions at once: where should history live so it
survives restarts and is shared across processes, and how should the chat
application's history be kept separate from the knowledge application's so the two
conversations never bleed into each other.

### Options considered

**Where memory lives.**
- **In-process dict (status quo).** Zero dependencies, but lost on restart and not
  shared across replicas.
- **Redis via LangChain's `RedisChatMessageHistory`.** Persistent, shared across
  processes, with native list operations well-suited to append-and-trim history;
  one more service to run.
- **A Postgres history table.** Reuses the existing database, but turns a simple
  recency-windowed list into schema, indexes, and pruning logic for data that is
  inherently ephemeral.

**How history is partitioned.**
- **One shared history per session.** Simplest, but mixes chat and knowledge turns
  into one stream so each surface sees the other's messages.
- **A scope prefix per application.** Each surface namespaces its keys
  (`aidoc:history:<scope>:<session>`), keeping conversations isolated while sharing
  one storage mechanism.

### Decision

Store conversation history in **Redis via `RedisChatMessageHistory`**, behind a
shared `app/memory.py` module that **namespaces every key by an application scope**
(`chat`, `knowledge`) and falls back to an in-process store when Redis is
unavailable.

Redis is chosen because history is an append-and-trim recency window — exactly what
Redis lists do well — and because it gives persistence across restarts and sharing
across processes without modelling ephemeral data as relational schema. `redis_url`
and `memory_window_turns` are config values.

The scope prefix is the partitioning decision: `app/memory.py` exposes
`get_history(scope, session_id)`, `append_turn(scope, ...)`, and `clear(scope, ...)`,
keying storage as `aidoc:history:<scope>:<session_id>`. The chat and knowledge
surfaces pass their own scope, so the same session id yields two independent
histories and neither conversation pollutes the other. `chat/memory.py` becomes a
thin adapter that delegates to the shared module with `scope="chat"`, preserving its
existing API so Phase 1's chat chain and its tests are untouched.

Resilience is built in: if Redis cannot be reached, the module transparently falls
back to an in-process dictionary (the prior behaviour) and the application keeps
working — degraded to single-process memory rather than broken. History is trimmed
to `memory_window_turns` turns so prompts stay bounded.

### Consequences

- Conversation history survives restarts and is shared across processes/replicas,
  and the chat and knowledge surfaces are cleanly isolated by scope despite sharing
  one mechanism.
- Adding memory to a future application is just a new scope string — no new storage
  code or table.
- Redis becomes an expected (but non-fatal) dependency; the in-process fallback
  keeps the app running without it, at the cost of losing persistence and cross-
  process sharing while Redis is down. The fallback path is deliberately silent so a
  missing Redis degrades rather than crashes.
- Refactoring `chat/memory.py` to delegate keeps one implementation of the
  append-and-trim logic, so a fix or change applies to every conversational surface
  at once.
