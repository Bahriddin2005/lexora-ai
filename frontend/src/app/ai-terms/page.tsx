import type { Metadata } from "next";

import { WordList } from "@/components/WordList";
import { getT } from "@/i18n/server";
import { apiServer } from "@/lib/server-api";
import type { WordSummary } from "@/lib/types";

export const metadata: Metadata = { title: "AI terminlar" };

export default async function AiTermsPage() {
  const [{ t }, words] = await Promise.all([getT(), apiServer<WordSummary[]>("/ai-terms?limit=50")]);
  return <WordList title={t("lists.aiTermsTitle")} words={words} />;
}
