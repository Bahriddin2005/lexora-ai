import { redirect } from "next/navigation";

import { UserControls } from "@/components/admin/InlineEditors";
import { formatDate, PageTitle, Pagination, Table } from "@/components/admin/ui";
import { apiServer, currentUser } from "@/lib/server-api";
import type { Page } from "@/lib/types";

type UserRow = {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  plan: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
};

export default async function UsersPage({ searchParams }: PageProps<"/admin/users">) {
  if ((await currentUser())?.role !== "admin") redirect("/admin");
  const sp = await searchParams;
  const q = (Array.isArray(sp.q) ? sp.q[0] : sp.q) ?? "";
  const page = Number(Array.isArray(sp.page) ? sp.page[0] : sp.page) || 1;
  const data = await apiServer<Page<UserRow>>(`/admin/users?${new URLSearchParams({ q, page: String(page), size: "25" })}`);
  return (
    <div>
      <PageTitle
        actions={
          <form action="/admin/users" className="flex gap-2">
            <input name="q" defaultValue={q} placeholder="Email bo‘yicha" className="input w-52" />
            <button className="btn">Qidirish</button>
          </form>
        }
      >
        Foydalanuvchilar
      </PageTitle>
      <Table head={["Email", "Ism", "Ro‘yxatdan o‘tgan", "Oxirgi kirish", "Rol / tarif / holat"]}>
        {data.items.map((u) => (
          <tr key={u.id}>
            <td className="px-3 py-2 font-medium">{u.email}</td>
            <td className="px-3 py-2">{u.display_name ?? "—"}</td>
            <td className="px-3 py-2 text-muted">{formatDate(u.created_at)}</td>
            <td className="px-3 py-2 text-muted">{formatDate(u.last_login_at)}</td>
            <td className="px-3 py-2">
              <UserControls user={u} />
            </td>
          </tr>
        ))}
      </Table>
      <Pagination page={data.page} size={data.size} total={data.total} href={(p) => `/admin/users?${new URLSearchParams({ q, page: String(p) })}`} />
    </div>
  );
}
