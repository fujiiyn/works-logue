"use client";

import { useEffect, useState } from "react";
import { Dialog } from "@/components/common/dialog";
import { adminApi, type AdminSeedTypeItem } from "@/lib/api-client";

interface Props {
  seedType: AdminSeedTypeItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: (updated: AdminSeedTypeItem) => void;
}

export function EditDescriptionDialog({
  seedType,
  open,
  onOpenChange,
  onSaved,
}: Props) {
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (seedType) setDescription(seedType.description);
  }, [seedType]);

  async function handleSave() {
    if (!seedType) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = await adminApi.updateSeedTypeDescription(seedType.id, {
        description,
      });
      onSaved(updated);
      onOpenChange(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存に失敗しました");
    } finally {
      setSubmitting(false);
    }
  }

  if (!seedType) return null;

  const trimmedLength = description.trim().length;
  const overLimit = trimmedLength > 1000;
  const tooShort = trimmedLength === 0;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="SeedType の説明を編集"
      description="新規追加・並び替え・名称変更は migration で行います。"
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
            data-testid="admin-edit-description-dialog-save"
            onClick={handleSave}
            disabled={submitting || overLimit || tooShort}
            className="rounded bg-primary px-4 py-1.5 text-body-s font-semibold text-white disabled:opacity-50"
          >
            {submitting ? "保存中..." : "保存"}
          </button>
        </>
      }
    >
      <dl className="grid grid-cols-3 gap-2 text-body-s">
        <dt className="text-text-secondary">名称</dt>
        <dd className="col-span-2 text-primary-dark">{seedType.name}</dd>
        <dt className="text-text-secondary">slug</dt>
        <dd className="col-span-2 text-primary-dark">{seedType.slug}</dd>
        <dt className="text-text-secondary">並び順</dt>
        <dd className="col-span-2 text-primary-dark">{seedType.sort_order}</dd>
      </dl>
      <label className="mt-4 block">
        <span className="text-body-s text-text-secondary">説明（1〜1000 字）</span>
        <textarea
          data-testid="admin-edit-description-dialog-textarea"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={5}
          className="mt-2 w-full rounded border border-border bg-white p-2 text-body-s text-primary-dark"
        />
        <p
          className={`mt-1 text-right text-caption ${
            overLimit ? "text-[#a6322c]" : "text-text-muted"
          }`}
        >
          {trimmedLength} / 1000
        </p>
      </label>
      {error ? (
        <p className="mt-2 text-body-s text-[#a6322c]">{error}</p>
      ) : null}
    </Dialog>
  );
}
