import { redirect } from "next/navigation";

import { LanguageControls, NewLanguageForm } from "@/components/admin/InlineEditors";
import { PageTitle, Table } from "@/components/admin/ui";
import { apiServer, currentUser } from "@/lib/server-api";

type LanguageRow = {
  code: string;
  name: string;
  native_name: string;
  script: string;
  direction: string;
  flag: string | null;
  is_active: boolean;
  tts_supported: boolean;
  sort_order: number;
};

export default async function LanguagesPage() {
  if ((await currentUser())?.role !== "admin") redirect("/admin");
  const languages = await apiServer<LanguageRow[]>("/admin/languages");
  return (
    <div className="space-y-6">
      <PageTitle>Tillar</PageTitle>
      <p className="text-sm text-muted">
        Yangi til = shu jadvalga yozuv. Normalizatsiya qoidasi kerak bo‘lsa — backend/app/services/normalization.py (docs/12-roadmap.md).
      </p>
      <Table head={["Kod", "Nomi", "Yozuv", "Yo‘nalish", "Sozlamalar"]}>
        {languages.map((lang) => (
          <tr key={lang.code}>
            <td className="px-3 py-2 font-medium">
              {lang.flag} {lang.code}
            </td>
            <td className="px-3 py-2">
              {lang.name} <span className="text-muted">· {lang.native_name}</span>
            </td>
            <td className="px-3 py-2">{lang.script}</td>
            <td className="px-3 py-2">{lang.direction}</td>
            <td className="px-3 py-2">
              <LanguageControls lang={lang} />
            </td>
          </tr>
        ))}
      </Table>
      <NewLanguageForm />
    </div>
  );
}
