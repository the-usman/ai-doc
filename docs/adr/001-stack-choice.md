# ADR-001 — Stack choice

**Date:** 2026-06-04
**Status:** Accepted

### Context

Phase 1 requires a platform shell with OAuth, PostgreSQL, Docker, CI, and a multi-application frontend. The programme recommends either a self-contained Next.js app or a React plus FastAPI split typical of AI product teams. The codebase must support clear separation between API logic (sessions, OAuth token exchange) and UI (application registry, navigation).

### Options considered

**Next.js monolith** — Single deployable unit, built-in routing, fewer moving parts locally. OAuth and DB access live in API routes; less explicit backend boundary for later LangServe/LangChain APIs.

**React (Vite) + FastAPI** — Two services in development, one production image possible. Matches common AI engineering stacks, keeps Python for agents/RAG in later phases without a Node backend rewrite.

**Vue/Svelte + FastAPI** — Viable only with prior framework depth; not chosen here.

### Decision

Adopt **React 18 with Vite and TypeScript** for the shell and **FastAPI** for authentication, sessions, and health APIs. PostgreSQL is accessed from Python via psycopg. Production runs a single container: FastAPI serves the built SPA and API on one port.

### Consequences

Easier to add Python-native LangChain/LangGraph in Phases 2–4. Local development runs two containers (api + web) with hot reload. CI must lint and test both stacks. Slightly more compose configuration than a Next.js monolith.
