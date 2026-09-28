import type { Metadata } from "next";
import Link from "next/link";
import { cache } from "react";

import { AIPanel } from "@/components/word/AIPanel";
import { SpeakButton } from "@/components/word/SpeakButton";
import { WordActions } from "@/components/word/WordActions";
import { getT } from "@/i18n/server";
import { labelOr, type TFunction } from "@/i18n/translate";
import { ApiError } from "@/lib/api-error";
import { apiServer } from "@/lib/server-api";
import type { Link as WordLink, Sense, WordEntry } from "@/lib/types";
import { frequencyDots, groupByPos, LANGUAGE_FLAGS, orderedDefinitions, searchHref, wordHref } from "@/lib/words";

type Suggestion = { language_code: string; slug: string; lemma: string };
type Loaded = { entry: WordEntry } | { entry: null; suggestions: Suggestion[] };

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

const load = cache(async (lang: string, rawSlug: string): Promise<Loaded> => {
  const slug = safeDecode(rawSlug);
  try {
    return { entry: await apiServer<WordEntry>(`/words/${lang}/${encodeURIComponent(slug)}`) };
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return { entry: null, suggestions: (err.details.suggestions as Suggestion[] | undefined) ?? [] };
    }
    throw err;
  }
});

function summary(entry: WordEntry): string {
  const first = entry.senses[0];
  const definition = first ? (first.definitions.uz ?? first.definitions.en ?? Object.values(first.definitions)[0]) : "";
  const translations = ["uz", "en", "ru", "tr"]
    .filter((l) => l !== entry.language_code)
    .map((l) => first?.translations[l]?.[0]?.text)
    .filter(Boolean)
    .join(", ");
  return [definition, translations].filter(Boolean).join(" — ");
}

export async function generateMetadata({ params }: PageProps<"/w/[lang]/[slug]">): Promise<Metadata> {
  const { lang, slug } = await params;
  const data = await load(lang, slug);
  if (!data.entry) return { title: safeDecode(slug), robots: { index: false } };
  const { entry } = data;
  return {
    title: `${entry.lemma} — ma’nosi, tarjimasi, talaffuzi`,
    description: summary(entry).slice(0, 300),
    alternates: { canonical: wordHref(entry.language_code, entry.slug) },
    openGraph: { title: `${entry.lemma} | Lexora AI`, description: summary(entry).slice(0, 300) },
    robots: entry.status === "published" ? undefined : { index: false },
  };
}

function Chips({ items, lang }: { items: WordLink[]; lang: string }) {
  return (
    <span className="inline-flex flex-wrap gap-1.5">
      {items.map((item) =>
        item.slug ? (
          <Link key={item.text} href={wordHref(lang, item.slug)} className="chip hover:border-brand" lang={lang}>
            {item.text}
          </Link>
        ) : (
          <span key={item.text} className="chip" lang={lang}>
            {item.text}
          </span>
        ),
      )}
    </span>
  );
}

function SenseBlock({ sense, index, entry, t, uiLang }: { sense: Sense; index: number; entry: WordEntry; t: TFunction; uiLang: string }) {
  const definitions = orderedDefinitions(sense.definitions, uiLang, entry.language_code);
  const translationLangs = ["uz", "en", "ru", "tr"].filter((l) => sense.translations[l]?.length);
  return (
    <li className="space-y-2" data-testid="sense">
      <div className="flex gap-3">
        <span className="font-semibold text-muted">{index}.</span>
        <div className="flex-1 space-y-2">
          <div className="flex flex-wrap items-baseline gap-2">
            {sense.domain && <span className="badge bg-accent/10 text-accent">{labelOr(t, "domain", sense.domain)}</span>}
            {sense.register !== "neutral" && t(`register.${sense.register}`) && (
              <span className="badge bg-warning/15 text-warning">{t(`register.${sense.register}`)}</span>
            )}
            {sense.cefr_level && <span className="badge bg-surface text-muted">{sense.cefr_level}</span>}
            {definitions[0] && (
              <span className="text-base" lang={definitions[0].lang}>
                {definitions[0].text}
              </span>
            )}
          </div>
          {definitions.slice(1).map((d) => (
            <p key={d.lang} className="text-sm text-muted" lang={d.lang}>
              ({d.text})
            </p>
          ))}
          {translationLangs.length > 0 && (
            <div className="space-y-1">
              {translationLangs.map((l) => (
                <div key={l} className="flex flex-wrap items-center gap-2 text-sm">
                  <span aria-hidden>{LANGUAGE_FLAGS[l]}</span>
                  <Chips items={sense.translations[l]} lang={l} />
                </div>
              ))}
            </div>
          )}
          {sense.examples.length > 0 && (
            <ul className="space-y-1 border-s-2 border-line ps-3 text-sm">
              {sense.examples.map((ex) => {
                const translation = ex.translations[uiLang] ?? ex.translations.uz ?? ex.translations.en;
                return (
                  <li key={ex.text}>
                    <span className="italic" lang={entry.language_code}>
                      {ex.text}
                    </span>
                    {translation && <span className="text-muted"> — {translation}</span>}
                  </li>
                );
              })}
            </ul>
          )}
          {(sense.synonyms.length > 0 || sense.antonyms.length > 0) && (
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
              {sense.synonyms.length > 0 && (
                <span className="flex flex-wrap items-center gap-1.5">
                  <span className="text-muted">{t("word.synonyms")}:</span>
                  <Chips items={sense.synonyms} lang={entry.language_code} />
                </span>
              )}
              {sense.antonyms.length > 0 && (
                <span className="flex flex-wrap items-center gap-1.5">
                  <span className="text-muted">{t("word.antonyms")}:</span>
                  <Chips items={sense.antonyms} lang={entry.language_code} />
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

export default async function WordPage({ params }: PageProps<"/w/[lang]/[slug]">) {
  const { lang, slug } = await params;
  const [data, { t, locale }] = await Promise.all([load(lang, slug), getT()]);

  if (!data.entry) {
    const term = safeDecode(slug);
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-12">
        <h1 className="text-2xl font-semibold">{t("word.notFound", { q: term })}</h1>
        {data.suggestions.length > 0 && (
          <p className="text-lg">
            {data.suggestions.map((s, i) => (
              <span key={s.slug}>
                {i > 0 && ", "}
                <Link href={wordHref(s.language_code, s.slug)} className="font-semibold link">
                  {s.lemma}
                </Link>
              </span>
            ))}{" "}
            <span className="text-muted">{t("search.didYouMean")}</span>
          </p>
        )}
        <Link href={searchHref(term, { from: lang, force_ai: "1" })} className="btn">
          🤖 {t("word.searchWithAi")}
        </Link>
      </div>
    );
  }

  const { entry } = data;
  const posList = [...new Set(entry.senses.map((s) => s.pos))];
  const dots = frequencyDots(entry.frequency_zipf);
  const primaryLangs = [locale, "uz", "en", "ru", "tr"].filter(
    (l, i, all) => l !== entry.language_code && all.indexOf(l) === i,
  );
  const primary = primaryLangs
    .map((l) => ({ lang: l, text: entry.senses.find((s) => s.translations[l]?.length)?.translations[l][0] }))
    .filter((p) => p.text);
  const relationRows = (["phrase", "related", "derived"] as const).filter((k) => entry.relations[k]?.length);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "DefinedTerm",
    name: entry.lemma,
    description: summary(entry),
    inLanguage: entry.language_code,
    inDefinedTermSet: "https://lexora.ai",
  };

  return (
    <article className="mx-auto max-w-3xl space-y-8 px-4 py-8" lang={locale}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />

      <header className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
          <div className="flex flex-wrap items-center gap-2">
            <span>
              {LANGUAGE_FLAGS[entry.language_code]} {t(`langs.${entry.language_code}`)}
            </span>
            {posList.length > 0 && <span className="italic">· {posList.map((p) => labelOr(t, "pos", p)).join(", ")}</span>}
            {entry.cefr_level && <span className="badge bg-brand/10 text-brand">{entry.cefr_level}</span>}
            {dots > 0 && (
              <span title={t("word.frequency")} aria-label={`${t("word.frequency")}: ${dots}/5`}>
                {"●".repeat(dots)}
                <span className="opacity-30">{"●".repeat(5 - dots)}</span>
              </span>
            )}
          </div>
          <WordActions wordId={entry.id} initialFavorite={entry.is_favorite} />
        </div>

        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl" lang={entry.language_code} data-testid="headword">
          {entry.lemma}
        </h1>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          {entry.pronunciations.length > 0 ? (
            entry.pronunciations.map((p, i) => (
              <span key={`${p.accent}-${i}`} className="inline-flex items-center gap-1">
                {p.ipa && <span className="font-[family-name:var(--font-ipa)] text-muted">{p.ipa}</span>}
                <SpeakButton url={p.audio_url} text={entry.lemma} lang={entry.language_code} accent={p.accent} label={p.accent ?? undefined} />
              </span>
            ))
          ) : (
            <SpeakButton url={entry.audio_url} text={entry.lemma} lang={entry.language_code} />
          )}
        </div>

        {primary.length > 0 && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-lg" data-testid="primary-translations">
            {primary.map((p) => (
              <span key={p.lang}>
                <span aria-hidden>{LANGUAGE_FLAGS[p.lang]}</span>{" "}
                {p.text!.slug ? (
                  <Link href={wordHref(p.lang, p.text!.slug)} className="link" lang={p.lang}>
                    {p.text!.text}
                  </Link>
                ) : (
                  <span lang={p.lang}>{p.text!.text}</span>
                )}
              </span>
            ))}
          </div>
        )}

        {entry.status === "ai_generated" && (
          <p className="rounded-lg bg-warning/10 px-3 py-2 text-sm text-warning" data-testid="ai-badge">
            {t("word.aiBadge", { n: Math.round((entry.confidence ?? 0) * 100) })}
            <span className="block text-xs opacity-80">{t("word.aiBadgeHint")}</span>
          </p>
        )}
      </header>

      {groupByPos(entry.senses).map(([pos, senses]) => (
        <section key={pos} className="space-y-3">
          <h2 className="border-b border-line pb-1 text-sm font-semibold uppercase tracking-wide text-muted">{labelOr(t, "pos", pos)}</h2>
          <ol className="space-y-5">
            {senses.map((sense, i) => (
              <SenseBlock key={sense.id} sense={sense} index={i + 1} entry={entry} t={t} uiLang={locale} />
            ))}
          </ol>
        </section>
      ))}

      {(relationRows.length > 0 || entry.forms.length > 0) && (
        <section className="space-y-2 text-sm">
          {relationRows.map((kind) => (
            <div key={kind} className="flex flex-wrap items-center gap-2">
              <span className="text-muted">{t(kind === "phrase" ? "word.phrases" : `word.${kind}`)}:</span>
              <Chips items={entry.relations[kind]} lang={entry.language_code} />
            </div>
          ))}
          {entry.forms.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-muted">{t("word.forms")}:</span>
              <span lang={entry.language_code}>{entry.forms.map((f) => f.form).join(" · ")}</span>
            </div>
          )}
        </section>
      )}

      {entry.etymology && Object.keys(entry.etymology).length > 0 && (
        <details className="card text-sm">
          <summary className="cursor-pointer font-medium">{t("word.etymology")}</summary>
          <p className="mt-2 text-muted">{entry.etymology[locale] ?? entry.etymology.uz ?? entry.etymology.en}</p>
        </details>
      )}

      <AIPanel lang={entry.language_code} slug={entry.slug} />

      {entry.sources.length > 0 && (
        <footer className="text-xs text-muted">
          {t("word.sources")}:{" "}
          {entry.sources.map((s, i) => (
            <span key={s.name}>
              {i > 0 && " · "}
              {s.url ? (
                <a href={s.url} className="hover:underline" rel="noopener nofollow">
                  {s.name}
                </a>
              ) : (
                s.name
              )}
              {s.license && ` (${s.license})`}
            </span>
          ))}
        </footer>
      )}
    </article>
  );
}
