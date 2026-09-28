import type { Metadata } from "next";

import { TranslateForm } from "@/components/TranslateForm";
import { getT } from "@/i18n/server";
import { apiServer } from "@/lib/server-api";
import type { Language } from "@/lib/types";

export const metadata: Metadata = { title: "Tarjimon" };

export default async function TranslatePage() {
  const [{ t }, languages] = await Promise.all([getT(), apiServer<Language[]>("/languages")]);
  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <h1 className="text-2xl font-semibold">{t("translate.title")}</h1>
      <TranslateForm languages={languages} />
    </div>
  );
}
