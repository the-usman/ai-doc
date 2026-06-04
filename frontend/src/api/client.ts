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

export type OAuthProvider = "google" | "github";

/**
 * Redirect browser to OAuth login for the given provider.
 *
 * @param provider - google or github
 */
export function startLogin(provider: OAuthProvider): void {
  window.location.href = `/api/auth/login/${provider}`;
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
