"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useI18n } from "@/i18n/client";
import { LOCALES } from "@/i18n/messages";
import { patch } from "@/lib/client-api";
import type { User } from "@/lib/types";

export function ProfileForm({ user }: { user: User }) {
  const { t } = useI18n();
  const router = useRouter();
  const [name, setName] = useState(user.display_name ?? "");
  const [uiLanguage, setUiLanguage] = useState(user.ui_language);
  const [status, setStatus] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await patch("/auth/me", { display_name: name, ui_language: uiLanguage });
      document.cookie = `NEXT_LOCALE=${uiLanguage}; path=/; max-age=31536000; samesite=lax`;
      setStatus(t("profile.saved"));
      router.refresh();
    } catch {
      setStatus(t("common.error"));
    }
  };

  return (
    <form onSubmit={submit} className="card space-y-4">
      <label className="block space-y-1 text-sm">
        <span>{t("auth.displayName")}</span>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} />
      </label>
      <label className="block space-y-1 text-sm">
        <span>{t("common.language")}</span>
        <select className="input" value={uiLanguage} onChange={(e) => setUiLanguage(e.target.value)}>
          {LOCALES.map((code) => (
            <option key={code} value={code}>
              {t(`langs.${code}`)}
            </option>
          ))}
        </select>
      </label>
      <div className="flex items-center gap-3">
        <button type="submit" className="btn btn-primary">
          {t("common.save")}
        </button>
        {status && <span className="text-sm text-muted">{status}</span>}
      </div>
    </form>
  );
}
