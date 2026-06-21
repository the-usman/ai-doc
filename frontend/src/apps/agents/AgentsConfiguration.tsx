/**
 * Agents application — Configuration page.
 *
 * Placeholder in Phase 3. Worker types and system prompts are configured on the
 * server through environment variables and code today; an editable UI arrives in
 * a later phase. This page documents the current configuration for reference.
 */
export function AgentsConfiguration() {
  return (
    <article>
      <h1>Configuration</h1>
      <p>
        The agent pipeline is configured on the server. The supervisor and both
        workers run on Anthropic Claude via LangGraph; the model and token budget
        are set through environment variables (<code>AGENTS_MODEL</code>,{" "}
        <code>AGENTS_MAX_TOKENS</code>).
      </p>
      <dl>
        <dt>Supervisor</dt>
        <dd>
          LCEL chain with structured routing output (DataAgent / ReportAgent /
          FINISH), capped at six worker steps per run.
        </dd>
        <dt>DataAgent</dt>
        <dd>
          ReAct agent with the platform database tools (get_platform_user_count,
          get_recent_signins, get_user_provider_breakdown).
        </dd>
        <dt>ReportAgent</dt>
        <dd>Tool-free synthesis chain that summarises the gathered findings.</dd>
        <dt>Automation</dt>
        <dd>
          n8n calls <code>POST /api/agents/trigger</code> on a schedule, guarded
          by the <code>AGENTS_TRIGGER_TOKEN</code> shared secret.
        </dd>
      </dl>
      <p className="muted">An editable configuration UI arrives in a later phase.</p>
    </article>
  );
}
