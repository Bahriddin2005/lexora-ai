import Link from "next/link";

import { PageTitle, Table } from "@/components/admin/ui";
import { apiServer } from "@/lib/server-api";

type Row = { calls: number; errors: number; tokens_in: number; tokens_out: number; cost_usd: number };
type Usage = { days: number; totals: Row; by_agent: (Row & { agent: string; model: string })[]; by_day: (Row & { day: string })[] };

const fmt = (n: number) => n.toLocaleString("en-US");
const usd = (n: number) => `$${n.toFixed(4)}`;

export default async function AiUsagePage({ searchParams }: PageProps<"/admin/ai-usage">) {
  const sp = await searchParams;
  const days = Number(Array.isArray(sp.days) ? sp.days[0] : sp.days) || 30;
  const usage = await apiServer<Usage>(`/admin/ai-usage?days=${days}`);
  const { totals } = usage;
  return (
    <div className="space-y-6">
      <PageTitle
        actions={
          <div className="flex gap-1">
            {[7, 30, 90].map((d) => (
              <Link key={d} href={`/admin/ai-usage?days=${d}`} className={`btn ${d === days ? "border-brand text-brand" : ""}`}>
                {d} kun
              </Link>
            ))}
          </div>
        }
      >
        AI xarajatlari
      </PageTitle>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          ["Chaqiruvlar", fmt(totals.calls)],
          ["Xatolar", `${fmt(totals.errors)}${totals.calls ? ` · ${Math.round((totals.errors / totals.calls) * 100)}%` : ""}`],
          ["Tokenlar (kirish / chiqish)", `${fmt(totals.tokens_in)} / ${fmt(totals.tokens_out)}`],
          ["Xarajat", usd(totals.cost_usd)],
        ].map(([label, value]) => (
          <div key={label} className="card">
            <div className="text-xs uppercase text-muted">{label}</div>
            <div className="mt-1 text-xl font-semibold tabular-nums">{value}</div>
          </div>
        ))}
      </div>
      <section>
        <h2 className="mb-2 font-semibold">Agentlar bo‘yicha</h2>
        <Table head={["Agent", "Model", "Chaqiruv", "Xato", "Token kirish", "Token chiqish", "Xarajat"]}>
          {usage.by_agent.map((r) => (
            <tr key={`${r.agent}-${r.model}`}>
              <td className="px-3 py-2 font-medium">{r.agent}</td>
              <td className="px-3 py-2 text-muted">{r.model}</td>
              <td className="px-3 py-2 tabular-nums">{fmt(r.calls)}</td>
              <td className="px-3 py-2 tabular-nums">{fmt(r.errors)}</td>
              <td className="px-3 py-2 tabular-nums">{fmt(r.tokens_in)}</td>
              <td className="px-3 py-2 tabular-nums">{fmt(r.tokens_out)}</td>
              <td className="px-3 py-2 tabular-nums">{usd(r.cost_usd)}</td>
            </tr>
          ))}
        </Table>
      </section>
      <section>
        <h2 className="mb-2 font-semibold">Kunlar bo‘yicha</h2>
        <Table head={["Kun", "Chaqiruv", "Xato", "Xarajat"]}>
          {usage.by_day.map((r) => (
            <tr key={r.day}>
              <td className="px-3 py-2">{r.day}</td>
              <td className="px-3 py-2 tabular-nums">{fmt(r.calls)}</td>
              <td className="px-3 py-2 tabular-nums">{fmt(r.errors)}</td>
              <td className="px-3 py-2 tabular-nums">{usd(r.cost_usd)}</td>
            </tr>
          ))}
        </Table>
      </section>
    </div>
  );
}
