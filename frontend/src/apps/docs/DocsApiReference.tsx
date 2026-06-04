/**
 * Docs — API reference placeholder until Phase 2 routes exist.
 */
export function DocsApiReference() {
  return (
    <article>
      <h1>API Reference</h1>
      <p>Placeholder for Phase 1. Endpoints available today:</p>
      <table>
        <thead>
          <tr>
            <th>Method</th>
            <th>Path</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>GET</td>
            <td>/health</td>
            <td>Liveness probe</td>
          </tr>
          <tr>
            <td>GET</td>
            <td>/api/auth/login</td>
            <td>Start OAuth flow</td>
          </tr>
          <tr>
            <td>GET</td>
            <td>/api/me</td>
            <td>Current user (session cookie)</td>
          </tr>
        </tbody>
      </table>
      <p>LangChain and LangServe routes will be documented in Phase 2.</p>
    </article>
  );
}
