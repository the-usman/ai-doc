/**
 * Chat application — Settings page.
 *
 * Placeholder in Phase 2. Model selection and a configurable system prompt are
 * server-side settings today; an editable UI arrives in a later phase.
 */
export function ChatSettings() {
  return (
    <article>
      <h1>Settings</h1>
      <p>
        The assistant runs on Anthropic Claude via LangChain. The model and
        system prompt are configured on the server through environment variables
        (<code>CHAT_MODEL</code>, <code>CHAT_MAX_TOKENS</code>).
      </p>
      <dl>
        <dt>Default model</dt>
        <dd>claude-opus-4-8</dd>
        <dt>Memory</dt>
        <dd>Sliding window, 10 turns, keyed by session</dd>
        <dt>Tools</dt>
        <dd>get_platform_user_count, get_recent_signins</dd>
      </dl>
      <p className="muted">An editable settings UI arrives in a later phase.</p>
    </article>
  );
}
