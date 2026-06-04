import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import type { UserProfile } from "./api/client";
import { fetchCurrentUser } from "./api/client";
import { HomeOverview } from "./apps/home/HomeOverview";
import { HomeSettings } from "./apps/home/HomeSettings";
import { DocsApiReference } from "./apps/docs/DocsApiReference";
import { DocsArchitecture } from "./apps/docs/DocsArchitecture";
import { DocsDecisions } from "./apps/docs/DocsDecisions";
import { DocsRunbook } from "./apps/docs/DocsRunbook";
import { PlatformShell } from "./platform/PlatformShell";
import { SignInPage } from "./pages/SignInPage";
import "./App.css";

/**
 * Root application with auth gate and platform routes.
 */
export default function App() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="loading">Loading…</div>;
  }

  return (
    <Routes>
      <Route
        path="/sign-in"
        element={user ? <Navigate to="/" replace /> : <SignInPage />}
      />
      <Route
        path="/*"
        element={
          user ? (
            <PlatformShell user={user} />
          ) : (
            <Navigate to="/sign-in" replace />
          )
        }
      >
        <Route index element={<HomeOverview />} />
        <Route path="settings" element={<HomeSettings user={user!} />} />
        <Route path="docs" element={<DocsArchitecture />} />
        <Route path="docs/decisions" element={<DocsDecisions />} />
        <Route path="docs/runbook" element={<DocsRunbook />} />
        <Route path="docs/api" element={<DocsApiReference />} />
      </Route>
    </Routes>
  );
}
