import { BookOpenText, ChevronLeft, ChevronRight, Search, X } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { WordCard } from "@/components/WordCard";
import { getT } from "@/i18n/server";
import { apiServer } from "@/lib/server-api";
import type { DictionaryPage } from "@/lib/types";
import { LANGUAGE_FLAGS } from "@/lib/words";

export const metadata: Metadata = {
  title: "Lug‘at",
  description: "Lexora AI lug‘atidagi barcha so‘zlar.",
};

const LANGUAGES = ["uz", "en", "ru", "tr"] as const;
const ALPHABETS: Record<string, string[]> = {
  uz: ["A", "B", "D", "E", "F", "G", "G‘", "H", "I", "J", "K", "L", "M", "N", "O", "O‘", "P", "Q", "R", "S", "Sh", "T", "U", "V", "X", "Y", "Z", "Ch"],
  en: "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split(""),
  ru: "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ".split(""),
  tr: ["A", "B", "C", "Ç", "D", "E", "F", "G", "Ğ", "H", "I", "İ", "J", "K", "L", "M", "N", "O", "Ö", "P", "R", "S", "Ş", "T", "U", "Ü", "V", "Y", "Z"],
};

const param = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value) ?? "";

export default async function DictionaryPage({ searchParams }: PageProps<"/dictionary">) {
  const sp = await searchParams;
  const lang = LANGUAGES.includes(param(sp.lang) as (typeof LANGUAGES)[number]) ? param(sp.lang) : "";
  const letter = param(sp.letter).slice(0, 3);
  const search = param(sp.q).trim().slice(0, 100);
  const page = Math.max(1, Number(param(sp.page)) || 1);
  const query = new URLSearchParams({ page: String(page), size: "40" });
  if (lang) query.set("lang", lang);
  if (letter) query.set("letter", letter.replace("‘", "'"));
  if (search) query.set("q", search);

  const [{ t }, data] = await Promise.all([
    getT(),
    apiServer<DictionaryPage>(`/dictionary?${query}`),
  ]);
  const totalPages = Math.max(1, Math.ceil(data.total / data.size));
  const href = (updates: { lang?: string; letter?: string; q?: string; page?: number }) => {
    const next = new URLSearchParams();
    const nextLang = updates.lang ?? lang;
    const nextLetter = updates.letter ?? letter;
    const nextSearch = updates.q ?? search;
    const nextPage = updates.page ?? 1;
    if (nextLang) next.set("lang", nextLang);
    if (nextLetter) next.set("letter", nextLetter);
    if (nextSearch) next.set("q", nextSearch);
    if (nextPage > 1) next.set("page", String(nextPage));
    const value = next.toString();
    return value ? `/dictionary?${value}` : "/dictionary";
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-7 sm:py-10">
      <header className="mb-7 border-b border-line pb-6">
        <div className="flex items-start gap-3">
          <div className="mt-1 rounded-xl bg-brand/10 p-2.5 text-brand">
            <BookOpenText aria-hidden className="size-6" />
          </div>
          <div>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{t("dictionary.title")}</h1>
            <p className="mt-1 max-w-xl text-sm text-muted sm:text-base">{t("dictionary.description")}</p>
          </div>
        </div>
        <p className="mt-5 text-sm font-medium text-brand">{t("dictionary.wordCount", { n: data.total })}</p>
      </header>

      <form action="/dictionary" className="mb-5 flex gap-2" role="search">
        {lang && <input type="hidden" name="lang" value={lang} />}
        {letter && <input type="hidden" name="letter" value={letter} />}
        <label className="relative min-w-0 flex-1">
          <span className="sr-only">{t("common.searchPlaceholder")}</span>
          <Search aria-hidden className="pointer-events-none absolute start-3 top-1/2 size-5 -translate-y-1/2 text-muted" />
          <input
            name="q"
            type="search"
            defaultValue={search}
            placeholder={t("common.searchPlaceholder")}
            className="input h-11 ps-10 text-base"
            autoComplete="off"
          />
        </label>
        {search && (
          <Link href={href({ q: "" })} className="btn size-11 shrink-0 p-0" aria-label={t("common.close")}>
            <X aria-hidden className="size-5" />
          </Link>
        )}
        <button type="submit" className="btn btn-primary h-11 shrink-0 px-4">
          <Search aria-hidden className="size-4 sm:hidden" />
          <span className="max-sm:sr-only">{t("common.search")}</span>
        </button>
      </form>

      <section aria-label={t("common.language")} className="mb-5 flex gap-2 overflow-x-auto pb-1">
        <Link href={href({ lang: "", letter: "" })} className={!lang ? "btn btn-primary shrink-0" : "btn shrink-0"}>
          {t("dictionary.allLanguages")}
        </Link>
        {LANGUAGES.map((code) => (
          <Link key={code} href={href({ lang: code, letter: "" })} className={lang === code ? "btn btn-primary shrink-0" : "btn shrink-0"}>
            <span aria-hidden>{LANGUAGE_FLAGS[code]}</span> {t(`langs.${code}`)}
          </Link>
        ))}
      </section>

      {lang && (
        <section aria-label={t("dictionary.allLetters")} className="mb-7 flex flex-wrap gap-1.5">
          <Link href={href({ letter: "" })} className={!letter ? "chip border-brand bg-brand text-white" : "chip"}>
            {t("dictionary.allLetters")}
          </Link>
          {ALPHABETS[lang].map((char) => (
            <Link key={char} href={href({ letter: char })} className={letter === char ? "chip border-brand bg-brand text-white" : "chip"}>
              {char}
            </Link>
          ))}
        </section>
      )}

      {data.items.length ? (
        <div className="grid gap-2.5 sm:grid-cols-2" data-testid="dictionary-words">
          {data.items.map((word) => <WordCard key={word.id} word={word} t={t} />)}
        </div>
      ) : data.online_items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-line px-5 py-12 text-center text-muted">{t("dictionary.empty")}</div>
      ) : null}

      {data.online_items.length > 0 && (
        <section className="mt-7 border-t border-line pt-6" data-testid="online-dictionary-results">
          <h2 className="text-xl font-semibold">{t("dictionary.onlineTitle")}</h2>
          <p className="mt-1 text-sm text-muted">{t("dictionary.onlineHint")}</p>
          <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
            {data.online_items.map((word) => (
              <a
                key={`${word.language_code}-${word.url}`}
                href={word.url}
                target="_blank"
                rel="noreferrer"
                className="card block transition hover:border-brand hover:shadow-sm"
              >
                <div className="flex items-center gap-2">
                  <span aria-hidden>{LANGUAGE_FLAGS[word.language_code]}</span>
                  <span className="text-lg font-semibold">{word.title}</span>
                  <span className="ms-auto text-xs text-brand">Wiktionary</span>
                </div>
                {word.description && <p className="mt-1 line-clamp-2 text-sm text-muted">{word.description}</p>}
                <span className="mt-2 inline-block text-sm font-medium text-brand">{t("dictionary.openSource")}</span>
              </a>
            ))}
          </div>
        </section>
      )}

      {totalPages > 1 && (
        <nav className="mt-8 flex items-center justify-between border-t border-line pt-5" aria-label={t("dictionary.page", { current: data.page, total: totalPages })}>
          {data.page > 1 ? (
            <Link href={href({ page: data.page - 1 })} className="btn"><ChevronLeft className="size-4" /> {t("dictionary.previous")}</Link>
          ) : <span />}
          <span className="text-sm tabular-nums text-muted">{t("dictionary.page", { current: data.page, total: totalPages })}</span>
          {data.page < totalPages ? (
            <Link href={href({ page: data.page + 1 })} className="btn">{t("dictionary.next")} <ChevronRight className="size-4" /></Link>
          ) : <span />}
        </nav>
      )}
    </div>
  );
}
