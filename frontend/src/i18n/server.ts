import { cookies } from "next/headers";

import { DEFAULT_LOCALE, type Locale } from "./messages";
import { isLocale, makeT } from "./translate";

export const LOCALE_COOKIE = "NEXT_LOCALE";

export async function getLocale(): Promise<Locale> {
  const value = (await cookies()).get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

export async function getT() {
  const locale = await getLocale();
  return { locale, t: makeT(locale) };
}
