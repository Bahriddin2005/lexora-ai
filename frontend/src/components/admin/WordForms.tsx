"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, api, post } from "@/lib/client-api";
import type { AdminWordDetail, Job } from "@/lib/types";

const LANGS = ["en", "uz", "ru", "tr"];

export function NewWordForm() {
  const router = useRouter();
  const [lang, setLang] = useState("en");
  const [lemma, setLemma] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      const detail = await post<AdminWordDetail>("/admin/words", { language_code: lang, lemma });
      router.push(`/admin/words/${detail.entry.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Xatolik");
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-center gap-2">
      <select value={lang} onChange={(e) => setLang(e.target.value)} className="input w-auto" aria-label="Til">
        {LANGS.map((l) => (
          <option key={l}>{l}</option>
        ))}
      </select>
      <input value={lemma} onChange={(e) => setLemma(e.target.value)} placeholder="Yangi so‘z" className="input w-40" required />
      <button className="btn">+ Qo‘lda</button>
      {error && <span className="text-xs text-danger">{error}</span>}
    </form>
  );
}

export function GenerateForm() {
  const router = useRouter();
  const [term, setTerm] = useState("");
  const [lang, setLang] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setStatus("🤖 AI ishlamoqda…");
    try {
      let job = await post<Job>("/admin/words/generate", { term, lang: lang || null });
      for (let i = 0; i < 80 && ["queued", "running"].includes(job.status); i++) {
        await new Promise((r) => setTimeout(r, 1500));
        job = await api<Job>(`/jobs/${job.id}`);
      }
      setStatus(`Natija: ${job.status}${job.message ? ` — ${job.message}` : ""}`);
      router.push(`/admin/words?q=${encodeURIComponent(term)}`);
      router.refresh();
    } catch (err) {
      setStatus(err instanceof ApiError ? err.message : "Xatolik");
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-center gap-2">
      <select value={lang} onChange={(e) => setLang(e.target.value)} className="input w-auto" aria-label="Til">
        <option value="">auto</option>
        {LANGS.map((l) => (
          <option key={l}>{l}</option>
        ))}
      </select>
      <input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="AI bilan yaratish" className="input w-44" required />
      <button className="btn btn-primary">🤖 Yaratish</button>
      {status && <span className="text-xs text-muted">{status}</span>}
    </form>
  );
}
