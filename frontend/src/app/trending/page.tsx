import type { Metadata } from "next";

import { WordList } from "@/components/WordList";
import { getT } from "@/i18n/server";
import { apiServer } from "@/lib/server-api";
import type { WordSummary } from "@/lib/types";

export const metadata: Metadata = { title: "Trending" };

export default async function TrendingPage() {
  const [{ t }, words] = await Promise.all([getT(), apiServer<WordSummary[]>("/trending?limit=50")]);
  return <WordList title={t("lists.trendingTitle")} words={words} />;
}
