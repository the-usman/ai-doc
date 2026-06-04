import { Link, Outlet, useLocation } from "react-router-dom";
import type { UserProfile } from "../api/client";
import { APP_REGISTRY, getActiveApp } from "./appRegistry";
import styles from "./PlatformShell.module.css";

interface PlatformShellProps {
  user: UserProfile;
}

/**
 * Authenticated platform chrome: app switcher and per-app sub-navigation.
 *
 * @param props.user - Signed-in user shown in the header
 */
export function PlatformShell({ user }: PlatformShellProps) {
  const location = useLocation();
  const activeApp = getActiveApp(location.pathname);

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.brand}>AI-Doc</div>
        <nav className={styles.appSwitcher} aria-label="Applications">
          {APP_REGISTRY.map((app) => {
            const isActive = app.key === activeApp.key;
            return (
              <Link
                key={app.key}
                to={app.rootPath === "/" ? "/" : app.rootPath}
                className={isActive ? styles.appActive : styles.appLink}
                aria-current={isActive ? "page" : undefined}
              >
                <span className={styles.appIcon}>{app.icon}</span>
                {app.name}
              </Link>
            );
          })}
        </nav>
        <div className={styles.user}>
          {user.avatar_url && (
            <img src={user.avatar_url} alt="" className={styles.avatar} />
          )}
          <span>{user.name ?? user.email}</span>
        </div>
      </header>

      <div className={styles.body}>
        <aside className={styles.subNav} aria-label={`${activeApp.name} navigation`}>
          <p className={styles.subNavTitle}>{activeApp.name}</p>
          <ul>
            {activeApp.subNav.map((item) => {
              const href =
                activeApp.rootPath === "/"
                  ? item.path
                    ? `/${item.path}`
                    : "/"
                  : `${activeApp.rootPath}${item.path ? `/${item.path}` : ""}`;
              const isSubActive = location.pathname === href || location.pathname === `${href}/`;
              return (
                <li key={item.path || "index"}>
                  <Link
                    to={href}
                    className={isSubActive ? styles.subActive : undefined}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </aside>
        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
