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
│  Home (/), Chat (/chat), Docs (/docs), …    │
├─────────────────────────────────────────────┤
│  API (FastAPI)                               │
│  OAuth · sessions · health · chat            │
│  LangChain (LCEL) + LangServe + tools        │
├─────────────────────────────────────────────┤
│  MCP server (tool manifest + call) ──┐       │
├──────────────────────────────────────┼──────┤
│  PostgreSQL (users, sessions) + Redis ◀┘     │
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
        <li>
          <strong>Chat</strong> — A LangChain (LCEL) chain served via LangServe.
          It binds database-backed tools, keeps a per-session memory window, and
          returns structured answers.
        </li>
      </ul>

      <h2>What is MCP?</h2>
      <p>
        The <strong>Model Context Protocol (MCP)</strong> is a shared standard
        for how AI assistants discover and call external tools. Instead of every
        assistant learning a bespoke way to reach each tool, an MCP server
        publishes a <em>manifest</em> describing the tools it offers, and clients
        call them through one consistent interface.
      </p>
      <p>
        Our MCP server runs as its own service and exposes the platform's two
        database tools — the current user count and recent sign-ins. The chat
        assistant uses these tools today; from Phase 3, autonomous agents will
        reach the same tools through MCP. Standardising on MCP now means each new
        capability we add becomes available to every future client without custom
        wiring.
      </p>
    </article>
  );
}
