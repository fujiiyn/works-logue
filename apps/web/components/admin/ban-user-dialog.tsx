"use client";

import { useState } from "react";
import { Dialog } from "@/components/common/dialog";
import { adminApi, type AdminUserItem } from "@/lib/api-client";

interface BanUserDialogProps {
  user: AdminUserItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onBanned: (updated: AdminUserItem) => void;
}

export function BanUserDialog({
  user,
  open,
  onOpenChange,
  onBanned,
}: BanUserDialogProps) {
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm() {
    if (!user) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = await adminApi.banUser(user.id, {
        reason: reason.trim() ? reason.trim() : null,
      });
      onBanned(updated);
      onOpenChange(false);
      setReason("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "BAN に失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  if (!user) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={`${user.display_name} を BAN しますか？`}
      description="BAN されたユーザーは投稿・編集・フォロー操作ができなくなります。理由は監査ログに残ります。"
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
            data-testid="admin-ban-dialog-confirm"
            onClick={handleConfirm}
            disabled={submitting}
            className="rounded bg-[#a6322c] px-4 py-1.5 text-body-s font-semibold text-white disabled:opacity-50"
          >
            {submitting ? "処理中..." : "BAN する"}
          </button>
        </>
      }
    >
      <label className="block">
        <span className="text-body-s text-text-secondary">
          BAN 理由（500 文字以内、任意）
        </span>
        <textarea
          data-testid="admin-ban-dialog-reason-input"
          value={reason}
          onChange={(e) => setReason(e.target.value.slice(0, 500))}
          rows={4}
          className="mt-2 w-full rounded border border-border bg-white p-2 text-body-s text-primary-dark"
        />
        <p className="mt-1 text-right text-caption text-text-muted">
          {reason.length} / 500
        </p>
      </label>
      {error ? (
        <p className="mt-2 text-body-s text-[#a6322c]">{error}</p>
      ) : null}
    </Dialog>
  );
}
