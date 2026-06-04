import { useEffect, useState } from "react";
import {
  fetchAuthProviders,
  startLogin,
  type OAuthProvider,
} from "../api/client";
import styles from "./SignInPage.module.css";

const PROVIDER_LABELS: Record<OAuthProvider, string> = {
  google: "Sign in with Google",
  github: "Sign in with GitHub",
};

/**
 * Public sign-in page with Google and GitHub OAuth options.
 */
export function SignInPage() {
  const [providers, setProviders] = useState<OAuthProvider[]>([
    "google",
    "github",
  ]);

  useEffect(() => {
    fetchAuthProviders().then(setProviders);
  }, []);

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1>AI-Doc</h1>
        <p>Personal developer platform — sign in to continue.</p>
        <div className={styles.buttons}>
          {providers.length === 0 ? (
            <p className={styles.hint}>No OAuth providers configured.</p>
          ) : (
            providers.map((provider) => (
              <button
                key={provider}
                type="button"
                onClick={() => startLogin(provider)}
                className={
                  provider === "github" ? styles.buttonGithub : styles.button
                }
              >
                {PROVIDER_LABELS[provider]}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
