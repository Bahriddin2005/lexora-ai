"use client";

import { Menu, Moon, Sun, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { SearchBox } from "@/components/SearchBox";
import { useI18n } from "@/i18n/client";
import { LOCALES } from "@/i18n/messages";
import { useDarkMode } from "@/lib/browser-store";
import { patch, post } from "@/lib/client-api";
import type { User } from "@/lib/types";

const NAV = [
  { href: "/translate", key: "nav.translate" },
  { href: "/trending", key: "nav.trending" },
  { href: "/ai-terms", key: "nav.aiTerms" },
  { href: "/new", key: "nav.newWords" },
];

export function Logo({ large = false }: { large?: boolean }) {
  return (
    <span className={`whitespace-nowrap font-semibold tracking-[0.18em] ${large ? "text-4xl sm:text-5xl" : "text-lg"}`}>
      LEXORA<span className="text-brand"> AI</span>
    </span>
  );
}

function ThemeToggle({ label }: { label: string }) {
  const dark = useDarkMode();
  const toggle = () => {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("lx_theme", next ? "dark" : "light");
    } catch {
      // storage unavailable
    }
  };
  return (
    <button type="button" onClick={toggle} aria-label={label} title={label} className="rounded-full p-2 hover:bg-surface">
      {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </button>
  );
}

function LocaleSwitcher({ user }: { user: User | null }) {
  const { locale, t } = useI18n();
  const router = useRouter();
  const change = async (value: string) => {
    document.cookie = `NEXT_LOCALE=${value}; path=/; max-age=31536000; samesite=lax`;
    if (user) await patch("/auth/me", { ui_language: value }).catch(() => undefined);
    router.refresh();
  };
  return (
    <select
      aria-label={t("common.language")}
      value={locale}
      onChange={(e) => change(e.target.value)}
      className="rounded-md border border-line bg-bg px-1.5 py-1 text-xs uppercase"
    >
      {LOCALES.map((code) => (
        <option key={code} value={code}>
          {code.toUpperCase()}
        </option>
      ))}
    </select>
  );
}

export function Header({ user }: { user: User | null }) {
  const { t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const isHome = pathname === "/";
  const isStaff = user?.role === "editor" || user?.role === "admin";

  // Close the mobile menu when a link inside it is followed.
  const closeOnLink = (event: React.MouseEvent) => {
    if ((event.target as HTMLElement).closest("a")) setOpen(false);
  };

  const logout = async () => {
    await post("/auth/logout").catch(() => undefined);
    router.push("/");
    router.refresh();
  };

  const links = (
    <>
      {NAV.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`whitespace-nowrap rounded-md px-2 py-1 hover:bg-surface ${pathname.startsWith(item.href) ? "text-brand" : ""}`}
        >
          {t(item.key)}
        </Link>
      ))}
      {isStaff && (
        <Link href="/admin" className="whitespace-nowrap rounded-md px-2 py-1 hover:bg-surface">
          {t("common.admin")}
        </Link>
      )}
    </>
  );

  const account = user ? (
    <>
      <Link href="/favorites" className="whitespace-nowrap rounded-md px-2 py-1 hover:bg-surface">
        {t("common.favorites")}
      </Link>
      <Link href="/profile" className="max-w-40 truncate whitespace-nowrap rounded-md px-2 py-1 hover:bg-surface" data-testid="profile-link">
        {user.display_name ?? t("common.profile")}
      </Link>
      <button type="button" onClick={logout} className="whitespace-nowrap rounded-md px-2 py-1 text-muted hover:bg-surface">
        {t("common.logout")}
      </button>
    </>
  ) : (
    <Link href={`/login?next=${encodeURIComponent(pathname)}`} className="btn btn-primary whitespace-nowrap">
      {t("common.login")}
    </Link>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4">
        <Link href="/" aria-label="Lexora AI" className="shrink-0">
          <Logo />
        </Link>
        {!isHome && (
          <div className="hidden flex-1 md:block">
            <SearchBox key={pathname} />
          </div>
        )}
        <nav className="ms-auto hidden items-center gap-1 text-sm xl:flex">{links}</nav>
        <div className="ms-auto flex shrink-0 items-center gap-1 text-sm xl:ms-0">
          <ThemeToggle label={t("common.theme")} />
          <LocaleSwitcher user={user} />
          {user ? <div className="hidden items-center gap-1 xl:flex">{account}</div> : account}
          <button
            type="button"
            className="rounded-full p-2 hover:bg-surface xl:hidden"
            aria-label={t("common.menu")}
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>
      {open && (
        <div className="border-t border-line px-4 py-3 xl:hidden" onClick={closeOnLink}>
          {!isHome && (
            <div className="mb-3">
              <SearchBox key={`m-${pathname}`} />
            </div>
          )}
          <nav className="flex flex-col gap-1 text-sm">
            {links}
            {user && account}
          </nav>
        </div>
      )}
    </header>
  );
}
