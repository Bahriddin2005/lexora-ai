"use client";

import { ArrowLeftRight, Mic, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

import { useI18n } from "@/i18n/client";
import { createLocalStore, useBrowserValue } from "@/lib/browser-store";
import type { Language, WordSummary } from "@/lib/types";
import { LANGUAGE_FLAGS, searchHref, wordHref } from "@/lib/words";

type Props = {
  variant?: "hero" | "compact";
  languages?: Language[];
  initialQuery?: string;
};

const SPEECH_LANGS: Record<string, string> = { uz: "uz-UZ", en: "en-US", ru: "ru-RU", tr: "tr-TR" };
const pairStore = createLocalStore("lx_pair", "auto|uz");

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  start: () => void;
};

function speechRecognition(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as Record<string, unknown>;
  return (w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null) as (new () => SpeechRecognitionLike) | null;
}

export function SearchBox({ variant = "compact", languages = [], initialQuery = "" }: Props) {
  const { t, locale } = useI18n();
  const router = useRouter();
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [q, setQ] = useState(initialQuery);
  const [items, setItems] = useState<WordSummary[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [from, to] = pairStore.useValue().split("|");
  const canListen = useBrowserValue(() => speechRecognition() !== null, false);
  const [listening, setListening] = useState(false);
  const hero = variant === "hero";

  useEffect(() => {
    if (!hero) return;
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (event.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [hero]);

  useEffect(() => {
    const term = q.trim();
    if (term.length < 2) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      const params = new URLSearchParams({ q: term });
      if (hero && from !== "auto") params.set("lang", from);
      try {
        const res = await fetch(`/api/v1/search/suggest?${params}`, { signal: controller.signal });
        if (res.ok) setItems(await res.json());
      } catch {
        // aborted or offline
      }
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [q, from, hero]);

  const savePair = (nextFrom: string, nextTo: string) => pairStore.write(`${nextFrom}|${nextTo}`);
  const suggestions = q.trim().length < 2 ? [] : items;

  const submit = (value = q) => {
    const term = value.trim();
    if (!term) return;
    setOpen(false);
    router.push(hero ? searchHref(term, { from: from === "auto" ? null : from, to }) : searchHref(term));
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => Math.max(i - 1, -1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const picked = open && active >= 0 ? suggestions[active] : undefined;
      if (picked) router.push(wordHref(picked.language_code, picked.slug));
      else submit();
    } else if (event.key === "Escape") {
      if (open) setOpen(false);
      else setQ("");
    }
  };

  const listen = () => {
    const Recognition = speechRecognition();
    if (!Recognition) return;
    const recognition = new Recognition();
    recognition.lang = SPEECH_LANGS[from !== "auto" ? from : locale] ?? "uz-UZ";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      setQ(transcript);
      submit(transcript);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    setListening(true);
    recognition.start();
  };

  const showList = open && suggestions.length > 0;

  return (
    <div className={hero ? "w-full max-w-2xl" : "w-full max-w-md"}>
      <form
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
        className="relative"
      >
        <div
          className={`flex items-center gap-2 rounded-full border border-line bg-bg shadow-sm focus-within:border-brand ${
            hero ? "h-14 px-5" : "h-10 px-4"
          }`}
        >
          <Search aria-hidden className="size-5 shrink-0 text-muted" />
          <input
            ref={inputRef}
            value={q}
            onChange={(event) => {
              setQ(event.target.value);
              setOpen(true);
              setActive(-1);
            }}
            onFocus={() => setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            onKeyDown={onKeyDown}
            placeholder={t("common.searchPlaceholder")}
            aria-label={t("common.searchPlaceholder")}
            role="combobox"
            aria-expanded={showList}
            aria-controls={listId}
            aria-autocomplete="list"
            autoComplete="off"
            spellCheck={false}
            className={`min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted ${hero ? "text-lg" : "text-sm"}`}
            name="q"
          />
          {canListen && (
            <button
              type="button"
              onClick={listen}
              aria-label={t("home.voice")}
              title={listening ? t("home.voiceListening") : t("home.voice")}
              className={`rounded-full p-1.5 hover:bg-surface ${listening ? "animate-pulse text-danger" : "text-muted"}`}
            >
              <Mic className="size-5" />
            </button>
          )}
        </div>
        {showList && (
          <ul
            id={listId}
            role="listbox"
            className="absolute inset-x-0 top-full z-30 mt-2 overflow-hidden rounded-2xl border border-line bg-bg py-1 shadow-lg"
          >
            {suggestions.map((item, index) => (
              <li
                key={item.id}
                role="option"
                aria-selected={index === active}
                onMouseDown={(event) => {
                  event.preventDefault();
                  router.push(wordHref(item.language_code, item.slug));
                }}
                className={`flex cursor-pointer items-baseline gap-2 px-4 py-2 text-sm ${
                  index === active ? "bg-surface" : ""
                }`}
              >
                <span aria-hidden>{LANGUAGE_FLAGS[item.language_code] ?? ""}</span>
                <span className="font-medium">{item.lemma}</span>
                {item.primary_translation && <span className="truncate text-muted">— {item.primary_translation.text}</span>}
              </li>
            ))}
          </ul>
        )}
      </form>

      {hero && languages.length > 0 && (
        <div className="mt-4 flex items-center justify-center gap-3 text-sm">
          <select
            aria-label="From"
            value={from}
            onChange={(event) => savePair(event.target.value, to)}
            className="rounded-lg border border-line bg-bg px-2 py-1"
          >
            <option value="auto">🌐 {t("home.auto")}</option>
            {languages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.flag} {t(`langs.${lang.code}`)}
              </option>
            ))}
          </select>
          <button
            type="button"
            aria-label={t("home.swap")}
            title={t("home.swap")}
            onClick={() => savePair(to, from === "auto" ? "en" : from)}
            className="rounded-full p-1.5 text-muted hover:bg-surface"
          >
            <ArrowLeftRight className="size-4" />
          </button>
          <select
            aria-label="To"
            value={to}
            onChange={(event) => savePair(from, event.target.value)}
            className="rounded-lg border border-line bg-bg px-2 py-1"
          >
            {languages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.flag} {t(`langs.${lang.code}`)}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
