import { Link } from "react-router-dom";
import { APP_REGISTRY } from "../../platform/appRegistry";
import styles from "./Home.module.css";

/** Short, plain-language description of each platform application. */
const APP_DESCRIPTIONS: Record<string, string> = {
  chat: "Chat with an AI assistant that can query real platform data through tools.",
  agents: "Run a LangGraph supervisor/worker pipeline and review its full trace.",
  knowledge: "Upload documents and ask questions answered from their contents (RAG).",
  docs: "Architecture, decision records, runbook, and the in-app API reference.",
};

/**
 * Home application overview dashboard.
 *
 * Renders a hero header, a grid of cards linking to every other registered
 * application, and a short platform status strip.
 */
export function HomeOverview() {
  const otherApps = APP_REGISTRY.filter((app) => app.key !== "home");

  return (
    <article>
      <header className={styles.hero}>
        <span className={styles.eyebrow}>Platform online</span>
        <h1 className={styles.heroTitle}>Welcome to AI-Doc</h1>
        <p className={styles.heroSubtitle}>
          One sign-on, many applications. Each app registers in a central
          registry and shares this shell, your identity, and one database.
          Pick an application below to get started.
        </p>
      </header>

      <h2 className={styles.sectionTitle}>Applications</h2>
      <div className={styles.grid}>
        {otherApps.map((app) => (
          <Link key={app.key} to={app.rootPath} className={styles.card}>
            <span className={styles.cardIcon} aria-hidden="true">
              {app.icon}
            </span>
            <h3 className={styles.cardName}>{app.name}</h3>
            <p className={styles.cardDesc}>
              {APP_DESCRIPTIONS[app.key] ?? `Open the ${app.name} application.`}
            </p>
            <div className={styles.cardFooter}>
              <span className={styles.cardPath}>{app.rootPath}</span>
              <span className={styles.cardArrow} aria-hidden="true">
                →
              </span>
            </div>
          </Link>
        ))}
      </div>

      <h2 className={styles.sectionTitle}>At a glance</h2>
      <div className={styles.statusStrip}>
        <div className={styles.statusItem}>
          <span className={styles.statusValue}>{APP_REGISTRY.length}</span>
          <span className={styles.statusLabel}>Registered apps</span>
        </div>
        <div className={styles.statusItem}>
          <span className={styles.statusValue}>SSO</span>
          <span className={styles.statusLabel}>Google &amp; GitHub</span>
        </div>
        <div className={styles.statusItem}>
          <span className={styles.statusValue}>Live</span>
          <span className={styles.statusLabel}>Session active</span>
        </div>
      </div>
    </article>
  );
}
