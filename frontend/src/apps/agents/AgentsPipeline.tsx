import { useState } from "react";
import {
  runAgentPipeline,
  type PipelineRun,
  type WorkerResult,
} from "../../api/client";
import { RunStatusBadge } from "./RunStatusBadge";
import styles from "./Agents.module.css";

const EXAMPLE_TASKS = [
  "How many users are registered, and how do they split across providers?",
  "Summarise recent sign-in activity on the platform.",
  "Report the user count and the most recent sign-ins.",
];

const WORKER_ICONS: Record<string, string> = {
  DataAgent: "🔎",
  ReportAgent: "📝",
};

/**
 * Agents application — Pipeline page.
 *
 * Submits a task to the LangGraph supervisor/worker pipeline and renders the
 * completed run: each worker step in the order the supervisor invoked it (the
 * intermediate state of the graph), followed by the synthesised final output.
 */
export function AgentsPipeline() {
  const [task, setTask] = useState("");
  const [pending, setPending] = useState(false);
  const [run, setRun] = useState<PipelineRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function start(taskText: string) {
    const trimmed = taskText.trim();
    if (!trimmed || pending) {
      return;
    }
    setError(null);
    setRun(null);
    setPending(true);
    try {
      const result = await runAgentPipeline(trimmed);
      setRun(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    void start(task);
  }

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <h1>Pipeline</h1>
        <p className={styles.subtitle}>
          A supervisor routes your task to specialised agents — DataAgent gathers
          platform data, ReportAgent writes the summary — then returns the result.
        </p>
      </header>

      <form className={styles.composer} onSubmit={handleSubmit}>
        <input
          className={styles.field}
          value={task}
          onChange={(event) => setTask(event.target.value)}
          placeholder="Describe a task for the agent pipeline…"
          aria-label="Task"
          disabled={pending}
        />
        <button
          type="submit"
          className={styles.run}
          disabled={pending || task.trim().length === 0}
        >
          {pending ? "Running…" : "Run pipeline"}
        </button>
      </form>

      <div className={styles.examples}>
        {EXAMPLE_TASKS.map((example) => (
          <button
            key={example}
            type="button"
            className={styles.example}
            disabled={pending}
            onClick={() => {
              setTask(example);
              void start(example);
            }}
          >
            {example}
          </button>
        ))}
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {pending && (
        <div className={styles.panel}>
          <div className={styles.panelHead}>
            <p className={styles.panelTask}>Running pipeline…</p>
          </div>
          <p className={styles.muted}>
            <span className={styles.running}>
              <i></i>
              <i></i>
              <i></i>
            </span>{" "}
            The supervisor is delegating to its workers.
          </p>
        </div>
      )}

      {run && !pending && <RunTrace run={run} />}
    </div>
  );
}

/**
 * Render a completed run: its task, status, per-worker timeline, and final output.
 *
 * @param props.run - The completed pipeline run to display
 */
export function RunTrace({ run }: { run: PipelineRun }) {
  return (
    <div className={styles.panel}>
      <div className={styles.panelHead}>
        <p className={styles.panelTask}>{run.task}</p>
        <RunStatusBadge status={run.status} />
      </div>

      <ol className={styles.timeline}>
        {run.trace.length === 0 && (
          <li className={styles.muted}>No worker steps were recorded.</li>
        )}
        {run.trace.map((step: WorkerResult, index: number) => (
          <li key={index} className={styles.step}>
            <span className={styles.stepIcon} aria-hidden="true">
              {WORKER_ICONS[step.worker] ?? "⚙️"}
            </span>
            <div className={styles.stepBody}>
              <p className={styles.stepWorker}>{step.worker}</p>
              <p className={styles.stepOutput}>{step.output}</p>
            </div>
          </li>
        ))}
      </ol>

      {run.final_output && (
        <div className={styles.final}>
          <p className={styles.finalLabel}>Final output</p>
          <p className={styles.finalText}>{run.final_output}</p>
        </div>
      )}
    </div>
  );
}
