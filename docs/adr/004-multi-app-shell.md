# ADR-004 — Multi-application shell architecture

**Date:** 2026-06-04
**Status:** Accepted

### Context

AI-Doc is a platform: one login, many applications with own URL prefixes and sub-navigation. Retrofitting this onto a single-route app later is costly.

### Options considered

**Separate deployments per tool** — Independent releases but duplicated auth and no unified navigation.

**Single SPA with central app registry** — One shell reads configuration and renders switcher plus per-app sub-nav.

**Micro-frontends** — Overkill for Phase 1 scope.

### Decision

**React shell** with `appRegistry.ts`: each app defines `key`, `name`, `icon`, `rootPath`, and `subNav`. Routes nest under `/` (Home) and `/docs` (Docs). Authenticated layout wraps all platform routes; API session cookie gates access. Phase 2+ apps add one registry entry only.

### Consequences

Adding Chat/Agents/Knowledge is registration-only. Sub-navigation hides when another app is active. Backend remains unaware of frontend app list except for shared auth.
