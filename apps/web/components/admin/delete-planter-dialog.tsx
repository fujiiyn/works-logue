"use client";

import { useState } from "react";
import { Dialog } from "@/components/common/dialog";
import { adminApi, type AdminPlanterItem } from "@/lib/api-client";

interface Props {
  planter: AdminPlanterItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeleted: (planter: AdminPlanterItem) => void;
}

export function DeletePlanterDialog({
  planter,
  open,
  onOpenChange,
  onDeleted,
}: Props) {
  const [confirmInput, setConfirmInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // BR-A12 D7: trim BOTH sides, then strict (case-sensitive) equality.
  const matched =
    !!planter && confirmInput.trim() === planter.title.trim();

  async function handleConfirm() {
    if (!planter || !matched) return;
    setSubmitting(true);
    setError(null);
    try {
      await adminApi.deletePlanter(planter.id, { confirm_title: confirmInput });
      onDeleted(planter);
      onOpenChange(false);
      setConfirmInput("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "削除に失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  if (!planter) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) setConfirmInput("");
        onOpenChange(o);
      }}
      title="この Planter を削除しますか？"
      description="この操作は取り消せません。確認のため Planter のタイトルを正確に入力してください。"
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
            data-testid="admin-delete-planter-dialog-confirm"
            onClick={handleConfirm}
            disabled={!matched || submitting}
            className="rounded bg-[#a6322c] px-4 py-1.5 text-body-s font-semibold text-white disabled:opacity-50"
          >
            {submitting ? "処理中..." : "削除する"}
          </button>
        </>
      }
    >
      <p className="text-body-s text-primary-dark">
        対象: 「{planter.title}」
      </p>
      <p className="mt-2 text-caption font-semibold text-[#a6322c]">
        この操作は取り消せません
      </p>
      <label className="mt-3 block">
        <span className="text-body-s text-text-secondary">
          確認: 上のタイトルを入力
        </span>
        <input
          type="text"
          data-testid="admin-delete-planter-dialog-confirm-input"
          value={confirmInput}
          onChange={(e) => setConfirmInput(e.target.value)}
          className="mt-2 w-full rounded border border-border bg-white p-2 text-body-s text-primary-dark"
        />
      </label>
      {error ? (
        <p className="mt-2 text-body-s text-[#a6322c]">{error}</p>
      ) : null}
    </Dialog>
  );
}
