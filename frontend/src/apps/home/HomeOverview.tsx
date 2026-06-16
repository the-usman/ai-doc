import { APP_REGISTRY } from "../../platform/appRegistry";

/**
 * Home application overview dashboard.
 */
export function HomeOverview() {
  const otherApps = APP_REGISTRY.filter((a) => a.key !== "home");

  return (
    <article>
      <h1>Platform home</h1>
      <p>
        Welcome to AI-Doc. You are signed in to the platform shell. Applications
        register in a central registry — switch using the navigation above.
      </p>
      <h2>Available applications</h2>
      <ul>
        {otherApps.map((app) => (
          <li key={app.key}>
            {app.icon} <strong>{app.name}</strong> — {app.rootPath}
          </li>
        ))}
      </ul>
      <p className="muted">
        Agents and Knowledge applications arrive in Phases 3–4.
      </p>
    </article>
  );
}
