"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AdminAction } from "@/components/admin/AdminAction";
import { Confidence, formatDate, StatusBadge } from "@/components/admin/ui";
import { ApiError, api, put } from "@/lib/client-api";
import type { AdminWordDetail, SenseIn, TranslationIn, WordEntryIn } from "@/lib/types";
import { wordHref } from "@/lib/words";

const LANGS = ["uz", "en", "ru", "tr"];
const POS = ["noun", "verb", "adj", "adv", "pron", "prep", "conj", "interj", "num", "phrase", "proper_noun", "det", "particle"];
const REGISTERS = ["neutral", "formal", "informal", "slang", "vulgar", "archaic"];
const CEFR = ["", "A1", "A2", "B1", "B2", "C1", "C2"];
const ENTRY_TYPES = ["word", "phrase", "idiom", "phrasal_verb", "abbreviation", "proper_noun"];

const split = (value: string) => value.split(",").map((s) => s.trim()).filter(Boolean);

/** Comma-separated list, committed on blur so typing commas is not disturbed. */
function ListInput({ value, onChange, placeholder }: { value: string[]; onChange: (v: string[]) => void; placeholder?: string }) {
  return (
    <input
      key={value.join(",")}
      defaultValue={value.join(", ")}
      onBlur={(e) => {
        const next = split(e.target.value);
        if (next.join(",") !== value.join(",")) onChange(next);
      }}
      placeholder={placeholder}
      className="input"
    />
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1 text-xs">
      <span className="text-muted">{label}</span>
      {children}
    </label>
  );
}

const emptySense = (): SenseIn => ({
  pos: "noun",
  domain: null,
  register: "neutral",
  cefr_level: null,
  definitions: {},
  translations: {},
  examples: [],
  synonyms: [],
  antonyms: [],
});

function SenseEditor({
  sense,
  index,
  wordLang,
  onChange,
  onRemove,
  onMove,
}: {
  sense: SenseIn;
  index: number;
  wordLang: string;
  onChange: (s: SenseIn) => void;
  onRemove: () => void;
  onMove: (delta: number) => void;
}) {
  const set = <K extends keyof SenseIn>(key: K, value: SenseIn[K]) => onChange({ ...sense, [key]: value });
  const setTranslations = (lang: string, texts: string[]) => {
    const old = sense.translations[lang] ?? [];
    const items: TranslationIn[] = texts.map((text, i) => ({
      text,
      is_primary: i === 0,
      note: old.find((o) => o.text === text)?.note ?? null,
    }));
    const next = { ...sense.translations, [lang]: items };
    if (!items.length) delete next[lang];
    set("translations", next);
  };

  return (
    <div className="card space-y-3" data-testid="sense-editor">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Ma’no {index + 1}</h3>
        <div className="flex gap-1">
          <button type="button" className="btn px-2" onClick={() => onMove(-1)} aria-label="Yuqoriga">
            <ArrowUp className="size-3.5" />
          </button>
          <button type="button" className="btn px-2" onClick={() => onMove(1)} aria-label="Pastga">
            <ArrowDown className="size-3.5" />
          </button>
          <button type="button" className="btn px-2 text-danger" onClick={onRemove} aria-label="O‘chirish">
            <Trash2 className="size-3.5" />
          </button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Field label="Turkum (POS)">
          <select value={sense.pos} onChange={(e) => set("pos", e.target.value)} className="input">
            {[...new Set([sense.pos, ...POS])].map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </Field>
        <Field label="Domen">
          <input value={sense.domain ?? ""} onChange={(e) => set("domain", e.target.value || null)} className="input" placeholder="computing, ai…" />
        </Field>
        <Field label="Register">
          <select value={sense.register} onChange={(e) => set("register", e.target.value)} className="input">
            {REGISTERS.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </Field>
        <Field label="CEFR">
          <select value={sense.cefr_level ?? ""} onChange={(e) => set("cefr_level", e.target.value || null)} className="input">
            {CEFR.map((c) => (
              <option key={c} value={c}>
                {c || "—"}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {LANGS.map((lang) => (
          <Field key={lang} label={`Izoh (${lang})`}>
            <textarea
              value={sense.definitions[lang] ?? ""}
              onChange={(e) => {
                const next = { ...sense.definitions, [lang]: e.target.value };
                if (!e.target.value) delete next[lang];
                set("definitions", next);
              }}
              rows={2}
              className="input"
              data-testid={`definition-${lang}`}
            />
          </Field>
        ))}
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        {LANGS.filter((l) => l !== wordLang).map((lang) => (
          <Field key={lang} label={`Tarjimalar (${lang}) — birinchisi asosiy`}>
            <ListInput value={(sense.translations[lang] ?? []).map((t) => t.text)} onChange={(v) => setTranslations(lang, v)} />
          </Field>
        ))}
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted">
          <span>Misollar</span>
          <button type="button" className="btn px-2 py-0.5 text-xs" onClick={() => set("examples", [...sense.examples, { text: "", translations: {} }])}>
            <Plus className="size-3" /> misol
          </button>
        </div>
        {sense.examples.map((ex, i) => (
          <div key={i} className="grid gap-2 rounded-lg bg-surface p-2 sm:grid-cols-[2fr_1fr_1fr_auto]">
            <input
              value={ex.text}
              onChange={(e) => set("examples", sense.examples.map((x, j) => (j === i ? { ...x, text: e.target.value } : x)))}
              placeholder={`Misol (${wordLang})`}
              className="input"
            />
            {["uz", "en"].filter((l) => l !== wordLang).concat(wordLang === "en" || wordLang === "uz" ? ["ru"] : []).slice(0, 2).map((lang) => (
              <input
                key={lang}
                value={ex.translations[lang] ?? ""}
                onChange={(e) =>
                  set(
                    "examples",
                    sense.examples.map((x, j) =>
                      j === i ? { ...x, translations: { ...x.translations, [lang]: e.target.value } } : x,
                    ),
                  )
                }
                placeholder={lang}
                className="input"
              />
            ))}
            <button type="button" className="btn px-2 text-danger" onClick={() => set("examples", sense.examples.filter((_, j) => j !== i))} aria-label="O‘chirish">
              <Trash2 className="size-3.5" />
            </button>
          </div>
        ))}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <Field label="Sinonimlar">
          <ListInput value={sense.synonyms} onChange={(v) => set("synonyms", v)} />
        </Field>
        <Field label="Antonimlar">
          <ListInput value={sense.antonyms} onChange={(v) => set("antonyms", v)} />
        </Field>
      </div>
    </div>
  );
}

function clean(form: WordEntryIn): WordEntryIn {
  return {
    ...form,
    senses: form.senses.map((s) => ({ ...s, examples: s.examples.filter((e) => e.text.trim()) })),
    pronunciations: form.pronunciations.filter((p) => p.ipa || p.accent),
  };
}

export function WordEditor({ detail, isAdmin }: { detail: AdminWordDetail; isAdmin: boolean }) {
  const router = useRouter();
  const { entry } = detail;
  const [form, setForm] = useState<WordEntryIn>(detail.form);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [jsonMode, setJsonMode] = useState(false);
  const [jsonText, setJsonText] = useState("");
  const [snapshot, setSnapshot] = useState<{ version: number; data: unknown } | null>(null);

  const set = <K extends keyof WordEntryIn>(key: K, value: WordEntryIn[K]) => setForm({ ...form, [key]: value });
  const setSense = (i: number, sense: SenseIn) => set("senses", form.senses.map((s, j) => (j === i ? sense : s)));
  const moveSense = (i: number, delta: number) => {
    const j = i + delta;
    if (j < 0 || j >= form.senses.length) return;
    const senses = [...form.senses];
    [senses[i], senses[j]] = [senses[j], senses[i]];
    set("senses", senses);
  };

  const save = async () => {
    let payload = form;
    if (jsonMode) {
      try {
        payload = JSON.parse(jsonText) as WordEntryIn;
      } catch {
        setMessage("JSON noto‘g‘ri");
        return;
      }
    }
    setSaving(true);
    setMessage(null);
    try {
      const updated = await put<AdminWordDetail>(`/admin/words/${entry.id}`, { entry: clean(payload), reason: reason || "edit" });
      setForm(updated.form);
      setJsonMode(false);
      setReason("");
      setMessage(`Saqlandi — v${updated.entry.version}`);
      router.refresh();
    } catch (err) {
      setMessage(err instanceof ApiError ? `${err.message}${err.details?.errors ? ` ${JSON.stringify(err.details.errors)}` : ""}` : "Xatolik");
    } finally {
      setSaving(false);
    }
  };

  const showVersion = async (version: number) => {
    setSnapshot({ version, data: await api(`/admin/words/${entry.id}/versions/${version}`) });
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_18rem]">
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" className={`btn ${!jsonMode ? "border-brand text-brand" : ""}`} onClick={() => setJsonMode(false)}>
            Forma
          </button>
          <button
            type="button"
            className={`btn ${jsonMode ? "border-brand text-brand" : ""}`}
            onClick={() => {
              setJsonText(JSON.stringify(form, null, 2));
              setJsonMode(true);
            }}
          >
            JSON
          </button>
        </div>

        {jsonMode ? (
          <textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={30} className="input font-mono text-xs" spellCheck={false} />
        ) : (
          <>
            <div className="card grid gap-3 sm:grid-cols-4">
              <Field label="Lemma">
                <input value={form.lemma} onChange={(e) => set("lemma", e.target.value)} className="input" data-testid="lemma-input" />
              </Field>
              <Field label="Turi">
                <select value={form.entry_type} onChange={(e) => set("entry_type", e.target.value)} className="input">
                  {ENTRY_TYPES.map((t) => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </Field>
              <Field label="CEFR">
                <select value={form.cefr_level ?? ""} onChange={(e) => set("cefr_level", e.target.value || null)} className="input">
                  {CEFR.map((c) => (
                    <option key={c} value={c}>
                      {c || "—"}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Teglar">
                <ListInput value={form.tags} onChange={(v) => set("tags", v)} placeholder="ai, slang, new" />
              </Field>
              <Field label="Shakllar">
                <ListInput value={form.forms.map((f) => f.form)} onChange={(v) => set("forms", v.map((form) => ({ form, tags: [] })))} />
              </Field>
              <Field label="Iboralar">
                <ListInput value={form.relations.phrase ?? []} onChange={(v) => set("relations", { ...form.relations, phrase: v })} />
              </Field>
              <Field label="Bog‘liq so‘zlar">
                <ListInput value={form.relations.related ?? []} onChange={(v) => set("relations", { ...form.relations, related: v })} />
              </Field>
              <Field label="Yasama so‘zlar">
                <ListInput value={form.relations.derived ?? []} onChange={(v) => set("relations", { ...form.relations, derived: v })} />
              </Field>
              {["uz", "en"].map((lang) => (
                <div key={lang} className="sm:col-span-2">
                  <Field label={`Etimologiya (${lang})`}>
                    <textarea
                      value={form.etymology?.[lang] ?? ""}
                      onChange={(e) => set("etymology", { ...(form.etymology ?? {}), [lang]: e.target.value })}
                      rows={2}
                      className="input"
                    />
                  </Field>
                </div>
              ))}
              <div className="space-y-2 sm:col-span-4">
                <span className="text-xs text-muted">Talaffuz</span>
                {form.pronunciations.map((p, i) => (
                  <div key={i} className="flex gap-2">
                    <input
                      value={p.ipa ?? ""}
                      onChange={(e) => set("pronunciations", form.pronunciations.map((x, j) => (j === i ? { ...x, ipa: e.target.value || null } : x)))}
                      placeholder="/IPA/"
                      className="input"
                    />
                    <select
                      value={p.accent ?? ""}
                      onChange={(e) => set("pronunciations", form.pronunciations.map((x, j) => (j === i ? { ...x, accent: e.target.value || null } : x)))}
                      className="input w-28"
                    >
                      {["", "US", "UK"].map((a) => (
                        <option key={a} value={a}>
                          {a || "—"}
                        </option>
                      ))}
                    </select>
                    <button type="button" className="btn px-2 text-danger" onClick={() => set("pronunciations", form.pronunciations.filter((_, j) => j !== i))} aria-label="O‘chirish">
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                ))}
                <button type="button" className="btn px-2 py-0.5 text-xs" onClick={() => set("pronunciations", [...form.pronunciations, { ipa: null, accent: null }])}>
                  <Plus className="size-3" /> talaffuz
                </button>
              </div>
            </div>

            {form.senses.map((sense, i) => (
              <SenseEditor
                key={i}
                sense={sense}
                index={i}
                wordLang={entry.language_code}
                onChange={(s) => setSense(i, s)}
                onRemove={() => set("senses", form.senses.filter((_, j) => j !== i))}
                onMove={(delta) => moveSense(i, delta)}
              />
            ))}
            <button type="button" className="btn" onClick={() => set("senses", [...form.senses, emptySense()])}>
              <Plus className="size-4" /> Ma’no qo‘shish
            </button>
          </>
        )}

        <div className="sticky bottom-0 flex flex-wrap items-center gap-2 border-t border-line bg-bg py-3">
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="O‘zgarish sababi" className="input max-w-xs" />
          <button type="button" onClick={save} disabled={saving} className="btn btn-primary" data-testid="save-word">
            💾 Saqlash
          </button>
          {message && <span className="text-sm text-muted">{message}</span>}
        </div>
      </div>

      <aside className="space-y-4 text-sm">
        <div className="card space-y-2">
          <div className="flex items-center justify-between">
            <StatusBadge status={entry.status} />
            <Confidence value={entry.confidence} />
          </div>
          <p className="text-muted">
            v{entry.version} · {formatDate(entry.updated_at)}
          </p>
          {(entry.status === "published" || entry.status === "ai_generated") && (
            <Link href={wordHref(entry.language_code, entry.slug)} className="link">
              Saytda ko‘rish ↗
            </Link>
          )}
          <div className="flex flex-wrap gap-1 pt-1">
            <AdminAction path={`/admin/words/${entry.id}/publish`} label="✅ Nashr" testId="publish-word" />
            <AdminAction path={`/admin/words/${entry.id}/reject`} label="⛔ Rad" />
            <AdminAction path={`/admin/words/${entry.id}/regenerate`} label="🔁 AI qayta" job confirm="AI bu yozuvni qayta yaratsinmi? (joriy holat versiyada saqlanadi)" />
            {isAdmin && (
              <AdminAction method="DELETE" path={`/admin/words/${entry.id}`} label="🗑" className="btn text-danger" confirm="So‘z butunlay o‘chirilsinmi?" redirectTo="/admin/words" />
            )}
          </div>
        </div>
        <div className="card space-y-2">
          <h3 className="font-semibold">Manbalar</h3>
          {entry.sources.map((s) => (
            <p key={s.name} className="text-muted">
              {s.name} {s.license && `(${s.license})`}
            </p>
          ))}
        </div>
        <div className="card space-y-2">
          <h3 className="font-semibold">Versiyalar</h3>
          <ul className="space-y-1">
            {detail.versions.map((v) => (
              <li key={v.version}>
                <button type="button" onClick={() => showVersion(v.version)} className="link text-left">
                  v{v.version}
                </button>{" "}
                <span className="text-muted">
                  {v.reason} · {v.changed_by ?? "tizim"} · {formatDate(v.created_at)}
                </span>
              </li>
            ))}
          </ul>
          {snapshot && (
            <details open className="rounded-lg bg-surface p-2">
              <summary className="cursor-pointer text-xs">v{snapshot.version} snapshot</summary>
              <pre className="mt-2 max-h-80 overflow-auto text-[11px]">{JSON.stringify(snapshot.data, null, 2)}</pre>
            </details>
          )}
        </div>
        {detail.reports.length > 0 && (
          <div className="card space-y-2">
            <h3 className="font-semibold">Reportlar</h3>
            {detail.reports.map((r) => (
              <p key={r.id}>
                <span className="badge bg-surface">{r.status}</span> {r.reason}
                {r.comment && <span className="text-muted"> — {r.comment}</span>}
              </p>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}
