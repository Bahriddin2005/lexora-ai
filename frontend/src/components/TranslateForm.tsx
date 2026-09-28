"use client";

import { ArrowLeftRight, Copy, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { SpeakButton } from "@/components/word/SpeakButton";
import { useI18n } from "@/i18n/client";
import { ApiError, post } from "@/lib/client-api";
import type { Language, TranslateResult } from "@/lib/types";
import { wordHref } from "@/lib/words";

const MAX_CHARS = 1000;

export function TranslateForm({ languages }: { languages: Language[] }) {
  const { t } = useI18n();
  const [text, setText] = useState("");
  const [source, setSource] = useState("auto");
  const [target, setTarget] = useState("uz");
  const [result, setResult] = useState<TranslateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event?: React.FormEvent) => {
    event?.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await post<TranslateResult>("/translate", { text, source, target }));
    } catch (err) {
      setResult(null);
      if (err instanceof ApiError && err.code === "quota_exceeded") setError(t("search.quotaExceeded"));
      else if (err instanceof ApiError && err.code === "ai_unavailable") setError(t("search.aiUnavailable"));
      else setError(err instanceof Error ? err.message : t("common.error"));
    } finally {
      setLoading(false);
    }
  };

  const swap = () => {
    if (source === "auto") return;
    setSource(target);
    setTarget(source);
    if (result) setText(result.translation);
    setResult(null);
  };

  const select = (value: string, onChange: (v: string) => void, withAuto: boolean, label: string) => (
    <select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} className="input w-auto">
      {withAuto && <option value="auto">🌐 {t("translate.auto")}</option>}
      {languages.map((l) => (
        <option key={l.code} value={l.code}>
          {l.flag} {t(`langs.${l.code}`)}
        </option>
      ))}
    </select>
  );

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="flex items-center gap-2">
        {select(source, setSource, true, "Source")}
        <button type="button" onClick={swap} className="btn" aria-label={t("home.swap")} disabled={source === "auto"}>
          <ArrowLeftRight className="size-4" />
        </button>
        {select(target, setTarget, false, "Target")}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
            }}
            placeholder={t("translate.placeholder")}
            rows={7}
            className="input resize-y text-base"
            aria-label={t("translate.placeholder")}
          />
          <div className="flex items-center justify-between text-xs text-muted">
            <span>
              {text.length} / {MAX_CHARS}
            </span>
            <button type="submit" className="btn btn-primary" disabled={loading || !text.trim()}>
              {loading && <Loader2 className="size-4 animate-spin" />} {t("translate.submit")}
            </button>
          </div>
        </div>
        <div className="card min-h-[11rem] space-y-3 bg-surface" aria-live="polite" data-testid="translation-result">
          {error && <p className="text-danger">{error}</p>}
          {result && (
            <>
              <p className="text-lg" lang={target}>
                {result.translation}
              </p>
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                {result.detected_source && (
                  <span>{t("translate.detected", { lang: t(`langs.${result.detected_source}`) })}</span>
                )}
                {result.dictionary && <span className="badge bg-success/15 text-success">{t("translate.fromDictionary")}</span>}
                <SpeakButton url={null} text={result.translation} lang={target} />
                <button
                  type="button"
                  className="rounded-full p-1 hover:bg-bg"
                  aria-label={t("translate.copy")}
                  onClick={() => navigator.clipboard?.writeText(result.translation)}
                >
                  <Copy className="size-4" />
                </button>
              </div>
              {result.alternatives.length > 0 && (
                <p className="text-sm">
                  <span className="text-muted">{t("translate.alternatives")}: </span>
                  {result.alternatives.join(", ")}
                </p>
              )}
              {result.notes && (
                <p className="text-sm">
                  <span className="text-muted">{t("translate.notes")}: </span>
                  {result.notes}
                </p>
              )}
              {result.dictionary && (
                <Link href={wordHref(result.dictionary.language_code, result.dictionary.slug)} className="text-sm link">
                  {t("translate.openInDictionary")}
                </Link>
              )}
            </>
          )}
        </div>
      </div>
    </form>
  );
}
