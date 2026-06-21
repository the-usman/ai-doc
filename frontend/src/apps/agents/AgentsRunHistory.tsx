import { useEffect, useState } from "react";
import { fetchAgentRuns, type PipelineRun } from "../../api/client";
import { RunTrace } from "./AgentsPipeline";
import { RunStatusBadge } from "./RunStatusBadge";
import styles from "./Agents.module.css";

/**
 * Format an ISO timestamp for the run list, falling back gracefully.
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
 * Agents application — Run History page.
 *
 * Reads completed pipeline runs from `/api/agents/runs` (newest first) and lists
 * them. Each row expands to reveal the full trace — which workers ran, in what
 * order, and what each returned — reusing the Pipeline page's trace view.
 */
export function AgentsRunHistory() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    fetchAgentRuns()
      .then(setRuns)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Could not load runs."),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <article>
        <h1>Run History</h1>
        <p className={styles.muted}>Loading runs…</p>
      </article>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <h1>Run History</h1>
        <p className={styles.subtitle}>
          Completed pipeline runs, newest first. Expand a run to see the full
          trace.
        </p>
      </header>

      {error && <p className={styles.error}>{error}</p>}

      {!error && runs.length === 0 && (
        <p className={styles.muted}>
          No runs yet. Start one on the Pipeline page or wait for the scheduled
          automation to fire.
        </p>
      )}

      <ul className={styles.runList}>
        {runs.map((run) => {
          const isOpen = openId === run.id;
          return (
            <li key={run.id} className={styles.runItem}>
              <button
                type="button"
                className={styles.runSummary}
                aria-expanded={isOpen}
                onClick={() => setOpenId(isOpen ? null : run.id)}
              >
                <span
                  className={`${styles.chevron} ${isOpen ? styles.chevronOpen : ""}`}
                  aria-hidden="true"
                >
                  ▸
                </span>
                <span className={styles.runTask}>{run.task}</span>
                <RunStatusBadge status={run.status} />
                <span className={styles.runDate}>
                  {formatDate(run.started_at)}
                </span>
              </button>
              {isOpen && (
                <div className={styles.runDetail}>
                  <RunTrace run={run} />
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
