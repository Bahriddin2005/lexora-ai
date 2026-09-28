import Link from "next/link";

import { Confidence, formatDate, PageTitle, Pagination, StatusBadge, Table } from "@/components/admin/ui";
import { GenerateForm, NewWordForm } from "@/components/admin/WordForms";
import { apiServer } from "@/lib/server-api";
import type { AdminWordRow, Page } from "@/lib/types";

const param = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value) ?? "";

export default async function AdminWordsPage({ searchParams }: PageProps<"/admin/words">) {
  const sp = await searchParams;
  const filters = { status: param(sp.status), lang: param(sp.lang), q: param(sp.q) };
  const page = Number(param(sp.page)) || 1;
  const query = new URLSearchParams({ page: String(page), size: "25" });
  for (const [key, value] of Object.entries(filters)) if (value) query.set(key, value);
  const data = await apiServer<Page<AdminWordRow>>(`/admin/words?${query}`);
  const href = (p: number) => `/admin/words?${new URLSearchParams({ ...filters, page: String(p) })}`;

  return (
    <div>
      <PageTitle actions={<NewWordForm />}>So‘zlar</PageTitle>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <form className="flex flex-wrap gap-2" action="/admin/words">
          <input name="q" defaultValue={filters.q} placeholder="Qidirish" className="input w-40" />
          <select name="status" defaultValue={filters.status} className="input w-auto" aria-label="Status">
            <option value="">barcha statuslar</option>
            <option value="published">published</option>
            <option value="ai_generated">ai_generated</option>
            <option value="draft">draft</option>
            <option value="rejected">rejected</option>
          </select>
          <select name="lang" defaultValue={filters.lang} className="input w-auto" aria-label="Til">
            <option value="">barcha tillar</option>
            {["en", "uz", "ru", "tr"].map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
          <button className="btn">Filtr</button>
        </form>
        <GenerateForm />
      </div>
      <Table head={["So‘z", "Til", "Turkum", "Status", "Ishonch", "Versiya", "Manba", "Yangilangan"]}>
        {data.items.map((w) => (
          <tr key={w.id} className="hover:bg-surface/60">
            <td className="px-3 py-2 font-medium">
              <Link href={`/admin/words/${w.id}`} className="link">
                {w.lemma}
              </Link>
            </td>
            <td className="px-3 py-2">{w.language_code}</td>
            <td className="px-3 py-2 text-muted">{w.pos.join(", ")}</td>
            <td className="px-3 py-2">
              <StatusBadge status={w.status} />
            </td>
            <td className="px-3 py-2">
              <Confidence value={w.confidence} />
            </td>
            <td className="px-3 py-2 tabular-nums">v{w.version}</td>
            <td className="px-3 py-2 text-muted">{w.source ?? "—"}</td>
            <td className="px-3 py-2 text-muted">{formatDate(w.updated_at)}</td>
          </tr>
        ))}
      </Table>
      <Pagination page={data.page} size={data.size} total={data.total} href={href} />
    </div>
  );
}
