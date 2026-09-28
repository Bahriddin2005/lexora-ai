import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthForm } from "@/components/AuthForm";

export const metadata: Metadata = { title: "Kirish", robots: { index: false } };

export default function LoginPage() {
  return (
    <Suspense>
      <AuthForm mode="login" />
    </Suspense>
  );
}
