import { describe, expect, it } from "vitest";

import { parseInline, parseMarkdown } from "./markdown";

describe("parseInline", () => {
  it("parses bold, italic and code", () => {
    expect(parseInline("**run** means *yugurmoq* in `uz`")).toEqual([
      { type: "bold", text: "run" },
      { type: "text", text: " means " },
      { type: "italic", text: "yugurmoq" },
      { type: "text", text: " in " },
      { type: "code", text: "uz" },
    ]);
  });

  it("keeps HTML as plain text", () => {
    expect(parseInline("<script>alert(1)</script>")).toEqual([
      { type: "text", text: "<script>alert(1)</script>" },
    ]);
  });
});

describe("parseMarkdown", () => {
  it("builds headings, paragraphs and lists", () => {
    const blocks = parseMarkdown("## Ma’nosi\nBirinchi qator\nikkinchi qator\n\n- bir\n- **ikki**\n1. uch");
    expect(blocks.map((b) => b.type)).toEqual(["heading", "paragraph", "list", "list"]);
    expect(blocks[1]).toEqual({ type: "paragraph", inlines: [{ type: "text", text: "Birinchi qator ikkinchi qator" }] });
    expect(blocks[2]).toMatchObject({ ordered: false, items: [[{ text: "bir" }], [{ type: "bold", text: "ikki" }]] });
    expect(blocks[3]).toMatchObject({ ordered: true });
  });
});
