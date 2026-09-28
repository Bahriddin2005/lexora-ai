import { DEFAULT_LOCALE, LOCALES, type Locale, MESSAGES, type Messages } from "./messages";

export type TFunction = (key: string, vars?: Record<string, string | number>) => string;

export function isLocale(value: string | undefined | null): value is Locale {
  return !!value && (LOCALES as string[]).includes(value);
}

function lookup(messages: Messages, key: string): string | undefined {
  let node: unknown = messages;
  for (const part of key.split(".")) {
    if (node && typeof node === "object" && part in node) node = (node as Record<string, unknown>)[part];
    else return undefined;
  }
  return typeof node === "string" ? node : undefined;
}

export function makeT(locale: Locale): TFunction {
  return (key, vars) => {
    let text = lookup(MESSAGES[locale], key) ?? lookup(MESSAGES[DEFAULT_LOCALE], key) ?? key;
    if (vars) for (const [name, value] of Object.entries(vars)) text = text.replaceAll(`{${name}}`, String(value));
    return text;
  };
}

/** Translate `prefix.value`, falling back to the raw value for unknown keys (e.g. new domains). */
export function labelOr(t: TFunction, prefix: string, value: string): string {
  const key = `${prefix}.${value}`;
  const text = t(key);
  return text === key ? value : text;
}
