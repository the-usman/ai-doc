# ADR-002 — OAuth provider and flow design

**Date:** 2026-06-04
**Status:** Accepted

### Context

Phase 1 requires single sign-on without password storage. Users must be identified by OAuth provider plus provider user id, not email alone.

### Options considered

**Google OAuth** — Universal for client demos, straightforward consent screen.

**GitHub OAuth** — Simpler app registration, strong for developer audiences.

**Username/password** — Rejected: credential management, reset flows, and breach surface are out of scope for Phase 1.

### Decision

Implement the **OAuth 2.0 authorization code flow** with **Google** as the default provider (`OAUTH_PROVIDER=google`). GitHub remains configurable via environment variables.

Flow: redirect to provider → user authenticates → callback with `code` → **server-side** exchange for tokens (secret never exposed to browser) → fetch profile → upsert `users` by `(provider, provider_user_id)` → create `sessions` row → set **httpOnly** session cookie → redirect to platform home.

The **`state`** parameter is generated per login, stored server-side (signed cookie), and validated on callback to prevent CSRF.

### Consequences

Requires Google Cloud OAuth client and redirect URIs for local and production. Session validation happens on every protected API call. Invalid or replayed `state` rejects the callback with HTTP 400.
