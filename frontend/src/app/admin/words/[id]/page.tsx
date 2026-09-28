import { notFound } from "next/navigation";

import { PageTitle } from "@/components/admin/ui";
import { WordEditor } from "@/components/admin/WordEditor";
import { apiServerOrNull, currentUser } from "@/lib/server-api";
import type { AdminWordDetail } from "@/lib/types";
import { LANGUAGE_FLAGS } from "@/lib/words";

export default async function AdminWordPage({ params }: PageProps<"/admin/words/[id]">) {
  const { id } = await params;
  const [detail, user] = await Promise.all([apiServerOrNull<AdminWordDetail>(`/admin/words/${id}`), currentUser()]);
  if (!detail) notFound();
  return (
    <div>
      <PageTitle>
        {LANGUAGE_FLAGS[detail.entry.language_code]} {detail.entry.lemma}
      </PageTitle>
      {/* key: reset local form state after a save/regenerate refreshes the server data */}
      <WordEditor key={`${detail.entry.id}-${detail.entry.version}`} detail={detail} isAdmin={user?.role === "admin"} />
    </div>
  );
}
