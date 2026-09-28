"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, patch, post } from "@/lib/client-api";

type UserRow = { id: string; role: string; plan: string; is_active: boolean };

export function UserControls({ user }: { user: UserRow }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const update = async (body: Partial<UserRow>) => {
    setError(null);
    try {
      await patch(`/admin/users/${user.id}`, body);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Xatolik");
    }
  };
  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <select value={user.role} onChange={(e) => update({ role: e.target.value })} className="input w-auto py-1" aria-label="Rol">
        {["user", "editor", "admin"].map((r) => (
          <option key={r}>{r}</option>
        ))}
      </select>
      <select value={user.plan} onChange={(e) => update({ plan: e.target.value })} className="input w-auto py-1" aria-label="Tarif">
        {["free", "pro"].map((p) => (
          <option key={p}>{p}</option>
        ))}
      </select>
      <label className="inline-flex items-center gap-1 text-xs">
        <input type="checkbox" checked={user.is_active} onChange={(e) => update({ is_active: e.target.checked })} /> faol
      </label>
      {error && <span className="text-xs text-danger">{error}</span>}
    </span>
  );
}

type LanguageRow = { code: string; is_active: boolean; tts_supported: boolean; sort_order: number };

export function LanguageControls({ lang }: { lang: LanguageRow }) {
  const router = useRouter();
  const update = async (body: Partial<LanguageRow>) => {
    await patch(`/admin/languages/${lang.code}`, body).catch(() => undefined);
    router.refresh();
  };
  return (
    <span className="inline-flex items-center gap-3 text-xs">
      <label className="inline-flex items-center gap-1">
        <input type="checkbox" checked={lang.is_active} onChange={(e) => update({ is_active: e.target.checked })} /> faol
      </label>
      <label className="inline-flex items-center gap-1">
        <input type="checkbox" checked={lang.tts_supported} onChange={(e) => update({ tts_supported: e.target.checked })} /> TTS
      </label>
      <input
        type="number"
        defaultValue={lang.sort_order}
        onBlur={(e) => Number(e.target.value) !== lang.sort_order && update({ sort_order: Number(e.target.value) })}
        className="input w-20 py-1"
        aria-label="Tartib"
      />
    </span>
  );
}

export function NewLanguageForm() {
  const router = useRouter();
  const [form, setForm] = useState({ code: "", name: "", native_name: "", script: "Latn", direction: "ltr", flag: "" });
  const [error, setError] = useState<string | null>(null);
  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [key]: e.target.value });
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await post("/admin/languages", { ...form, flag: form.flag || null });
      setForm({ code: "", name: "", native_name: "", script: "Latn", direction: "ltr", flag: "" });
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Xatolik");
    }
  };
  return (
    <form onSubmit={submit} className="card flex flex-wrap items-end gap-2">
      <input required placeholder="code (kk)" value={form.code} onChange={set("code")} className="input w-24" />
      <input required placeholder="Name (Kazakh)" value={form.name} onChange={set("name")} className="input w-36" />
      <input required placeholder="Native (Қазақша)" value={form.native_name} onChange={set("native_name")} className="input w-36" />
      <select value={form.script} onChange={set("script")} className="input w-auto" aria-label="Yozuv">
        {["Latn", "Cyrl", "Arab", "Hans", "Jpan", "Kore", "Deva", "Grek", "Hebr", "Geor", "Armn"].map((s) => (
          <option key={s}>{s}</option>
        ))}
      </select>
      <select value={form.direction} onChange={set("direction")} className="input w-auto" aria-label="Yo‘nalish">
        <option>ltr</option>
        <option>rtl</option>
      </select>
      <input placeholder="🇰🇿" value={form.flag} onChange={set("flag")} className="input w-16" />
      <button className="btn btn-primary">+ Til qo‘shish</button>
      {error && <span className="w-full text-xs text-danger">{error}</span>}
    </form>
  );
}
