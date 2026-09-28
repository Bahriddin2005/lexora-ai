import { describe, expect, it } from "vitest";

import { makeT } from "./translate";

describe("makeT", () => {
  it("translates with variables and falls back to Uzbek, then to the key", () => {
    expect(makeT("en")("search.resultsFor", { q: "run" })).toBe("Results for “run”");
    expect(makeT("ru")("pos.verb")).toBe("глаг.");
    expect(makeT("uz")("missing.key")).toBe("missing.key");
  });
});
