import Link from "next/link";

import type { ContentStatus } from "@/lib/types";

const STATUS_STYLES: Record<ContentStatus, string> = {
  published: "bg-success/15 text-success",
  ai_generated: "bg-warning/15 text-warning",
  draft: "bg-accent/15 text-accent",
  rejected: "bg-danger/15 text-danger",
};

const STATUS_LABELS: Record<ContentStatus, string> = {
  published: "nashr",
  ai_generated: "AI",
  draft: "qoralama",
  rejected: "rad etilgan",
};

export function StatusBadge({ status }: { status: ContentStatus }) {
  return <span className={`badge ${STATUS_STYLES[status]}`}>{STATUS_LABELS[status]}</span>;
}

export function Confidence({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted">—</span>;
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "text-success" : pct >= 60 ? "text-warning" : "text-danger";
  return <span className={`tabular-nums ${color}`}>{pct}%</span>;
}

export function PageTitle({ children, actions }: { children: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-semibold">{children}</h1>
      {actions}
    </div>
  );
}

export function Table({ head, children }: { head: string[]; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full text-left text-sm">
        <thead className="bg-surface text-xs uppercase text-muted">
          <tr>
            {head.map((h) => (
              <th key={h} className="px-3 py-2 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">{children}</tbody>
      </table>
    </div>
  );
}

export function Pagination({ page, size, total, href }: { page: number; size: number; total: number; href: (page: number) => string }) {
  const pages = Math.max(1, Math.ceil(total / size));
  if (pages <= 1) return null;
  return (
    <div className="mt-4 flex items-center gap-2 text-sm">
      {page > 1 && (
        <Link href={href(page - 1)} className="btn">
          ←
        </Link>
      )}
      <span className="text-muted">
        {page} / {pages} · {total}
      </span>
      {page < pages && (
        <Link href={href(page + 1)} className="btn">
          →
        </Link>
      )}
    </div>
  );
}

/** Deterministic UTC "YYYY-MM-DD HH:mm" — identical on the server and in the browser (no hydration mismatch). */
export function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toISOString().slice(0, 16).replace("T", " ");
}
