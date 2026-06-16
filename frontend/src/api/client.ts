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
