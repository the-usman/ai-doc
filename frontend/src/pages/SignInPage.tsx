import { startLogin } from "../api/client";
import styles from "./SignInPage.module.css";

/**
 * Public sign-in page for unauthenticated visitors.
 */
export function SignInPage() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1>AI-Doc</h1>
        <p>Personal developer platform — sign in to continue.</p>
        <button type="button" onClick={startLogin} className={styles.button}>
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
