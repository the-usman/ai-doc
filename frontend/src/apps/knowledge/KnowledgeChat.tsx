import { useEffect, useRef, useState } from "react";
import { askKnowledge, type SourceChunk } from "../../api/client";
import styles from "./Knowledge.module.css";

interface KnowledgeMessage {
  role: "user" | "assistant";
  text: string;
  sources?: SourceChunk[];
}

/**
 * Knowledge application — Chat page.
 *
 * A retrieval-augmented chat: each question is answered from the uploaded
 * documents, and the source chunks that grounded the answer are shown beneath it
 * so the retrieval step is transparent to the user.
 */
export function KnowledgeChat() {
  const [messages, setMessages] = useState<KnowledgeMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || pending) {
      return;
    }
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setPending(true);
    try {
      const reply = await askKnowledge(text);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: reply.answer, sources: reply.sources },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className={styles.chat}>
      <header className={styles.head}>
        <h1>Knowledge Chat</h1>
        <p className={styles.subtitle}>
          Ask questions about your uploaded documents. Answers are grounded in
          retrieved passages, shown beneath each reply.
        </p>
      </header>

      <div className={styles.thread}>
        {messages.length === 0 && (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>📖</span>
            <p>Ask a question about your documents.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={
              message.role === "user" ? styles.userRow : styles.assistantRow
            }
          >
            <div
              className={
                message.role === "user"
                  ? styles.userBubble
                  : styles.assistantBubble
              }
            >
              <p className={styles.text}>{message.text}</p>
              {message.role === "assistant" &&
                message.sources &&
                message.sources.length > 0 && (
                  <div className={styles.sources}>
                    <p className={styles.sourcesLabel}>Sources</p>
                    {message.sources.map((source, sourceIndex) => (
                      <details key={sourceIndex} className={styles.source}>
                        <summary className={styles.sourceSummary}>
                          <span className={styles.sourceTitle}>
                            📄 {source.document_title}
                          </span>
                          <span className={styles.sourceScore}>
                            {(source.similarity * 100).toFixed(0)}% match
                          </span>
                        </summary>
                        <p className={styles.sourceSnippet}>{source.snippet}</p>
                      </details>
                    ))}
                  </div>
                )}
            </div>
          </div>
        ))}
        {pending && (
          <div className={styles.assistantRow}>
            <div className={styles.assistantBubble}>
              <span className={styles.typing}>
                <i></i>
                <i></i>
                <i></i>
              </span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <form className={styles.composer} onSubmit={handleSubmit}>
        <input
          className={styles.field}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about your documents…"
          aria-label="Question"
          disabled={pending}
        />
        <button
          type="submit"
          className={styles.primary}
          disabled={pending || input.trim().length === 0}
        >
          Ask
        </button>
      </form>
    </div>
  );
}
