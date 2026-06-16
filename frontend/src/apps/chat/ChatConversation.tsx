import { useEffect, useRef, useState } from "react";
import { sendChatMessage, type ChatConfidence } from "../../api/client";
import styles from "./ChatConversation.module.css";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  confidence?: ChatConfidence;
  sources?: string[];
}

/**
 * Chat application — the conversation interface for the LangChain assistant.
 *
 * Sends messages to the session-backed `/api/chat/message` endpoint and renders
 * the structured response, including the assistant's confidence and any tools
 * it called.
 */
export function ChatConversation() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
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
      const reply = await sendChatMessage(text);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: reply.response,
          confidence: reply.confidence,
          sources: reply.sources,
        },
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
        <h1>Conversation</h1>
        <p className={styles.subtitle}>
          Ask about the platform — try “How many users are registered?”
        </p>
      </header>

      <div className={styles.thread}>
        {messages.length === 0 && (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>💬</span>
            <p>Start the conversation below.</p>
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
                message.role === "user" ? styles.userBubble : styles.assistantBubble
              }
            >
              <p className={styles.text}>{message.text}</p>
              {message.role === "assistant" && (
                <div className={styles.meta}>
                  {message.confidence && (
                    <span className={`${styles.tag} ${styles[message.confidence]}`}>
                      {message.confidence} confidence
                    </span>
                  )}
                  {message.sources?.map((source) => (
                    <span key={source} className={styles.source}>
                      🛠 {source}
                    </span>
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
          placeholder="Message the assistant…"
          aria-label="Message"
          disabled={pending}
        />
        <button
          type="submit"
          className={styles.send}
          disabled={pending || input.trim().length === 0}
        >
          Send
        </button>
      </form>
    </div>
  );
}
