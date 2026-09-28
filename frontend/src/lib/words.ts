export const LANGUAGE_FLAGS: Record<string, string> = { uz: "🇺🇿", en: "🇬🇧", ru: "🇷🇺", tr: "🇹🇷" };

export function wordHref(lang: string, slug: string): string {
  return `/w/${lang}/${encodeURIComponent(slug)}`;
}

export function searchHref(q: string, params: Record<string, string | undefined | null> = {}): string {
  const sp = new URLSearchParams({ q });
  for (const [key, value] of Object.entries(params)) if (value) sp.set(key, value);
  return `/search?${sp.toString()}`;
}

/** Zipf frequency (1-7) → 0-5 dots. */
export function frequencyDots(zipf: number | null): number {
  if (!zipf) return 0;
  return Math.max(1, Math.min(5, Math.round(zipf - 1.5)));
}

/** Definition order: UI language first, then Uzbek, English, the word's own language, then the rest. */
export function orderedDefinitions(definitions: Record<string, string>, uiLang: string, wordLang: string) {
  const order = [uiLang, "uz", "en", wordLang];
  const keys = Object.keys(definitions).sort((a, b) => {
    const ia = order.indexOf(a) === -1 ? 99 : order.indexOf(a);
    const ib = order.indexOf(b) === -1 ? 99 : order.indexOf(b);
    return ia - ib;
  });
  return keys.map((lang) => ({ lang, text: definitions[lang] }));
}

export function groupByPos<T extends { pos: string }>(senses: T[]): [string, T[]][] {
  const groups = new Map<string, T[]>();
  for (const sense of senses) groups.set(sense.pos, [...(groups.get(sense.pos) ?? []), sense]);
  return [...groups.entries()];
}
