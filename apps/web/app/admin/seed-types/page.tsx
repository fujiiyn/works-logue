"use client";

import { useEffect, useState } from "react";
import { Pencil } from "lucide-react";
import { adminApi, type AdminSeedTypeItem } from "@/lib/api-client";
import { FilterChipGroup } from "@/components/admin/filter-chip-group";
import { Switch } from "@/components/common/switch";
import { EditDescriptionDialog } from "@/components/admin/edit-description-dialog";

type StatusFilter = "all" | "active" | "inactive";

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "すべて" },
  { value: "active", label: "公開中" },
  { value: "inactive", label: "非公開" },
];

export default function AdminSeedTypesPage() {
  const [status, setStatus] = useState<StatusFilter>("all");
  const [items, setItems] = useState<AdminSeedTypeItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editTarget, setEditTarget] = useState<AdminSeedTypeItem | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    adminApi
      .listSeedTypes({ status })
      .then((res) => {
        if (active) setItems(res);
      })
      .catch((e: unknown) => {
        if (active)
          setError(e instanceof Error ? e.message : "読み込みに失敗しました");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [status]);

  async function handleToggle(st: AdminSeedTypeItem) {
    // Optimistic flip
    setItems((prev) =>
      prev
        ? prev.map((it) =>
            it.id === st.id ? { ...it, is_active: !it.is_active } : it,
          )
        : prev,
    );
    try {
      const updated = await adminApi.toggleSeedTypeActive(st.id);
      setItems((prev) =>
        prev ? prev.map((it) => (it.id === updated.id ? updated : it)) : prev,
      );
    } catch {
      // Revert on failure
      setItems((prev) =>
        prev
          ? prev.map((it) =>
              it.id === st.id ? { ...it, is_active: st.is_active } : it,
            )
          : prev,
      );
    }
  }

  function applyEdit(updated: AdminSeedTypeItem) {
    setItems((prev) =>
      prev ? prev.map((it) => (it.id === updated.id ? updated : it)) : prev,
    );
  }

  return (
    <div>
      <h1 className="text-heading-xl font-semibold text-primary-dark">
        SeedType マスタ
      </h1>
      <p className="mt-1 text-body-m text-text-secondary">
        Seed の種類の説明・公開状態を管理します。新規追加・並び替え・名称変更は migration で行います。
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-bg-card px-4 py-3">
        <FilterChipGroup
          options={STATUS_OPTIONS}
          value={status}
          onChange={(v) => setStatus(v as StatusFilter)}
          ariaLabel="公開状態フィルター"
        />
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-border bg-bg-card">
        <table className="w-full">
          <thead className="bg-bg text-left text-body-s text-text-secondary">
            <tr>
              <th className="px-4 py-3 font-semibold">並び順</th>
              <th className="px-4 py-3 font-semibold">名称 / slug</th>
              <th className="px-4 py-3 font-semibold">説明</th>
              <th className="px-4 py-3 font-semibold">公開状態</th>
              <th className="px-4 py-3 text-right font-semibold">操作</th>
            </tr>
          </thead>
          <tbody className="text-body-s">
            {loading && !items ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-text-muted">
                  読み込み中…
                </td>
              </tr>
            ) : null}
            {error ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-[#a6322c]">
                  {error}
                </td>
              </tr>
            ) : null}
            {items?.map((st) => (
              <tr
                key={st.id}
                data-testid={`admin-seed-types-row-${st.id}`}
                className="border-t border-border"
              >
                <td className="px-4 py-3 text-text-secondary">
                  {st.sort_order}
                </td>
                <td className="px-4 py-3">
                  <p className="font-semibold text-primary-dark">{st.name}</p>
                  <p className="text-caption text-text-muted">{st.slug}</p>
                </td>
                <td className="max-w-md truncate px-4 py-3 text-primary-dark">
                  {st.description}
                </td>
                <td className="px-4 py-3">
                  <Switch
                    checked={st.is_active}
                    onCheckedChange={() => handleToggle(st)}
                    aria-label={`${st.name} の公開状態`}
                    data-testid={`admin-seed-types-toggle-${st.id}`}
                  />
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    data-testid={`admin-seed-types-edit-${st.id}`}
                    onClick={() => setEditTarget(st)}
                    className="inline-flex items-center gap-1 rounded border border-border bg-white px-3 py-1.5 text-caption font-semibold text-primary-dark hover:bg-bg"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                    説明を編集
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <EditDescriptionDialog
        seedType={editTarget}
        open={!!editTarget}
        onOpenChange={(o) => !o && setEditTarget(null)}
        onSaved={applyEdit}
      />
    </div>
  );
}
