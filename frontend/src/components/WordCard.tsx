import Link from "next/link";

import { labelOr, type TFunction } from "@/i18n/translate";
import type { WordSummary } from "@/lib/types";
import { LANGUAGE_FLAGS, wordHref } from "@/lib/words";

export function WordCard({ word, t, compact = false }: { word: WordSummary; t: TFunction; compact?: boolean }) {
  return (
    <Link
      href={wordHref(word.language_code, word.slug)}
      className="card block transition hover:border-brand hover:shadow-sm"
      data-testid="word-card"
    >
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span aria-hidden>{LANGUAGE_FLAGS[word.language_code] ?? ""}</span>
        <span className={`font-semibold ${compact ? "" : "text-lg"}`}>{word.lemma}</span>
        {word.primary_translation && <span className="text-muted">— {word.primary_translation.text}</span>}
        {word.status === "ai_generated" && <span className="badge bg-warning/15 text-warning">AI</span>}
        {word.match && word.match !== "exact" && word.match !== "list" && (
          <span className="badge bg-surface text-muted">{t(`search.match.${word.match}`)}</span>
        )}
      </div>
      {!compact && (
        <>
          {word.pos.length > 0 && (
            <div className="mt-1 text-xs italic text-muted">{word.pos.map((p) => labelOr(t, "pos", p)).join(", ")}</div>
          )}
          {word.short_definition && <p className="mt-1 line-clamp-2 text-sm text-muted">{word.short_definition}</p>}
        </>
      )}
    </Link>
  );
}
