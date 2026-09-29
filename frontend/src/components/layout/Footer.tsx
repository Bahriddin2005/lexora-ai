import Link from "next/link";

import { getT } from "@/i18n/server";

export async function Footer() {
  const { t } = await getT();
  return (
    <footer className="mt-16 border-t border-line max-md:hidden">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-6 text-sm text-muted">
        <span>© {new Date().getFullYear()} Lexora AI</span>
        <Link href="/about" className="hover:text-fg">
          {t("nav.about")}
        </Link>
        <a href="https://www.wiktionary.org" className="hover:text-fg" rel="noopener">
          Wiktionary (CC BY-SA 4.0)
        </a>
        <a href="/api/v1/languages" className="hover:text-fg">
          API
        </a>
      </div>
    </footer>
  );
}
