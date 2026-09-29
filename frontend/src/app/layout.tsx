import type { Metadata } from "next";

import "./globals.css";

import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { MobileNav } from "@/components/layout/MobileNav";
import { I18nProvider } from "@/i18n/client";
import { getLocale } from "@/i18n/server";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: { default: "Lexora AI — Dunyo tillari bitta joyda", template: "%s | Lexora AI" },
  description:
    "AI asosidagi tirik lug‘at: so‘z ma’nolari, talaffuz, kontekstli tarjimalar, misollar va AI izohlar — o‘zbek, ingliz, rus va turk tillarida.",
  openGraph: { siteName: "Lexora AI", type: "website" },
};

// Applies the saved (or system) theme before the first paint. Static string, no user input.
const THEME_SCRIPT = `try{var t=localStorage.getItem('lx_theme');if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.classList.add('dark')}catch(e){}`;

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const locale = await getLocale();
  return (
    <html lang={locale} suppressHydrationWarning className="h-full">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="flex min-h-full flex-col">
        <I18nProvider locale={locale}>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
          <MobileNav />
        </I18nProvider>
      </body>
    </html>
  );
}
