import type { MetadataRoute } from "next";

import { BACKEND_URL } from "@/lib/server-api";
import { wordHref } from "@/lib/words";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages: MetadataRoute.Sitemap = ["", "/dictionary", "/translate", "/trending", "/new", "/ai-terms", "/about"].map((path) => ({
    url: `${SITE}${path}`,
    changeFrequency: "daily",
  }));
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/sitemap-words?size=45000`, { cache: "no-store" });
    const words: { language_code: string; slug: string; updated_at: string }[] = res.ok ? await res.json() : [];
    return [
      ...pages,
      ...words.map((w) => ({ url: `${SITE}${wordHref(w.language_code, w.slug)}`, lastModified: w.updated_at })),
    ];
  } catch {
    return pages;
  }
}
