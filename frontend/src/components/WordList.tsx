import { getT } from "@/i18n/server";
import type { WordSummary } from "@/lib/types";

import { WordCard } from "./WordCard";

export async function WordList({ title, words }: { title: string; words: WordSummary[] }) {
  const { t } = await getT();
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">{title}</h1>
      {words.length === 0 ? (
        <p className="text-muted">{t("lists.empty")}</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {words.map((word) => (
            <WordCard key={word.id} word={word} t={t} />
          ))}
        </div>
      )}
    </div>
  );
}
