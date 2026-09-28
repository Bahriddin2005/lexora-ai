import { type Inline, parseMarkdown } from "@/lib/markdown";

function Inlines({ items }: { items: Inline[] }) {
  return (
    <>
      {items.map((item, i) => {
        if (item.type === "bold") return <strong key={i}>{item.text}</strong>;
        if (item.type === "italic") return <em key={i}>{item.text}</em>;
        if (item.type === "code")
          return (
            <code key={i} className="rounded bg-surface px-1 text-[0.9em]">
              {item.text}
            </code>
          );
        return <span key={i}>{item.text}</span>;
      })}
    </>
  );
}

export function Markdown({ text }: { text: string }) {
  return (
    <div className="space-y-2 leading-relaxed">
      {parseMarkdown(text).map((block, i) => {
        if (block.type === "heading") {
          return (
            <p key={i} className="pt-1 font-semibold">
              <Inlines items={block.inlines} />
            </p>
          );
        }
        if (block.type === "list") {
          const Tag = block.ordered ? "ol" : "ul";
          return (
            <Tag key={i} className={`${block.ordered ? "list-decimal" : "list-disc"} space-y-1 ps-5`}>
              {block.items.map((item, j) => (
                <li key={j}>
                  <Inlines items={item} />
                </li>
              ))}
            </Tag>
          );
        }
        return (
          <p key={i}>
            <Inlines items={block.inlines} />
          </p>
        );
      })}
    </div>
  );
}
