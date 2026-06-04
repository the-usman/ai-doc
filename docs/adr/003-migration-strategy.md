# ADR-003 — Database migration strategy

**Date:** 2026-06-04
**Status:** Accepted

### Context

The database must stay in sync with the repository across local Docker, CI, and Dokploy. Phase 1 only needs `users` and `sessions`; later phases add tables already guarded in `schema/schema.sql`.

### Options considered

**Idempotent `schema/schema.sql`** — `CREATE TABLE IF NOT EXISTS`, triggers, extensions. Simple for a single developer; reapplied safely in CI via `psql -f`.

**Numbered migrations (Alembic/Drizzle)** — Full history and rollbacks; more tooling for a solo programme phase.

### Decision

Use **`schema/schema.sql` as the single source of truth**, applied on first Postgres init (Docker `docker-entrypoint-initdb.d`) and explicitly in CI before tests. Application code does not mutate schema at runtime.

### Consequences

No migration runner dependency. Schema changes require editing one file and re-applying in environments that already exist (manual or reset volume). Acceptable for Phase 1; revisit Alembic if team size or branching schema work grows.
