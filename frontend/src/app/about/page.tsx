import type { Metadata } from "next";

import { getT } from "@/i18n/server";

export const metadata: Metadata = { title: "Loyiha haqida" };

export default async function AboutPage() {
  const { t } = await getT();
  return (
    <div className="mx-auto max-w-2xl space-y-4 px-4 py-10 leading-relaxed">
      <h1 className="text-2xl font-semibold">{t("about.title")}</h1>
      <p>{t("about.body1")}</p>
      <p>{t("about.body2")}</p>
      <h2 className="pt-4 text-lg font-semibold">{t("about.sources")}</h2>
      <ul className="list-disc space-y-1 ps-5 text-muted">
        <li>
          <a href="https://www.wiktionary.org" className="link" rel="noopener">
            Wiktionary
          </a>{" "}
          — {t("about.wiktionary")}
        </li>
        <li>{t("about.gemini")}</li>
      </ul>
    </div>
  );
}
