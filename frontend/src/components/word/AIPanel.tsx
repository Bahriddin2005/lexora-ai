"use client";

import { Loader2, Sparkles } from "lucide-react";
import { useRef, useState } from "react";

import { Markdown } from "@/components/Markdown";
import { useI18n } from "@/i18n/client";
import { apiFetch } from "@/lib/client-api";
import { toApiError } from "@/lib/api-error";
import { readSse } from "@/lib/sse";

type Level = "simple" | "detailed";

export function AIPanel({ lang, slug }: { lang: string; slug: string }) {
  const { t, locale } = useI18n();
  const [level, setLevel] = useState<Level>("simple");
  const [question, setQuestion] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runId = useRef(0);

  const run = async (nextLevel: Level, ask?: string) => {
    const id = ++runId.current;
    setLevel(nextLevel);
    setText("");
    setError(null);
    setLoading(true);
    try {
      const res = await apiFetch(`/words/${lang}/${encodeURIComponent(slug)}/explain`, {
        method: "POST",
        body: JSON.stringify({ lang: locale, level: nextLevel, question: ask || null }),
      });
      if (!res.ok) {
        const err = await toApiError(res);
        setError(err.code === "quota_exceeded" ? t("search.quotaExceeded") : err.code === "ai_unavailable" ? t("search.aiUnavailable") : err.message);
        return;
      }
      await readSse(res, (event) => {
        if (id !== runId.current) return;
        if (event.delta) setText((prev) => prev + event.delta);
        if (event.error) setError(event.message ?? t("search.aiFailed"));
      });
    } catch {
      if (id === runId.current) setError(t("common.error"));
    } finally {
      if (id === runId.current) setLoading(false);
    }
  };

  return (
    <section className="rounded-xl border border-accent/40 bg-accent/5 p-4" data-testid="ai-panel">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-semibold">
          <Sparkles className="size-4 text-accent" /> {t("word.explainTitle")}
        </h2>
        <div className="flex gap-1">
          {(["simple", "detailed"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => run(value)}
              disabled={loading}
              className={`btn ${level === value && text ? "border-accent text-accent" : ""}`}
            >
              {value === "simple" ? t("word.explainSimple") : t("word.explainDetailed")}
            </button>
          ))}
        </div>
      </div>
      <form
        className="mt-3 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (question.trim()) run(level, question.trim());
        }}
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t("word.explainQuestion")}
          maxLength={500}
          className="input"
        />
        <button type="submit" className="btn btn-primary shrink-0" disabled={loading || !question.trim()}>
          {t("word.explainAsk")}
        </button>
      </form>
      {(text || loading || error) && (
        <div className="mt-4 text-sm" aria-live="polite">
          {text && <Markdown text={text} />}
          {loading && !text && <Loader2 className="size-5 animate-spin text-accent" />}
          {error && <p className="text-danger">{error}</p>}
          {text && !loading && <p className="mt-3 text-xs text-muted">{t("word.explainDisclaimer")}</p>}
        </div>
      )}
    </section>
  );
}
