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
 * Redirect browser to OAuth login endpoint.
 */
export function startLogin(): void {
  window.location.href = "/api/auth/login";
}
