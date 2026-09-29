"use client";

import { Menu, Moon, Sun, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { SearchBox } from "@/components/SearchBox";
import { useI18n } from "@/i18n/client";
import { LOCALES } from "@/i18n/messages";
import { useDarkMode } from "@/lib/browser-store";

const NAV = [
  { href: "/dictionary", key: "nav.dictionary" },
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

function LocaleSwitcher() {
  const { locale, t } = useI18n();
  const router = useRouter();
  const change = async (value: string) => {
    document.cookie = `NEXT_LOCALE=${value}; path=/; max-age=31536000; samesite=lax`;
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

export function Header() {
  const { t } = useI18n();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const isHome = pathname === "/";

  // Close the mobile menu when a link inside it is followed.
  const closeOnLink = (event: React.MouseEvent) => {
    if ((event.target as HTMLElement).closest("a")) setOpen(false);
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
    </>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4 max-sm:h-16">
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
          <LocaleSwitcher />
          <button
            type="button"
            className="hidden rounded-full p-2 hover:bg-surface md:block xl:hidden"
            aria-label={t("common.menu")}
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>
      {open && (
        <div className="hidden border-t border-line px-4 py-3 md:block xl:hidden" onClick={closeOnLink}>
          {!isHome && (
            <div className="mb-3">
              <SearchBox key={`m-${pathname}`} />
            </div>
          )}
          <nav className="flex flex-col gap-1 text-sm">
            {links}
          </nav>
        </div>
      )}
    </header>
  );
}
