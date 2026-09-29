import { NextRequest, NextResponse } from "next/server";

import type { Language, SearchResponse, WordEntry, WordSummary } from "@/lib/types";

const LANGUAGES: Language[] = [
  { code: "uz", name: "Uzbek", native_name: "O‘zbekcha", script: "Latin", direction: "ltr", flag: "🇺🇿", tts_supported: true },
  { code: "en", name: "English", native_name: "English", script: "Latin", direction: "ltr", flag: "🇬🇧", tts_supported: true },
  { code: "ru", name: "Russian", native_name: "Русский", script: "Cyrillic", direction: "ltr", flag: "🇷🇺", tts_supported: true },
  { code: "tr", name: "Turkish", native_name: "Türkçe", script: "Latin", direction: "ltr", flag: "🇹🇷", tts_supported: true },
];

const STARTER_WORDS: Array<[string, string, string, string]> = [
  ["en", "hello", "interjection", "salom"], ["en", "book", "noun", "kitob"],
  ["en", "write", "verb", "yozmoq"], ["en", "play", "verb", "o‘ynamoq"],
  ["uz", "salom", "interjection", "hello"], ["uz", "kitob", "noun", "book"],
  ["uz", "maktab", "noun", "school"], ["ru", "привет", "interjection", "salom"],
  ["ru", "книга", "noun", "kitob"], ["tr", "merhaba", "interjection", "salom"],
  ["tr", "kitap", "noun", "kitob"], ["en", "artificial intelligence", "noun", "sun’iy intellekt"],
];

const slugify = (value: string) => encodeURIComponent(value.trim().toLocaleLowerCase()).replace(/%20/g, "-");
const unSlug = (value: string) => decodeURIComponent(value).replaceAll("-", " ");
const idFor = (value: string) => [...value].reduce((sum, char) => (sum * 31 + char.charCodeAt(0)) >>> 0, 7);

function summary(lang: string, lemma: string, pos = "word", translation?: string, match: WordSummary["match"] = "list"): WordSummary {
  return {
    id: idFor(`${lang}:${lemma}`), language_code: lang, lemma, slug: slugify(lemma), entry_type: "word",
    status: "published", confidence: null, pos: [pos], cefr_level: null,
    short_definition: translation ? `${translation}` : null,
    primary_translation: translation ? { language_code: lang === "uz" ? "en" : "uz", text: translation } : null,
    match, score: null, saved_at: null,
  };
}

const starterSummaries = () => STARTER_WORDS.map(([lang, lemma, pos, translation]) => summary(lang, lemma, pos, translation));

async function wikiSearch(query: string, preferred?: string, limit = 12) {
  const langs = ["uz", "en", "ru", "tr"].sort((a) => a === preferred ? -1 : 0);
  const batches = await Promise.allSettled(langs.map(async (lang) => {
    const url = new URL(`https://${lang}.wiktionary.org/w/api.php`);
    Object.entries({ action: "opensearch", search: query, limit: "6", namespace: "0", format: "json", origin: "*" })
      .forEach(([key, value]) => url.searchParams.set(key, value));
    const response = await fetch(url, { headers: { "user-agent": "LexoraAI/1.0" }, signal: AbortSignal.timeout(5000) });
    if (!response.ok) return [];
    const data = await response.json() as [string, string[], string[], string[]];
    return (data[1] ?? []).map((title, index) => ({ language_code: lang, title, description: data[2]?.[index] || null, url: data[3]?.[index] }));
  }));
  return batches.flatMap((batch) => batch.status === "fulfilled" ? batch.value : []).filter((item) => item.url).slice(0, limit);
}

async function wordEntry(lang: string, lemma: string): Promise<WordEntry | null> {
  let definitions: string[] = [];
  let pos = "word";
  let phonetic: string | null = null;
  let audio: string | null = null;
  let synonyms: string[] = [];
  let antonyms: string[] = [];

  if (lang === "en") {
    try {
      const response = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(lemma)}`, { signal: AbortSignal.timeout(6000) });
      if (response.ok) {
        const rows = await response.json() as Array<Record<string, unknown>>;
        const first = rows[0] as { phonetic?: string; phonetics?: Array<{ text?: string; audio?: string }>; meanings?: Array<{ partOfSpeech?: string; definitions?: Array<{ definition?: string; example?: string; synonyms?: string[]; antonyms?: string[] }> }> };
        phonetic = first.phonetic ?? first.phonetics?.find((p) => p.text)?.text ?? null;
        audio = first.phonetics?.find((p) => p.audio)?.audio ?? null;
        pos = first.meanings?.[0]?.partOfSpeech ?? "word";
        const defs = first.meanings?.flatMap((meaning) => meaning.definitions ?? []) ?? [];
        definitions = defs.map((item) => item.definition ?? "").filter(Boolean).slice(0, 5);
        synonyms = defs.flatMap((item) => item.synonyms ?? []).slice(0, 8);
        antonyms = defs.flatMap((item) => item.antonyms ?? []).slice(0, 8);
      }
    } catch { /* online source temporarily unavailable */ }
  }

  if (!definitions.length) {
    try {
      const response = await fetch(`https://${lang}.wiktionary.org/api/rest_v1/page/summary/${encodeURIComponent(lemma)}`, { signal: AbortSignal.timeout(5000) });
      if (response.ok) {
        const data = await response.json() as { extract?: string; description?: string };
        definitions = [data.extract ?? data.description ?? ""].filter(Boolean);
      }
    } catch { /* online source temporarily unavailable */ }
  }
  const starter = STARTER_WORDS.find(([code, word]) => code === lang && word.toLocaleLowerCase() === lemma.toLocaleLowerCase());
  if (!definitions.length && starter) definitions = [starter[3]];
  if (!definitions.length) return null;

  return {
    id: idFor(`${lang}:${lemma}`), language_code: lang, lemma, slug: slugify(lemma), entry_type: "word",
    status: "published", confidence: null, cefr_level: null, frequency_zipf: null, tags: [], etymology: null,
    audio_url: audio, pronunciations: phonetic || audio ? [{ ipa: phonetic, accent: null, audio_url: audio }] : [], forms: [],
    senses: [{ id: idFor(`sense:${lang}:${lemma}`), pos, domain: null, register: "neutral", cefr_level: null,
      definitions: { [lang]: definitions[0], ...(lang !== "en" ? { en: definitions[0] } : {}) }, translations: {},
      examples: [], synonyms: synonyms.map((text) => ({ text, slug: slugify(text) })), antonyms: antonyms.map((text) => ({ text, slug: slugify(text) })) }],
    relations: { synonym: [], antonym: [], related: [], derived: [], phrase: [] },
    sources: [{ name: lang === "en" ? "Free Dictionary API / Wiktionary" : "Wiktionary", url: `https://${lang}.wiktionary.org/wiki/${encodeURIComponent(lemma)}`, license: "CC BY-SA" }],
    is_favorite: false, version: 1, updated_at: new Date().toISOString(),
  };
}

function json(data: unknown, status = 200) { return NextResponse.json(data, { status }); }

async function handleGet(request: NextRequest, parts: string[]) {
  const endpoint = parts.join("/");
  if (endpoint === "languages") return json(LANGUAGES);
  if (["trending", "new-words", "ai-terms"].includes(endpoint)) return json(starterSummaries().slice(0, Number(request.nextUrl.searchParams.get("limit")) || 20));
  if (endpoint === "sitemap-words") return json(starterSummaries().map((item) => ({ language_code: item.language_code, slug: item.slug, updated_at: new Date().toISOString() })));
  if (endpoint === "dictionary") {
    const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";
    const lang = request.nextUrl.searchParams.get("lang") ?? "";
    const letter = request.nextUrl.searchParams.get("letter")?.toLocaleLowerCase() ?? "";
    const page = Math.max(1, Number(request.nextUrl.searchParams.get("page")) || 1);
    const size = Math.max(1, Number(request.nextUrl.searchParams.get("size")) || 40);
    let items = starterSummaries().filter((item) => (!lang || item.language_code === lang) && (!letter || item.lemma.toLocaleLowerCase().startsWith(letter)));
    if (q) items = items.filter((item) => `${item.lemma} ${item.primary_translation?.text ?? ""}`.toLocaleLowerCase().includes(q.toLocaleLowerCase()));
    const online = q ? await wikiSearch(q, lang || undefined) : [];
    if (q && !items.length) items = online.slice(0, 8).map((item) => summary(item.language_code, item.title, "word", item.description ?? undefined, "prefix"));
    return json({ items: items.slice((page - 1) * size, page * size), online_items: online, total: items.length, page, size });
  }
  if (endpoint === "search/suggest") {
    const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";
    const lang = request.nextUrl.searchParams.get("lang") ?? "en";
    if (!q) return json([]);
    return json((await wikiSearch(q, lang, 8)).map((item) => summary(item.language_code, item.title, "word", item.description ?? undefined, "prefix")));
  }
  if (endpoint === "search") {
    const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";
    const from = request.nextUrl.searchParams.get("from") ?? "en";
    const online = await wikiSearch(q, from, 10);
    const results = online.length ? online.map((item, index) => summary(item.language_code, item.title, "word", item.description ?? undefined, index === 0 && item.title.toLocaleLowerCase() === q.toLocaleLowerCase() ? "exact" : "prefix")) : [summary(from, q, "word", undefined, "exact")];
    const response: SearchResponse = { query: q, intent: { type: "lookup", term: q, source_lang: from, target_lang: request.nextUrl.searchParams.get("to"), domain: null, year: null }, results, did_you_mean: [], job: null, notice: null, ai_available: false };
    return json(response);
  }
  if (parts[0] === "words" && parts.length >= 3) {
    const lang = parts[1]; const lemma = unSlug(parts.slice(2).join("/"));
    const entry = await wordEntry(lang, lemma);
    return entry ? json(entry) : json({ error: { code: "not_found", message: "Word not found", details: { suggestions: [] } } }, 404);
  }
  return json({ error: { code: "not_found", message: "Endpoint not found", details: {} } }, 404);
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handleGet(request, (await context.params).path);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const parts = (await context.params).path;
  if (parts.join("/") === "translate") {
    const body = await request.json() as { text?: string; source?: string; target?: string };
    const text = body.text?.trim() ?? ""; const source = body.source === "auto" ? "en" : body.source ?? "en"; const target = body.target ?? "uz";
    try {
      const url = new URL("https://api.mymemory.translated.net/get");
      url.searchParams.set("q", text); url.searchParams.set("langpair", `${source}|${target}`);
      const response = await fetch(url, { signal: AbortSignal.timeout(8000) });
      const data = await response.json() as { responseData?: { translatedText?: string; detectedLanguage?: string }; matches?: Array<{ translation?: string }> };
      const translation = data.responseData?.translatedText ?? text;
      return json({ translation, detected_source: data.responseData?.detectedLanguage ?? source, alternatives: (data.matches ?? []).map((row) => row.translation).filter(Boolean).slice(0, 3), notes: null, dictionary: null, cached: false });
    } catch { return json({ error: { code: "translation_failed", message: "Tarjima xizmati vaqtincha ishlamayapti", details: {} } }, 503); }
  }
  return json({ error: { code: "not_found", message: "Endpoint not found", details: {} } }, 404);
}
