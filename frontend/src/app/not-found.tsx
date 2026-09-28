import Link from "next/link";

import { getT } from "@/i18n/server";

export default async function NotFound() {
  const { t } = await getT();
  return (
    <div className="mx-auto max-w-md px-4 py-24 text-center">
      <h1 className="text-2xl font-semibold">{t("notFound.title")}</h1>
      <Link href="/" className="btn mt-6">
        {t("notFound.home")}
      </Link>
    </div>
  );
}
