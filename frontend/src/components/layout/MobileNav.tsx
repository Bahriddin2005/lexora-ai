"use client";

import { BookOpenText, Clock3, Home, Languages, Sparkles, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useI18n } from "@/i18n/client";

const ITEMS: Array<{ href: string; key: string; icon: LucideIcon }> = [
  { href: "/", key: "common.home", icon: Home },
  { href: "/dictionary", key: "nav.dictionary", icon: BookOpenText },
  { href: "/translate", key: "nav.translate", icon: Languages },
  { href: "/ai-terms", key: "nav.aiTerms", icon: Sparkles },
  { href: "/new", key: "nav.newWords", icon: Clock3 },
];

export function MobileNav() {
  const pathname = usePathname();
  const { t } = useI18n();

  return (
    <nav className="mobile-dock" aria-label={t("common.menu")}>
      {ITEMS.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        const Icon = item.icon;
        return (
          <Link key={item.href} href={item.href} className={active ? "mobile-dock-item is-active" : "mobile-dock-item"}>
            <Icon aria-hidden className="size-5" />
            <span>{t(item.key)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
