/**
 * Docs — Operational runbook for local run and deploy.
 */
export function DocsRunbook() {
  return (
    <article>
      <h1>Runbook</h1>
      <h2>Run locally</h2>
      <ol>
        <li>Copy <code>.env.example</code> to <code>.env</code> and fill values.</li>
        <li>
          From project root:{" "}
          <code>docker compose up --build</code>
        </li>
        <li>
          Open <code>http://localhost:3000</code> and sign in with Google OAuth.
        </li>
      </ol>
      <h2>Tests</h2>
      <pre>
        <code>docker compose run --rm api pytest</code>
        {"\n"}
        <code>docker compose run --rm web npm test</code>
      </pre>
      <h2>Deploy (Dokploy)</h2>
      <p>
        Point the application at <code>docker/docker-compose.prod.yml</code>.
        Set secrets in the Dokploy panel — never commit production credentials.
      </p>
      <h2>Common problems</h2>
      <ul>
        <li>
          <strong>DB connection fails in Docker</strong> — Use service name{" "}
          <code>db</code> as <code>DB_HOST</code>, not localhost.
        </li>
        <li>
          <strong>redirect_uri_mismatch</strong> — Register exact callback URLs
          in Google Cloud Console for local and production.
        </li>
        <li>
          <strong>Port conflict</strong> — Change host ports in compose if 3000
          or 5432 are taken.
        </li>
      </ul>
    </article>
  );
}
