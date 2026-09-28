import { AdminAction } from "@/components/admin/AdminAction";
import { formatDate, PageTitle, Table } from "@/components/admin/ui";
import { apiServer } from "@/lib/server-api";

type Missing = { normalized: string; query: string; language_code: string | null; count: number; last_searched_at: string };

export default async function MissingPage({ searchParams }: PageProps<"/admin/missing">) {
  const sp = await searchParams;
  const days = Number(Array.isArray(sp.days) ? sp.days[0] : sp.days) || 30;
  const rows = await apiServer<Missing[]>(`/admin/missing-words?days=${days}&limit=200`);
  return (
    <div>
      <PageTitle>Topilmagan so‘zlar ({days} kun)</PageTitle>
      <p className="mb-4 text-sm text-muted">
        Foydalanuvchilar qidirgan, lekin lug‘atda hali yo‘q so‘zlar — Live Words’ning eng qimmatli signali.
      </p>
      <Table head={["So‘rov", "Kalit", "Til", "Soni", "Oxirgi", ""]}>
        {rows.map((m) => (
          <tr key={m.normalized}>
            <td className="px-3 py-2 font-medium">{m.query}</td>
            <td className="px-3 py-2 text-muted">{m.normalized}</td>
            <td className="px-3 py-2">{m.language_code ?? "—"}</td>
            <td className="px-3 py-2 tabular-nums">{m.count}</td>
            <td className="px-3 py-2 text-muted">{formatDate(m.last_searched_at)}</td>
            <td className="px-3 py-2 text-right">
              <AdminAction path="/admin/words/generate" body={{ term: m.query, lang: m.language_code }} label="🤖 Yaratish" job />
            </td>
          </tr>
        ))}
        {rows.length === 0 && (
          <tr>
            <td colSpan={6} className="px-3 py-6 text-center text-muted">
              Topilmagan so‘z yo‘q
            </td>
          </tr>
        )}
      </Table>
    </div>
  );
}
