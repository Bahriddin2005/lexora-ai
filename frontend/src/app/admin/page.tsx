import Link from "next/link";

import { AdminAction } from "@/components/admin/AdminAction";
import { formatDate, PageTitle, Table } from "@/components/admin/ui";
import { apiServer } from "@/lib/server-api";

type Stats = {
  words: { total: number; by_status: Record<string, number>; by_language: Record<string, number> };
  users: number;
  searches_24h: number;
  not_found_24h: number;
  not_found_rate: number;
  open_reports: number;
  ai_calls_7d: number;
  ai_cost_7d: number;
  top_missing: { normalized: string; query: string; language_code: string | null; count: number; last_searched_at: string }[];
};

function Stat({ label, value, href }: { label: string; value: React.ReactNode; href?: string }) {
  const body = (
    <div className="card h-full">
      <div className="text-xs uppercase text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
    </div>
  );
  return href ? <Link href={href}>{body}</Link> : body;
}

export default async function AdminDashboard() {
  const stats = await apiServer<Stats>("/admin/stats");
  const s = stats.words.by_status;
  return (
    <div className="space-y-8">
      <PageTitle>Dashboard</PageTitle>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4" data-testid="admin-stats">
        <Stat label="Jami so‘zlar" value={stats.words.total} href="/admin/words" />
        <Stat label="Nashr qilingan" value={s.published ?? 0} href="/admin/words?status=published" />
        <Stat label="AI / qoralama" value={`${s.ai_generated ?? 0} / ${s.draft ?? 0}`} href="/admin/moderation" />
        <Stat label="Ochiq reportlar" value={stats.open_reports} href="/admin/reports" />
        <Stat label="Qidiruvlar (24 soat)" value={stats.searches_24h} />
        <Stat label="Topilmadi (24 soat)" value={`${stats.not_found_24h} · ${Math.round(stats.not_found_rate * 100)}%`} href="/admin/missing" />
        <Stat label="Foydalanuvchilar" value={stats.users} />
        <Stat label="AI xarajati (7 kun)" value={`$${stats.ai_cost_7d.toFixed(4)}`} href="/admin/ai-usage" />
      </div>

      <section>
        <h2 className="mb-2 font-semibold">Tillar bo‘yicha</h2>
        <p className="text-sm text-muted">
          {Object.entries(stats.words.by_language)
            .map(([lang, count]) => `${lang}: ${count}`)
            .join(" · ") || "—"}
        </p>
      </section>

      <section>
        <h2 className="mb-3 font-semibold">Eng ko‘p qidirilgan, lekin topilmagan so‘zlar</h2>
        <Table head={["So‘rov", "Til", "Soni", "Oxirgi", ""]}>
          {stats.top_missing.map((m) => (
            <tr key={m.normalized}>
              <td className="px-3 py-2 font-medium">{m.query}</td>
              <td className="px-3 py-2">{m.language_code ?? "—"}</td>
              <td className="px-3 py-2 tabular-nums">{m.count}</td>
              <td className="px-3 py-2 text-muted">{formatDate(m.last_searched_at)}</td>
              <td className="px-3 py-2 text-right">
                <AdminAction path="/admin/words/generate" body={{ term: m.query, lang: m.language_code }} label="🤖 Yaratish" job />
              </td>
            </tr>
          ))}
          {stats.top_missing.length === 0 && (
            <tr>
              <td colSpan={5} className="px-3 py-4 text-center text-muted">
                Hammasi topilgan 🎉
              </td>
            </tr>
          )}
        </Table>
      </section>
    </div>
  );
}
