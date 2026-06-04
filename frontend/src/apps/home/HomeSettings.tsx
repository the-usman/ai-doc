import type { UserProfile } from "../../api/client";

interface HomeSettingsProps {
  user: UserProfile;
}

/**
 * Home application settings placeholder.
 *
 * @param props.user - Current authenticated user
 */
export function HomeSettings({ user }: HomeSettingsProps) {
  return (
    <article>
      <h1>Settings</h1>
      <p>Account connected via {user.provider}.</p>
      <dl>
        <dt>Email</dt>
        <dd>{user.email}</dd>
        <dt>Display name</dt>
        <dd>{user.name ?? "—"}</dd>
      </dl>
    </article>
  );
}
