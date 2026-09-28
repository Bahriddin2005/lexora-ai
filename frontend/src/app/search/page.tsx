import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { JobWaiter } from "@/components/JobWaiter";
import { WordCard } from "@/components/WordCard";
import { getT } from "@/i18n/server";
import { apiServer } from "@/lib/server-api";
import type { SearchResponse } from "@/lib/types";
import { LANGUAGE_FLAGS, searchHref, wordHref } from "@/lib/words";

const param = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value) ?? "";

export async function generateMetadata({ searchParams }: PageProps<"/search">): Promise<Metadata> {
  const q = param((await searchParams).q);
  return { title: q ? `“${q}”` : "Search", robots: { index: false } };
}

export default async function SearchPage({ searchParams }: PageProps<"/search">) {
  const sp = await searchParams;
  const q = param(sp.q).trim();
  if (!q) redirect("/");
  const from = param(sp.from);
  const to = param(sp.to);
  const forceAi = param(sp.force_ai) === "1";

  const params = new URLSearchParams({ q });
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  if (forceAi) params.set("force_ai", "true");
  const data = await apiServer<SearchResponse>(`/search?${params}`);
  const { t } = await getT();

  const exact = data.results.filter((r) => r.match === "exact");
  if (data.intent.type !== "list_new_terms" && exact.length === 1 && data.results[0]?.match === "exact") {
    redirect(wordHref(exact[0].language_code, exact[0].slug));
  }

  const title =
    data.intent.type === "list_new_terms"
      ? [data.intent.year, t("search.newTerms"), data.intent.domain?.toUpperCase()].filter(Boolean).join(" · ")
      : t("search.resultsFor", { q: data.intent.term ?? q });

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <h1 className="text-xl font-semibold">{title}</h1>

      {data.results.length > 0 && (
        <div className="grid gap-3" data-testid="search-results">
          {data.results.map((word) => (
            <WordCard key={word.id} word={word} t={t} />
          ))}
        </div>
      )}

      {data.results.length === 0 && data.intent.type !== "list_new_terms" && (
        <div className="space-y-4">
          <p className="text-muted">{t("search.noResults")}</p>
          {data.did_you_mean.length > 0 && (
            <p className="text-lg" data-testid="did-you-mean">
              {data.did_you_mean.slice(0, 3).map((s, i) => (
                <span key={`${s.language_code}-${s.slug}`}>
                  {i > 0 && ", "}
                  <Link href={wordHref(s.language_code, s.slug)} className="font-semibold link">
                    {LANGUAGE_FLAGS[s.language_code]} {s.lemma}
                  </Link>
                </span>
              ))}{" "}
              <span className="text-muted">{t("search.didYouMean")}</span>
            </p>
          )}
          {data.job && <JobWaiter job={data.job} />}
          {data.notice === "quota_exceeded" && <p className="card text-warning">{t("search.quotaExceeded")}</p>}
          {data.notice === "ai_unavailable" && <p className="card text-muted">{t("search.aiUnavailable")}</p>}
          {!data.job && !data.notice && data.ai_available && data.did_you_mean.length > 0 && (
            <Link
              href={searchHref(data.intent.term ?? q, { from, to, force_ai: "1" })}
              className="btn"
              data-testid="ai-anyway"
            >
              🤖 {t("search.aiAnyway")}
            </Link>
          )}
        </div>
      )}

      {data.results.length === 0 && data.intent.type === "list_new_terms" && (
        <p className="text-muted">{t("lists.empty")}</p>
      )}
    </div>
  );
}
