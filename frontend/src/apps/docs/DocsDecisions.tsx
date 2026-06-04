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
