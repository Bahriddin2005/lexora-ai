"use client";

import { Flag, Share2 } from "lucide-react";
import { useRef, useState } from "react";

import { useI18n } from "@/i18n/client";
import { post } from "@/lib/client-api";

const REASONS = ["wrong_translation", "wrong_definition", "wrong_pronunciation", "offensive", "duplicate", "other"];

export function WordActions({ wordId }: { wordId: number }) {
  const { t } = useI18n();
  const [toast, setToast] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [reason, setReason] = useState(REASONS[0]);
  const [comment, setComment] = useState("");

  const flash = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 2500);
  };

  const share = async () => {
    const url = window.location.href;
    try {
      if (navigator.share) await navigator.share({ url, title: document.title });
      else {
        await navigator.clipboard.writeText(url);
        flash(t("word.copied"));
      }
    } catch {
      // share dialog dismissed
    }
  };

  const sendReport = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await post("/reports", { word_id: wordId, reason, comment: comment || null });
      dialogRef.current?.close();
      setComment("");
      flash(t("word.reportSent"));
    } catch {
      flash(t("common.error"));
    }
  };

  return (
    <div className="flex items-center gap-1">
      <button type="button" onClick={() => dialogRef.current?.showModal()} className="btn" title={t("word.report")}>
        <Flag className="size-4" />
        <span className="sr-only">{t("word.report")}</span>
      </button>
      <button type="button" onClick={share} className="btn" title={t("word.share")}>
        <Share2 className="size-4" />
        <span className="sr-only">{t("word.share")}</span>
      </button>

      <dialog ref={dialogRef} className="m-auto w-full max-w-md rounded-xl border border-line bg-bg p-0 text-fg">
        <form onSubmit={sendReport} className="space-y-4 p-5">
          <h2 className="text-lg font-semibold">{t("word.reportTitle")}</h2>
          <label className="block space-y-1 text-sm">
            <span className="text-muted">{t("word.reportReason")}</span>
            <select value={reason} onChange={(e) => setReason(e.target.value)} className="input">
              {REASONS.map((r) => (
                <option key={r} value={r}>
                  {t(`word.reasons.${r}`)}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1 text-sm">
            <span className="text-muted">{t("word.reportComment")}</span>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              maxLength={2000}
              className="input"
            />
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn" onClick={() => dialogRef.current?.close()}>
              {t("common.cancel")}
            </button>
            <button type="submit" className="btn btn-primary">
              {t("common.send")}
            </button>
          </div>
        </form>
      </dialog>

      {toast && (
        <div role="status" className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg bg-fg px-4 py-2 text-sm text-bg shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}
