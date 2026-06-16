/**
 * Chat application — History page.
 *
 * Placeholder in Phase 2. Conversation persistence and a browsable session log
 * arrive in Phase 3 when runs are recorded in the database.
 */
export function ChatHistory() {
  return (
    <article>
      <h1>History</h1>
      <p>
        Conversation history will be listed here. In Phase 2 the chat keeps a
        ten-turn sliding window in memory, keyed by your session — it is not yet
        persisted across sign-ins.
      </p>
      <p className="muted">Durable history lands in Phase 3.</p>
    </article>
  );
}
