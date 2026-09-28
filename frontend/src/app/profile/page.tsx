import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ProfileForm } from "@/components/ProfileForm";
import { getT } from "@/i18n/server";
import { apiServer, currentUser } from "@/lib/server-api";

export const metadata: Metadata = { title: "Profil", robots: { index: false } };

type Quota = { plan: string; unlimited: boolean; usage: Record<string, { used: number; limit: number | null }> };

export default async function ProfilePage() {
  const user = await currentUser();
  if (!user) redirect("/login?next=/profile");
  const [{ t }, quota] = await Promise.all([getT(), apiServer<Quota>("/me/quota")]);
  return (
    <div className="mx-auto max-w-xl space-y-6 px-4 py-10">
      <h1 className="text-2xl font-semibold">{t("profile.title")}</h1>
      <div className="card space-y-1 text-sm">
        <p>{user.email}</p>
        <p className="text-muted">
          {t("profile.plan")}: <span className="font-medium uppercase text-fg">{user.plan}</span> · {t("profile.role")}:{" "}
          <span className="font-medium text-fg">{user.role}</span>
        </p>
      </div>
      <ProfileForm user={user} />
      <section className="card space-y-2">
        <h2 className="font-semibold">{t("profile.quota")}</h2>
        <ul className="space-y-1 text-sm">
          {Object.entries(quota.usage).map(([kind, value]) => (
            <li key={kind} className="flex justify-between">
              <span className="text-muted">{t(`quota.${kind}`)}</span>
              <span>
                {value.used} / {value.limit ?? t("profile.unlimited")}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
