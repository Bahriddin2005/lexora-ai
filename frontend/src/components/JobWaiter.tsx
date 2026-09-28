"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useI18n } from "@/i18n/client";
import type { Job } from "@/lib/types";
import { searchHref, wordHref } from "@/lib/words";

const POLL_MS = 1500;
const MAX_POLLS = 80;

export function JobWaiter({ job: initial }: { job: Job }) {
  const { t } = useI18n();
  const router = useRouter();
  const [job, setJob] = useState(initial);

  useEffect(() => {
    let polls = 0;
    let stopped = false;
    const tick = async () => {
      if (stopped) return;
      polls += 1;
      try {
        const res = await fetch(`/api/v1/jobs/${initial.id}`, { cache: "no-store" });
        if (res.ok) {
          const next = (await res.json()) as Job;
          setJob(next);
          if (next.status === "done" && next.word) {
            router.replace(wordHref(next.word.language_code, next.word.slug));
            return;
          }
          if (!["queued", "running"].includes(next.status)) return;
        }
      } catch {
        // retry on next tick
      }
      if (polls < MAX_POLLS) setTimeout(tick, POLL_MS);
      else setJob((j) => ({ ...j, status: "failed" }));
    };
    const timer = setTimeout(tick, 300);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [initial.id, router]);

  if (job.status === "queued" || job.status === "running" || (job.status === "done" && job.word)) {
    return (
      <div className="card flex items-start gap-3 border-accent/40 bg-accent/5" role="status" data-testid="job-waiter">
        <Loader2 className="mt-0.5 size-5 shrink-0 animate-spin text-accent" />
        <div>
          <p className="font-medium">{t("search.aiPreparing")}</p>
          <p className="text-sm text-muted">{t("search.aiPreparingHint")}</p>
        </div>
      </div>
    );
  }

  const message =
    job.status === "draft"
      ? t("search.aiDraft")
      : job.status === "rejected"
        ? t("search.aiRejected")
        : job.status === "not_a_word"
          ? t("search.aiNotAWord")
          : t("search.aiFailed");

  return (
    <div className="card space-y-2" role="status" data-testid="job-result">
      <p>{message}</p>
      {job.suggestions.length > 0 && (
        <p className="flex flex-wrap gap-2 text-sm">
          {job.suggestions.map((s) => (
            <Link key={s} href={searchHref(s)} className="chip hover:border-brand">
              {s}
            </Link>
          ))}
        </p>
      )}
    </div>
  );
}
