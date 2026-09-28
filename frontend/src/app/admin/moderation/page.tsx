import Link from "next/link";

import { AdminAction } from "@/components/admin/AdminAction";
import { Confidence, PageTitle, Pagination, StatusBadge, Table } from "@/components/admin/ui";
import { apiServer } from "@/lib/server-api";
import type { AdminWordRow, Page } from "@/lib/types";

export default async function ModerationPage({ searchParams }: PageProps<"/admin/moderation">) {
  const sp = await searchParams;
  const page = Number(Array.isArray(sp.page) ? sp.page[0] : sp.page) || 1;
  const data = await apiServer<Page<AdminWordRow>>(`/admin/moderation?page=${page}&size=25`);
  return (
    <div>
      <PageTitle>Moderatsiya navbati</PageTitle>
      <p className="mb-4 text-sm text-muted">
        AI yaratgan va qoralama yozuvlar. Saralash: reportlar → talab (30 kunlik qidiruvlar) → past ishonch.
      </p>
      <Table head={["So‘z", "Til", "Status", "Ishonch", "Talab", "Reportlar", ""]}>
        {data.items.map((w) => (
          <tr key={w.id} data-testid="moderation-row">
            <td className="px-3 py-2 font-medium">
              <Link href={`/admin/words/${w.id}`} className="link">
                {w.lemma}
              </Link>
            </td>
            <td className="px-3 py-2">{w.language_code}</td>
            <td className="px-3 py-2">
              <StatusBadge status={w.status} />
            </td>
            <td className="px-3 py-2">
              <Confidence value={w.confidence} />
            </td>
            <td className="px-3 py-2 tabular-nums">{w.demand}</td>
            <td className="px-3 py-2 tabular-nums">{w.open_reports}</td>
            <td className="space-x-1 whitespace-nowrap px-3 py-2 text-right">
              <AdminAction path={`/admin/words/${w.id}/publish`} label="✅ Nashr" testId={`publish-${w.lemma}`} />
              <AdminAction path={`/admin/words/${w.id}/reject`} label="⛔ Rad" />
            </td>
          </tr>
        ))}
        {data.items.length === 0 && (
          <tr>
            <td colSpan={7} className="px-3 py-6 text-center text-muted">
              Navbat bo‘sh 🎉
            </td>
          </tr>
        )}
      </Table>
      <Pagination page={data.page} size={data.size} total={data.total} href={(p) => `/admin/moderation?page=${p}`} />
    </div>
  );
}
