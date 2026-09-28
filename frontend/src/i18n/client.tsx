"use client";

import { createContext, useContext, useMemo } from "react";

import { DEFAULT_LOCALE, type Locale } from "./messages";
import { makeT, type TFunction } from "./translate";

const I18nContext = createContext<{ locale: Locale; t: TFunction }>({
  locale: DEFAULT_LOCALE,
  t: makeT(DEFAULT_LOCALE),
});

export function I18nProvider({ locale, children }: { locale: Locale; children: React.ReactNode }) {
  const value = useMemo(() => ({ locale, t: makeT(locale) }), [locale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
