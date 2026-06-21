import type { PipelineStatus } from "../../api/client";
import styles from "./Agents.module.css";

const STATUS_CLASS: Record<PipelineStatus, string> = {
  completed: styles.completed,
  failed: styles.failed,
  running: styles.running_badge,
};

/**
 * Small coloured pill showing a pipeline run's status.
 *
 * @param props.status - The run status (running | completed | failed)
 */
export function RunStatusBadge({ status }: { status: PipelineStatus }) {
  return (
    <span className={`${styles.badge} ${STATUS_CLASS[status] ?? ""}`}>
      {status}
    </span>
  );
}
