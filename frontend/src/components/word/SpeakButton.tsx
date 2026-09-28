"use client";

import { Loader2, Volume2 } from "lucide-react";
import { useState } from "react";

import { useI18n } from "@/i18n/client";

const VOICE_LANGS: Record<string, string> = { uz: "uz-UZ", en: "en-US", ru: "ru-RU", tr: "tr-TR" };

export function SpeakButton({
  url,
  text,
  lang,
  accent,
  label,
}: {
  url: string | null;
  text: string;
  lang: string;
  accent?: string | null;
  label?: string;
}) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);

  const fallback = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = accent === "UK" && lang === "en" ? "en-GB" : (VOICE_LANGS[lang] ?? lang);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const play = async () => {
    if (!url) return fallback();
    setBusy(true);
    try {
      await new Audio(url).play();
    } catch {
      fallback();
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      type="button"
      onClick={play}
      className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-sm text-brand hover:bg-surface"
      aria-label={`${t("word.listen")}${accent ? ` (${accent})` : ""}`}
      title={t("word.listen")}
    >
      {busy ? <Loader2 className="size-4 animate-spin" /> : <Volume2 className="size-4" />}
      {label && <span>{label}</span>}
    </button>
  );
}
