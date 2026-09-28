import type { Metadata } from "next";

import { WordList } from "@/components/WordList";
import { getT } from "@/i18n/server";
import { apiServer } from "@/lib/server-api";
import type { WordSummary } from "@/lib/types";

export const metadata: Metadata = { title: "Yangi so‘zlar" };

export default async function NewWordsPage() {
  const [{ t }, words] = await Promise.all([getT(), apiServer<WordSummary[]>("/new-words?limit=50")]);
  return <WordList title={t("lists.newTitle")} words={words} />;
}
