"use client";

import { useState } from "react";
import { Dialog } from "@/components/common/dialog";
import { adminApi, type AdminPlanterItem } from "@/lib/api-client";

interface Props {
  planter: AdminPlanterItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onArchived: (updated: AdminPlanterItem) => void;
}

export function ArchivePlanterDialog({
  planter,
  open,
  onOpenChange,
  onArchived,
}: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm() {
    if (!planter) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = await adminApi.archivePlanter(planter.id);
      onArchived(updated);
      onOpenChange(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "アーカイブに失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  if (!planter) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="この Planter をアーカイブしますか？"
      description="アーカイブされた Planter は公開フィードに表示されなくなります。後から復元できます。"
      footer={
        <>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
            className="rounded border border-border bg-white px-3 py-1.5 text-body-s text-primary-dark hover:bg-bg-card disabled:opacity-50"
          >
            キャンセル
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={submitting}
            className="rounded bg-primary px-4 py-1.5 text-body-s font-semibold text-white disabled:opacity-50"
          >
            {submitting ? "処理中..." : "アーカイブする"}
          </button>
        </>
      }
    >
      <p className="text-body-s text-primary-dark">「{planter.title}」</p>
      {error ? (
        <p className="mt-2 text-body-s text-[#a6322c]">{error}</p>
      ) : null}
    </Dialog>
  );
}
