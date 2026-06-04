/**
 * Docs — Architecture page with platform layer diagram.
 */
export function DocsArchitecture() {
  return (
    <article>
      <h1>Architecture</h1>
      <p>
        AI-Doc is a multi-application platform. One authentication layer serves
        every application; each app owns its routes and sub-navigation under a
        URL prefix.
      </p>
      <pre className="diagram">{`┌─────────────────────────────────────────────┐
│  Platform shell (React)                      │
│  • SSO session cookie                        │
│  • Application switcher                      │
│  • Per-app sub-navigation                    │
├─────────────────────────────────────────────┤
│  Applications                                │
│  Home (/), Docs (/docs), Chat, Agents, …   │
├─────────────────────────────────────────────┤
│  API (FastAPI)                               │
│  OAuth · sessions · health                   │
├─────────────────────────────────────────────┤
│  PostgreSQL (users, sessions) + Redis        │
└─────────────────────────────────────────────┘`}</pre>
      <h2>Components</h2>
      <ul>
        <li>
          <strong>Shell</strong> — Authenticated layout and app registry in{" "}
          <code>appRegistry.ts</code>.
        </li>
        <li>
          <strong>API</strong> — FastAPI service for OAuth, session validation,
          and health checks.
        </li>
        <li>
          <strong>Database</strong> — PostgreSQL with idempotent{" "}
          <code>schema/schema.sql</code>.
        </li>
        <li>
          <strong>Redis</strong> — Reserved for conversational memory (Phase 4+).
        </li>
      </ul>
    </article>
  );
}
