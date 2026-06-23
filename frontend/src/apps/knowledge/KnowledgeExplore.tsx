import { useState } from "react";
import { searchKnowledge, type SearchResult } from "../../api/client";
import styles from "./Knowledge.module.css";

/**
 * Knowledge application — Explore page.
 *
 * A direct semantic-search interface over the knowledge base: it runs the
 * retrieval step without the conversational wrapper, so the user can inspect
 * which chunks match a query and how strongly. (Phase 4 deliberately keeps this
 * page lightweight; the Documents and Chat pages are the functional core.)
 */
export function KnowledgeExplore() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const text = query.trim();
    if (!text || pending) {
      return;
    }
    setError(null);
    setPending(true);
    try {
      setResults(await searchKnowledge(text));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
      setResults(null);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <h1>Explore</h1>
        <p className={styles.subtitle}>
          Search the knowledge base directly. Returns the most semantically
          similar chunks, with their match scores — no conversational framing.
        </p>
      </header>

      <form className={styles.uploader} onSubmit={handleSubmit}>
        <input
          className={styles.field}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search your documents…"
          aria-label="Search query"
          disabled={pending}
        />
        <button
          type="submit"
          className={styles.primary}
          disabled={pending || query.trim().length === 0}
        >
          {pending ? "Searching…" : "Search"}
        </button>
      </form>

      {error && <p className={styles.error}>{error}</p>}

      {results !== null && results.length === 0 && (
        <p className={styles.muted}>No matching chunks found.</p>
      )}

      {results && results.length > 0 && (
        <ul className={styles.resultList}>
          {results.map((result, index) => (
            <li key={index} className={styles.resultItem}>
              <div className={styles.resultHead}>
                <span className={styles.sourceTitle}>
                  📄 {result.document_title}
                </span>
                <span className={styles.sourceScore}>
                  {(result.similarity * 100).toFixed(0)}% match
                </span>
              </div>
              <p className={styles.resultText}>{result.text}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
