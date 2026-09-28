import { describe, expect, it } from "vitest";

import { SseParser } from "./sse";

describe("SseParser", () => {
  it("handles events split across chunks", () => {
    const parser = new SseParser();
    expect(parser.push('data: {"delta": "sa')).toEqual([]);
    expect(parser.push('lom"}\n\ndata: {"delta": " dunyo"}\n\n')).toEqual([{ delta: "salom" }, { delta: " dunyo" }]);
    expect(parser.push('data: {"done": true, "cached": false}\n\n')).toEqual([{ done: true, cached: false }]);
  });

  it("ignores malformed data", () => {
    expect(new SseParser().push("data: not-json\n\n: comment\n\n")).toEqual([]);
  });
});
