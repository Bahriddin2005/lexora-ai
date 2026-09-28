"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { useI18n } from "@/i18n/client";
import { ApiError, post } from "@/lib/client-api";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { t } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawNext = searchParams.get("next") ?? "/";
  const next = rawNext.startsWith("/") && !rawNext.startsWith("//") ? rawNext : "/";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "login") await post("/auth/login", { email, password });
      else await post("/auth/register", { email, password, display_name: name || null });
      router.replace(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("common.error"));
      setLoading(false);
    }
  };

  const other = mode === "login" ? "/register" : "/login";
  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="mb-6 text-center text-2xl font-semibold">
        {mode === "login" ? t("auth.loginTitle") : t("auth.registerTitle")}
      </h1>
      <form onSubmit={submit} className="card space-y-4">
        {mode === "register" && (
          <label className="block space-y-1 text-sm">
            <span>{t("auth.displayName")}</span>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} autoComplete="name" />
          </label>
        )}
        <label className="block space-y-1 text-sm">
          <span>{t("auth.email")}</span>
          <input
            className="input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            name="email"
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span>{t("auth.password")}</span>
          <input
            className="input"
            type="password"
            required
            minLength={mode === "register" ? 8 : 1}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            name="password"
          />
          {mode === "register" && <span className="text-xs text-muted">{t("auth.passwordHint")}</span>}
        </label>
        {error && (
          <p className="text-sm text-danger" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary w-full" disabled={loading}>
          {mode === "login" ? t("common.login") : t("common.register")}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-muted">
        {mode === "login" ? t("auth.noAccount") : t("auth.haveAccount")}{" "}
        <Link href={`${other}?next=${encodeURIComponent(next)}`} className="link">
          {mode === "login" ? t("common.register") : t("common.login")}
        </Link>
      </p>
    </div>
  );
}
