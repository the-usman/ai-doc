/**
 * API helpers for session-backed requests.
 */

export interface UserProfile {
  email: string;
  name: string | null;
  provider: string;
  avatar_url: string | null;
}

/**
 * Fetch the current user session from the API.
 *
 * @returns User profile when authenticated
 * @throws Error when response is not OK
 */
export async function fetchCurrentUser(): Promise<UserProfile> {
  const response = await fetch("/api/me", { credentials: "include" });
  if (!response.ok) {
    throw new Error("Not authenticated");
  }
  return response.json() as Promise<UserProfile>;
}

/**
 * End the current session, clearing the session cookie server-side.
 */
export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}

export type OAuthProvider = "google" | "github";

/**
 * Redirect browser to OAuth login for the given provider.
 *
 * @param provider - google or github
 */
export function startLogin(provider: OAuthProvider): void {
  window.location.href = `/api/auth/login/${provider}`;
}

export type ChatConfidence = "low" | "medium" | "high";

export interface ChatResponse {
  response: string;
  confidence: ChatConfidence;
  sources: string[];
}

/**
 * Send a chat message to the LangChain assistant in the current session.
 *
 * @param message - The user's message
 * @returns The structured assistant response
 * @throws Error with the server detail when the request is not OK
 */
export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await fetch("/api/chat/message", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    let detail = "The assistant is unavailable right now.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return response.json() as Promise<ChatResponse>;
}

export type PipelineStatus = "running" | "completed" | "failed";

export interface WorkerResult {
  worker: string;
  output: string;
}

export interface PipelineRun {
  id: string;
  user_id: string;
  task: string;
  status: PipelineStatus;
  final_output: string | null;
  trace: WorkerResult[];
  started_at: string | null;
  completed_at: string | null;
}

/**
 * Start an agent pipeline run for the signed-in user and return the completed run.
 *
 * @param task - The task description for the supervisor/worker pipeline
 * @returns The persisted run, including its final output and worker trace
 * @throws Error with the server detail when the request is not OK
 */
export async function runAgentPipeline(task: string): Promise<PipelineRun> {
  const response = await fetch("/api/agents/run", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  });
  if (!response.ok) {
    let detail = "The agent pipeline is unavailable right now.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return response.json() as Promise<PipelineRun>;
}

/**
 * Fetch recent agent pipeline runs for the Run History page, newest first.
 *
 * @returns The list of recent runs
 * @throws Error when the response is not OK
 */
export async function fetchAgentRuns(): Promise<PipelineRun[]> {
  const response = await fetch("/api/agents/runs", { credentials: "include" });
  if (!response.ok) {
    throw new Error("Could not load run history.");
  }
  const data = (await response.json()) as { runs: PipelineRun[] };
  return data.runs;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  source_name: string;
  chunk_count: number;
  created_at: string | null;
}

export interface SourceChunk {
  document_id: string;
  document_title: string;
  chunk_index: number;
  similarity: number;
  snippet: string;
}

export interface KnowledgeAnswer {
  answer: string;
  answer_found: boolean;
  sources: SourceChunk[];
}

export interface SearchResult {
  document_id: string;
  document_title: string;
  chunk_index: number;
  similarity: number;
  text: string;
}

/**
 * Fetch the signed-in user's uploaded knowledge documents, newest first.
 *
 * @returns The list of documents
 * @throws Error when the response is not OK
 */
export async function fetchDocuments(): Promise<KnowledgeDocument[]> {
  const response = await fetch("/api/knowledge/documents", {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Could not load documents.");
  }
  const data = (await response.json()) as { documents: KnowledgeDocument[] };
  return data.documents;
}

/**
 * Upload a document for ingestion (extract, chunk, embed, index).
 *
 * @param file - The file to upload (.txt, .md or .pdf)
 * @param title - Human-readable title for the document
 * @returns The created document summary
 * @throws Error with the server detail when the request is not OK
 */
export async function uploadDocument(
  file: File,
  title: string,
): Promise<KnowledgeDocument> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  const response = await fetch("/api/knowledge/documents", {
    method: "POST",
    credentials: "include",
    body: form,
  });
  if (!response.ok) {
    let detail = "Upload failed.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return response.json() as Promise<KnowledgeDocument>;
}

/**
 * Delete one of the caller's documents and its indexed chunks.
 *
 * @param documentId - The document id to delete
 * @throws Error when the response is not OK
 */
export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`/api/knowledge/documents/${documentId}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Could not delete the document.");
  }
}

/**
 * Ask a question over the knowledge base; returns a grounded answer and sources.
 *
 * @param question - The user's question
 * @returns The answer plus the source chunks used to ground it
 * @throws Error with the server detail when the request is not OK
 */
export async function askKnowledge(question: string): Promise<KnowledgeAnswer> {
  const response = await fetch("/api/knowledge/chat", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    let detail = "The knowledge assistant is unavailable right now.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return response.json() as Promise<KnowledgeAnswer>;
}

/**
 * Run a raw retrieval against the knowledge base (Explore page).
 *
 * @param query - The search query
 * @returns The matching chunks with similarity scores
 * @throws Error with the server detail when the request is not OK
 */
export async function searchKnowledge(query: string): Promise<SearchResult[]> {
  const response = await fetch("/api/knowledge/search", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) {
    let detail = "Search is unavailable right now.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  const data = (await response.json()) as { results: SearchResult[] };
  return data.results;
}

/**
 * Load which OAuth providers are configured on the server.
 *
 * @returns List of provider keys (e.g. google, github)
 */
export async function fetchAuthProviders(): Promise<OAuthProvider[]> {
  const response = await fetch("/api/auth/providers");
  if (!response.ok) {
    return ["google", "github"];
  }
  const data = (await response.json()) as { providers: string[] };
  return data.providers.filter(
    (p): p is OAuthProvider => p === "google" || p === "github",
  );
}
