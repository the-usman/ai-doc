/**
 * Docs — Architecture Decision Records summary.
 */
export function DocsDecisions() {
  const adrs = [
    {
      id: "ADR-001",
      title: "Stack choice",
      summary: "React (Vite) + FastAPI; PostgreSQL via psycopg.",
    },
    {
      id: "ADR-002",
      title: "OAuth provider and flow",
      summary:
        "Google OAuth authorization code flow; server-side token exchange; CSRF state parameter.",
    },
    {
      id: "ADR-003",
      title: "Migration strategy",
      summary: "Idempotent schema/schema.sql as single source of truth.",
    },
    {
      id: "ADR-004",
      title: "Multi-application shell",
      summary: "Central app registry; shell owns auth and top-level navigation.",
    },
    {
      id: "ADR-005",
      title: "LangChain chat architecture",
      summary:
        "LCEL chain with structured output; bound database tools; sliding-window memory keyed by session; served via LangServe; tools also exposed over MCP.",
    },
    {
      id: "ADR-006",
      title: "LangGraph agent state design",
      summary:
        "Five-field PipelineState TypedDict; worker_results uses an additive reducer so workers append rather than overwrite; field-by-field reasoning recorded.",
    },
    {
      id: "ADR-007",
      title: "Supervisor routing and worker responsibilities",
      summary:
        "Supervisor is an LCEL chain emitting a structured RouteDecision; DataAgent (ReAct + DB tools) gathers, ReportAgent (tool-free) synthesises; conditional edge routes on state.next with a step-count safety cap.",
    },
  ];

  return (
    <article>
      <h1>Decisions</h1>
      <p>
        Living log of architecture decisions. Full text lives in{" "}
        <code>docs/adr/</code> in the repository and should stay in sync with
        this page.
      </p>
      <ul className="adrList">
        {adrs.map((adr) => (
          <li key={adr.id}>
            <h2>
              {adr.id} — {adr.title}
            </h2>
            <p>{adr.summary}</p>
          </li>
        ))}
      </ul>
    </article>
  );
}
