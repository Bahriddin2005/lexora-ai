import { describe, expect, it } from "vitest";

import { frequencyDots, groupByPos, orderedDefinitions, searchHref, wordHref } from "./words";

describe("word helpers", () => {
  it("builds URLs", () => {
    expect(wordHref("uz", "o'g'il")).toBe("/w/uz/o'g'il");
    expect(wordHref("en", "vibe coding")).toBe("/w/en/vibe%20coding");
    expect(searchHref("run", { from: "en", to: null })).toBe("/search?q=run&from=en");
  });

  it("orders definitions by UI language", () => {
    const defs = { en: "to move", ru: "бежать", uz: "yugurmoq" };
    expect(orderedDefinitions(defs, "uz", "en").map((d) => d.lang)).toEqual(["uz", "en", "ru"]);
    expect(orderedDefinitions(defs, "ru", "en").map((d) => d.lang)).toEqual(["ru", "uz", "en"]);
  });

  it("maps frequency and groups senses", () => {
    expect(frequencyDots(null)).toBe(0);
    expect(frequencyDots(6.2)).toBe(5);
    expect(frequencyDots(3.0)).toBe(2);
    expect(groupByPos([{ pos: "verb" }, { pos: "noun" }, { pos: "verb" }]).map(([p, s]) => [p, s.length])).toEqual([
      ["verb", 2],
      ["noun", 1],
    ]);
  });
});
