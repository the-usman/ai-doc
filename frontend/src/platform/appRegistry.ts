/**
 * Central registry of platform applications.
 * Adding a new app requires one entry here — not scattered route files.
 */

export interface SubNavItem {
  /** Route segment relative to app rootPath */
  path: string;
  /** Label shown in sub-navigation */
  label: string;
}

export interface PlatformApp {
  /** Stable key for routing and tests */
  key: string;
  /** Display name in application switcher */
  name: string;
  /** Emoji or short icon label */
  icon: string;
  /** URL prefix for this application */
  rootPath: string;
  /** Pages within the application */
  subNav: SubNavItem[];
}

/** All applications registered on the platform shell. */
export const APP_REGISTRY: PlatformApp[] = [
  {
    key: "home",
    name: "Home",
    icon: "🏠",
    rootPath: "/",
    subNav: [
      { path: "", label: "Overview" },
      { path: "settings", label: "Settings" },
    ],
  },
  {
    key: "chat",
    name: "Chat",
    icon: "💬",
    rootPath: "/chat",
    subNav: [
      { path: "", label: "Conversation" },
      { path: "history", label: "History" },
      { path: "settings", label: "Settings" },
    ],
  },
  {
    key: "docs",
    name: "Docs",
    icon: "📚",
    rootPath: "/docs",
    subNav: [
      { path: "", label: "Architecture" },
      { path: "decisions", label: "Decisions" },
      { path: "runbook", label: "Runbook" },
      { path: "api", label: "API Reference" },
    ],
  },
];

/**
 * Resolve which app is active from the current pathname.
 *
 * @param pathname - Browser location pathname
 * @returns Matching app or the home app as default
 */
export function getActiveApp(pathname: string): PlatformApp {
  const match = APP_REGISTRY.find(
    (app) =>
      app.rootPath !== "/" &&
      (pathname === app.rootPath || pathname.startsWith(`${app.rootPath}/`)),
  );
  if (match) {
    return match;
  }
  return APP_REGISTRY[0];
}
