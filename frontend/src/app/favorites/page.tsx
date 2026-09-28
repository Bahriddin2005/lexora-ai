import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { WordCard } from "@/components/WordCard";
import { getT } from "@/i18n/server";
import { apiServerOrNull } from "@/lib/server-api";
import type { WordSummary } from "@/lib/types";

export const metadata: Metadata = { title: "Mening lug‘atim", robots: { index: false } };

export default async function FavoritesPage() {
  const [{ t }, words] = await Promise.all([getT(), apiServerOrNull<WordSummary[]>("/me/favorites")]);
  if (words === null) redirect("/login?next=/favorites");
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">{t("favorites.title")}</h1>
      {words.length === 0 ? (
        <p className="text-muted">{t("favorites.empty")}</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2" data-testid="favorites">
          {words.map((word) => (
            <WordCard key={word.id} word={word} t={t} />
          ))}
        </div>
      )}
    </div>
  );
}
