"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, api } from "@/lib/client-api";
import type { Job } from "@/lib/types";

type Props = {
  path: string;
  method?: "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  label: React.ReactNode;
  className?: string;
  confirm?: string;
  redirectTo?: string;
  /** For endpoints that return a generation job: poll until it finishes. */
  job?: boolean;
  testId?: string;
};

async function waitForJob(job: Job): Promise<Job> {
  let current = job;
  for (let i = 0; i < 80 && ["queued", "running"].includes(current.status); i++) {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    current = await api<Job>(`/jobs/${job.id}`);
  }
  return current;
}

const JOB_MESSAGES: Record<string, string> = {
  done: "Tayyor",
  draft: "Qoralama yaratildi (moderatsiya navbatida)",
  rejected: "AI yozuvi rad etildi (past ishonch)",
  not_a_word: "Bunday so‘z mavjud emas",
  failed: "AI xatosi",
};

export function AdminAction({ path, method = "POST", body, label, className = "btn", confirm, redirectTo, job, testId }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const run = async () => {
    if (confirm && !window.confirm(confirm)) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await api<unknown>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
      if (job && result) {
        const finished = await waitForJob(result as Job);
        setMessage(JOB_MESSAGES[finished.status] ?? finished.status);
      }
      if (redirectTo) router.push(redirectTo);
      router.refresh();
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <span className="inline-flex items-center gap-2">
      <button type="button" onClick={run} disabled={busy} className={className} data-testid={testId}>
        {busy && <Loader2 className="size-3.5 animate-spin" />}
        {label}
      </button>
      {message && <span className="text-xs text-muted">{message}</span>}
    </span>
  );
}
