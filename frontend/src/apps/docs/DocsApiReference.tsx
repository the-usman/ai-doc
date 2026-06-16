/**
 * Docs — API reference for platform and Phase 2 chat endpoints.
 */
export function DocsApiReference() {
  return (
    <article>
      <h1>API Reference</h1>
      <h2>Platform &amp; auth</h2>
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
            <td>/api/auth/providers</td>
            <td>Enabled OAuth providers (google, github)</td>
          </tr>
          <tr>
            <td>GET</td>
            <td>/api/auth/login/google</td>
            <td>Start Google OAuth</td>
          </tr>
          <tr>
            <td>GET</td>
            <td>/api/auth/login/github</td>
            <td>Start GitHub OAuth</td>
          </tr>
          <tr>
            <td>GET</td>
            <td>/api/me</td>
            <td>Current user (session cookie)</td>
          </tr>
          <tr>
            <td>POST</td>
            <td>/api/auth/logout</td>
            <td>Clear the session cookie</td>
          </tr>
        </tbody>
      </table>

      <h2>Chat (LangChain + LangServe)</h2>
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
            <td>POST</td>
            <td>/api/chat/message</td>
            <td>
              Authenticated turn; returns structured{" "}
              <code>{`{ response, confidence, sources }`}</code>
            </td>
          </tr>
          <tr>
            <td>POST</td>
            <td>/api/chat/invoke</td>
            <td>LangServe — run the chat chain</td>
          </tr>
          <tr>
            <td>POST</td>
            <td>/api/chat/stream</td>
            <td>LangServe — streaming responses</td>
          </tr>
          <tr>
            <td>GET</td>
            <td>/api/chat/playground</td>
            <td>LangServe interactive playground</td>
          </tr>
        </tbody>
      </table>

      <h2>MCP server</h2>
      <p>
        Runs as a separate service (default port 8001) and exposes the same
        tools over the Model Context Protocol.
      </p>
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
            <td>/mcp/tools</td>
            <td>Tool manifest (names + JSON-Schema inputs)</td>
          </tr>
          <tr>
            <td>POST</td>
            <td>/mcp/call</td>
            <td>Execute a tool by name and return its result</td>
          </tr>
        </tbody>
      </table>
    </article>
  );
}
