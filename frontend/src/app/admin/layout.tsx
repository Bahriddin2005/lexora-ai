import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { currentUser } from "@/lib/server-api";

export const metadata: Metadata = { title: "Admin", robots: { index: false } };

const NAV = [
  { href: "/admin", label: "Dashboard", admin: false },
  { href: "/admin/moderation", label: "Moderatsiya", admin: false },
  { href: "/admin/words", label: "So‘zlar", admin: false },
  { href: "/admin/reports", label: "Reportlar", admin: false },
  { href: "/admin/missing", label: "Topilmaganlar", admin: false },
  { href: "/admin/ai-usage", label: "AI xarajatlari", admin: false },
  { href: "/admin/users", label: "Foydalanuvchilar", admin: true },
  { href: "/admin/languages", label: "Tillar", admin: true },
];

export default async function AdminLayout({ children }: LayoutProps<"/admin">) {
  const user = await currentUser();
  if (!user) redirect("/login?next=/admin");
  if (user.role === "user") {
    return (
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <h1 className="text-xl font-semibold">Ruxsat yo‘q</h1>
        <p className="mt-2 text-muted">Admin panel faqat muharrir va administratorlar uchun.</p>
      </div>
    );
  }
  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 md:flex-row">
      <aside className="md:w-52 md:shrink-0">
        <nav className="flex gap-1 overflow-x-auto text-sm md:sticky md:top-20 md:flex-col">
          {NAV.filter((item) => !item.admin || user.role === "admin").map((item) => (
            <Link key={item.href} href={item.href} className="whitespace-nowrap rounded-md px-3 py-2 hover:bg-surface">
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
