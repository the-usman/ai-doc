import { useEffect, useRef, useState } from "react";
import {
  deleteDocument,
  fetchDocuments,
  uploadDocument,
  type KnowledgeDocument,
} from "../../api/client";
import styles from "./Knowledge.module.css";

/**
 * Format an ISO timestamp for the document list, falling back gracefully.
 *
 * @param iso - ISO 8601 timestamp string or null
 * @returns A short human-readable date, or an em dash when absent
 */
function formatDate(iso: string | null): string {
  if (!iso) {
    return "—";
  }
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

/**
 * Knowledge application — Documents page.
 *
 * Uploads a file (.txt/.md/.pdf) with a title to `/api/knowledge/documents`,
 * which extracts, chunks, embeds and indexes it, then lists the user's documents
 * with their chunk counts and a delete control.
 */
export function KnowledgeDocuments() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function load() {
    fetchDocuments()
      .then(setDocuments)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Could not load documents."),
      )
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!file || uploading) {
      return;
    }
    setError(null);
    setUploading(true);
    try {
      await uploadDocument(file, title.trim() || file.name);
      setTitle("");
      setFile(null);
      if (fileRef.current) {
        fileRef.current.value = "";
      }
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete.");
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <h1>Documents</h1>
        <p className={styles.subtitle}>
          Upload PDFs or text files. Each document is split into chunks, embedded,
          and indexed for retrieval-augmented answers on the Chat page.
        </p>
      </header>

      <form className={styles.uploader} onSubmit={handleUpload}>
        <input
          className={styles.field}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Document title"
          aria-label="Document title"
          disabled={uploading}
        />
        <input
          ref={fileRef}
          className={styles.fileField}
          type="file"
          accept=".txt,.md,.text,.pdf"
          aria-label="File"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          disabled={uploading}
        />
        <button
          type="submit"
          className={styles.primary}
          disabled={uploading || !file}
        >
          {uploading ? "Indexing…" : "Upload"}
        </button>
      </form>

      {error && <p className={styles.error}>{error}</p>}

      {loading ? (
        <p className={styles.muted}>Loading documents…</p>
      ) : documents.length === 0 ? (
        <p className={styles.muted}>
          No documents yet. Upload one above to start building the knowledge base.
        </p>
      ) : (
        <ul className={styles.docList}>
          {documents.map((doc) => (
            <li key={doc.id} className={styles.docItem}>
              <span className={styles.docIcon} aria-hidden="true">
                📄
              </span>
              <div className={styles.docBody}>
                <p className={styles.docTitle}>{doc.title}</p>
                <p className={styles.docMeta}>
                  {doc.source_name} · {doc.chunk_count} chunk
                  {doc.chunk_count === 1 ? "" : "s"} · {formatDate(doc.created_at)}
                </p>
              </div>
              <button
                type="button"
                className={styles.delete}
                onClick={() => handleDelete(doc.id)}
                aria-label={`Delete ${doc.title}`}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
