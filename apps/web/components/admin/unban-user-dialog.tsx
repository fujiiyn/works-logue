"use client";

import { useState } from "react";
import { Dialog } from "@/components/common/dialog";
import { adminApi, type AdminUserItem } from "@/lib/api-client";

interface UnbanUserDialogProps {
  user: AdminUserItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUnbanned: (updated: AdminUserItem) => void;
}

export function UnbanUserDialog({
  user,
  open,
  onOpenChange,
  onUnbanned,
}: UnbanUserDialogProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm() {
    if (!user) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = await adminApi.unbanUser(user.id);
      onUnbanned(updated);
      onOpenChange(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "BAN 解除に失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  if (!user) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={`${user.display_name} の BAN を解除しますか？`}
      description="解除後は通常通り投稿・操作ができるようになります。"
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
            data-testid="admin-unban-dialog-confirm"
            onClick={handleConfirm}
            disabled={submitting}
            className="rounded bg-primary px-4 py-1.5 text-body-s font-semibold text-white disabled:opacity-50"
          >
            {submitting ? "処理中..." : "BAN を解除する"}
          </button>
        </>
      }
    >
      {user.ban_reason ? (
        <p className="text-body-s text-text-secondary">
          BAN 理由: <span className="text-primary-dark">{user.ban_reason}</span>
        </p>
      ) : null}
      {error ? (
        <p className="mt-2 text-body-s text-[#a6322c]">{error}</p>
      ) : null}
    </Dialog>
  );
}
