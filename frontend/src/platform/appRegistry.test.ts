import { describe, expect, it } from "vitest";
import { APP_REGISTRY, getActiveApp } from "./appRegistry";

describe("platform navigation registry", () => {
  it("renders the correct number of registered applications", () => {
    expect(APP_REGISTRY).toHaveLength(5);
    expect(APP_REGISTRY.map((a) => a.key)).toEqual([
      "home",
      "chat",
      "agents",
      "knowledge",
      "docs",
    ]);
  });

  it("registers the Knowledge application with its three sub-pages", () => {
    const knowledge = APP_REGISTRY.find((a) => a.key === "knowledge");
    expect(knowledge?.rootPath).toBe("/knowledge");
    expect(knowledge?.subNav.map((s) => s.label)).toEqual([
      "Documents",
      "Chat",
      "Explore",
    ]);
  });

  it("resolves the Knowledge app from a nested pathname", () => {
    expect(getActiveApp("/knowledge/chat").key).toBe("knowledge");
  });

  it("registers the Agents application with its three sub-pages", () => {
    const agents = APP_REGISTRY.find((a) => a.key === "agents");
    expect(agents?.rootPath).toBe("/agents");
    expect(agents?.subNav.map((s) => s.label)).toEqual([
      "Pipeline",
      "Run History",
      "Configuration",
    ]);
  });

  it("resolves the Agents app from a nested pathname", () => {
    expect(getActiveApp("/agents/history").key).toBe("agents");
  });
});
