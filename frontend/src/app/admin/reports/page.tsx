import Link from "next/link";

import { AdminAction } from "@/components/admin/AdminAction";
import { formatDate, PageTitle, Pagination, Table } from "@/components/admin/ui";
import { apiServer } from "@/lib/server-api";
import type { Page } from "@/lib/types";

type ReportRow = {
  id: number;
  word_id: number;
  word_lemma: string;
  word_language: string;
  reason: string;
  comment: string | null;
  status: string;
  user_email: string | null;
  created_at: string;
};

const STATUSES = ["open", "resolved", "rejected"];

export default async function ReportsPage({ searchParams }: PageProps<"/admin/reports">) {
  const sp = await searchParams;
  const status = (Array.isArray(sp.status) ? sp.status[0] : sp.status) || "open";
  const page = Number(Array.isArray(sp.page) ? sp.page[0] : sp.page) || 1;
  const data = await apiServer<Page<ReportRow>>(`/admin/reports?status=${status}&page=${page}&size=25`);
  return (
    <div>
      <PageTitle
        actions={
          <div className="flex gap-1">
            {STATUSES.map((s) => (
              <Link key={s} href={`/admin/reports?status=${s}`} className={`btn ${s === status ? "border-brand text-brand" : ""}`}>
                {s}
              </Link>
            ))}
          </div>
        }
      >
        Reportlar
      </PageTitle>
      <Table head={["So‘z", "Sabab", "Izoh", "Kim", "Qachon", ""]}>
        {data.items.map((r) => (
          <tr key={r.id}>
            <td className="px-3 py-2 font-medium">
              <Link href={`/admin/words/${r.word_id}`} className="link">
                {r.word_lemma}
              </Link>{" "}
              <span className="text-muted">({r.word_language})</span>
            </td>
            <td className="px-3 py-2">{r.reason}</td>
            <td className="max-w-xs px-3 py-2 text-muted">{r.comment ?? "—"}</td>
            <td className="px-3 py-2 text-muted">{r.user_email ?? "anonim"}</td>
            <td className="px-3 py-2 text-muted">{formatDate(r.created_at)}</td>
            <td className="space-x-1 whitespace-nowrap px-3 py-2 text-right">
              {r.status === "open" ? (
                <>
                  <AdminAction method="PATCH" path={`/admin/reports/${r.id}`} body={{ status: "resolved" }} label="Hal qilindi" />
                  <AdminAction method="PATCH" path={`/admin/reports/${r.id}`} body={{ status: "rejected" }} label="Rad" />
                </>
              ) : (
                <AdminAction method="PATCH" path={`/admin/reports/${r.id}`} body={{ status: "open" }} label="Qayta ochish" />
              )}
            </td>
          </tr>
        ))}
        {data.items.length === 0 && (
          <tr>
            <td colSpan={6} className="px-3 py-6 text-center text-muted">
              Report yo‘q
            </td>
          </tr>
        )}
      </Table>
      <Pagination page={data.page} size={data.size} total={data.total} href={(p) => `/admin/reports?status=${status}&page=${p}`} />
    </div>
  );
}
