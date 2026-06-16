import { describe, expect, it } from "vitest";
import { APP_REGISTRY } from "./appRegistry";

describe("platform navigation registry", () => {
  it("renders the correct number of registered applications", () => {
    expect(APP_REGISTRY).toHaveLength(3);
    expect(APP_REGISTRY.map((a) => a.key)).toEqual(["home", "chat", "docs"]);
  });
});
