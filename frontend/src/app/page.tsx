import Link from "next/link";

import { Logo } from "@/components/layout/Header";
import { SearchBox } from "@/components/SearchBox";
import { WordCard } from "@/components/WordCard";
import { getT } from "@/i18n/server";
import type { TFunction } from "@/i18n/translate";
import { apiServer } from "@/lib/server-api";
import type { Language, WordSummary } from "@/lib/types";

async function safe<T>(promise: Promise<T>, fallback: T): Promise<T> {
  try {
    return await promise;
  } catch {
    return fallback;
  }
}

function Column({ title, href, words, t }: { title: string; href: string; words: WordSummary[]; t: TFunction }) {
  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="font-semibold">{title}</h2>
        <Link href={href} className="text-sm link">
          {t("home.seeAll")}
        </Link>
      </div>
      {words.length === 0 ? (
        <p className="text-sm text-muted">{t("home.empty")}</p>
      ) : (
        <div className="space-y-2">
          {words.map((word) => (
            <WordCard key={word.id} word={word} t={t} compact />
          ))}
        </div>
      )}
    </section>
  );
}

export default async function HomePage() {
  const { t } = await getT();
  const [languages, trending, aiTerms, newWords] = await Promise.all([
    safe(apiServer<Language[]>("/languages"), []),
    safe(apiServer<WordSummary[]>("/trending?limit=5"), []),
    safe(apiServer<WordSummary[]>("/ai-terms?limit=5"), []),
    safe(apiServer<WordSummary[]>("/new-words?limit=5"), []),
  ]);

  return (
    <div className="mx-auto max-w-6xl px-4">
      <section className="flex flex-col items-center pb-12 pt-16 text-center sm:pt-24">
        <h1>
          <Logo large />
        </h1>
        <p className="mt-3 text-lg text-muted">{t("common.tagline")}</p>
        <div className="mt-8 flex w-full justify-center">
          <SearchBox variant="hero" languages={languages} />
        </div>
      </section>

      <div className="grid gap-8 md:grid-cols-3">
        <Column title={t("home.trending")} href="/trending" words={trending.length ? trending : newWords} t={t} />
        <Column title={t("home.aiTerms")} href="/ai-terms" words={aiTerms} t={t} />
        <Column title={t("home.newWords")} href="/new" words={newWords} t={t} />
      </div>

      <section className="mt-10 rounded-xl border border-dashed border-line p-5 text-center">
        <h2 className="font-semibold">{t("home.learn")}</h2>
        <p className="mt-1 text-sm text-muted">{t("home.learnSoon")}</p>
      </section>
    </div>
  );
}
