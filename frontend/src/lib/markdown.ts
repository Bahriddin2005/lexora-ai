// A tiny, safe Markdown subset for AI explanations (no HTML is ever injected).

export type Inline = { type: "text" | "bold" | "italic" | "code"; text: string };
export type Block =
  | { type: "heading"; level: 1 | 2 | 3; inlines: Inline[] }
  | { type: "paragraph"; inlines: Inline[] }
  | { type: "list"; ordered: boolean; items: Inline[][] };

const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*|_[^_\s][^_]*_)/g;

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  let last = 0;
  for (const match of text.matchAll(INLINE)) {
    const token = match[0];
    const index = match.index ?? 0;
    if (index > last) out.push({ type: "text", text: text.slice(last, index) });
    if (token.startsWith("**")) out.push({ type: "bold", text: token.slice(2, -2) });
    else if (token.startsWith("`")) out.push({ type: "code", text: token.slice(1, -1) });
    else out.push({ type: "italic", text: token.slice(1, -1) });
    last = index + token.length;
  }
  if (last < text.length) out.push({ type: "text", text: text.slice(last) });
  return out;
}

export function parseMarkdown(source: string): Block[] {
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let list: { ordered: boolean; items: Inline[][] } | null = null;

  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: "paragraph", inlines: parseInline(paragraph.join(" ")) });
    paragraph = [];
  };
  const flushList = () => {
    if (list) blocks.push({ type: "list", ...list });
    list = null;
  };

  for (const raw of source.split("\n")) {
    const line = raw.trim();
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    const bullet = /^[-*•]\s+(.*)$/.exec(line);
    const numbered = /^\d+[.)]\s+(.*)$/.exec(line);
    if (!line) {
      flushParagraph();
      flushList();
    } else if (heading) {
      flushParagraph();
      flushList();
      blocks.push({ type: "heading", level: heading[1].length as 1 | 2 | 3, inlines: parseInline(heading[2]) });
    } else if (bullet || numbered) {
      flushParagraph();
      const ordered = Boolean(numbered);
      if (list && list.ordered !== ordered) flushList();
      list ??= { ordered, items: [] };
      list.items.push(parseInline((bullet ?? numbered)![1]));
    } else {
      flushList();
      paragraph.push(line);
    }
  }
  flushParagraph();
  flushList();
  return blocks;
}
