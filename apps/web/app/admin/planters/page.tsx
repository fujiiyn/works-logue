"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Search, Trash2 } from "lucide-react";
import {
  ApiError,
  adminApi,
  type AdminPlanterItem,
  type AdminPlanterList,
} from "@/lib/api-client";
import { FilterChipGroup } from "@/components/admin/filter-chip-group";
import { Pagination } from "@/components/admin/pagination";
import { ArchivePlanterDialog } from "@/components/admin/archive-planter-dialog";
import { RestorePlanterDialog } from "@/components/admin/restore-planter-dialog";
import { DeletePlanterDialog } from "@/components/admin/delete-planter-dialog";

type StatusFilter =
  | "all"
  | "seed"
  | "sprout"
  | "louge"
  | "archived"
  | "deleted";

const STATUS_OPTIONS: { value: StatusFilter; label: string; suffix?: string }[] =
  [
    { value: "all", label: "すべて", suffix: "= フィードに出ているもの" },
    { value: "seed", label: "Seed" },
    { value: "sprout", label: "Sprout" },
    { value: "louge", label: "Louge" },
    { value: "archived", label: "アーカイブ" },
    { value: "deleted", label: "削除済み" },
  ];

const PER_PAGE = 20;

function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function formatDate(iso: string): string {
  return iso.slice(0, 10);
}

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  seed: { label: "Seed", cls: "bg-primary-light-bg text-primary" },
  sprout: { label: "Sprout", cls: "bg-primary-light-bg text-primary" },
  louge: { label: "Louge", cls: "bg-primary-dark/10 text-primary-dark" },
  archived: { label: "アーカイブ", cls: "bg-bg text-text-secondary" },
  deleted: { label: "削除済み", cls: "bg-[#fcebea] text-[#a6322c]" },
};

export default function AdminPlantersPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<AdminPlanterList | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [archiveTarget, setArchiveTarget] = useState<AdminPlanterItem | null>(
    null,
  );
  const [restoreTarget, setRestoreTarget] = useState<AdminPlanterItem | null>(
    null,
  );
  const [deleteTarget, setDeleteTarget] = useState<AdminPlanterItem | null>(
    null,
  );

  const debouncedQ = useDebounced(q, 300);
  const filtersKey = useMemo(
    () => `${debouncedQ}|${status}`,
    [debouncedQ, status],
  );
  const lastFiltersKey = useRef(filtersKey);
  useEffect(() => {
    if (lastFiltersKey.current !== filtersKey) {
      lastFiltersKey.current = filtersKey;
      setPage(1);
    }
  }, [filtersKey]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    adminApi
      .listPlanters({
        q: debouncedQ.trim() || undefined,
        status,
        page,
        per_page: PER_PAGE,
      })
      .then((res) => {
        if (active) setData(res);
      })
      .catch((e: unknown) => {
        if (!active) return;
        if (e instanceof ApiError && e.status === 404) {
          setError("一覧の取得に失敗しました");
        } else {
          setError(e instanceof Error ? e.message : "読み込みに失敗しました");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [debouncedQ, status, page]);

  function applyUpdate(updated: AdminPlanterItem) {
    setData((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((it) =>
              it.id === updated.id ? updated : it,
            ),
          }
        : prev,
    );
  }

  function applyDelete(deleted: AdminPlanterItem) {
    setData((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.filter((it) => it.id !== deleted.id),
            total: Math.max(0, prev.total - 1),
          }
        : prev,
    );
  }

  return (
    <div>
      <h1 className="text-heading-xl font-semibold text-primary-dark">
        Planter 管理
      </h1>
      <p className="mt-1 text-body-m text-text-secondary">
        Planter の確認・アーカイブ・削除を行います
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-bg-card px-4 py-3">
        <div className="flex flex-1 flex-wrap items-center gap-3">
          <label className="relative w-80">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-text-muted" />
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="タイトルで検索"
              className="w-full rounded border border-border bg-bg py-2 pl-8 pr-3 text-body-s text-primary-dark placeholder:text-text-muted"
            />
          </label>
          <FilterChipGroup
            options={STATUS_OPTIONS}
            value={status}
            onChange={(v) => setStatus(v as StatusFilter)}
            ariaLabel="ステータスフィルター"
          />
        </div>
        <span className="text-body-s text-text-secondary">
          {data ? `全 ${data.total} 件` : "—"}
        </span>
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-border bg-bg-card">
        <table className="w-full">
          <thead className="bg-bg text-left text-body-s text-text-secondary">
            <tr>
              <th className="px-4 py-3 font-semibold">タイトル / SeedType</th>
              <th className="px-4 py-3 font-semibold">投稿者</th>
              <th className="px-4 py-3 font-semibold">状態</th>
              <th className="px-4 py-3 font-semibold">Logs</th>
              <th className="px-4 py-3 font-semibold">更新日</th>
              <th className="px-4 py-3 text-right font-semibold">操作</th>
            </tr>
          </thead>
          <tbody className="text-body-s">
            {loading && !data ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-text-muted">
                  読み込み中…
                </td>
              </tr>
            ) : null}
            {error ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-[#a6322c]">
                  {error}
                </td>
              </tr>
            ) : null}
            {data && data.items.length === 0 && !loading && !error ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-text-muted">
                  該当する Planter が見つかりませんでした
                </td>
              </tr>
            ) : null}
            {data?.items.map((p) => {
              const badge =
                p.deleted_at !== null
                  ? STATUS_BADGE.deleted
                  : (STATUS_BADGE[p.status] ?? STATUS_BADGE.seed);
              const isDeleted = p.deleted_at !== null;
              const isArchived = !isDeleted && p.status === "archived";
              return (
                <tr
                  key={p.id}
                  data-testid={`admin-planters-row-${p.id}`}
                  className="border-t border-border"
                >
                  <td className="px-4 py-3">
                    <p className="font-semibold text-primary-dark">{p.title}</p>
                    <p className="text-caption text-text-secondary">
                      {p.seed_type_name}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {p.author.display_name}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded px-2 py-0.5 text-caption font-semibold ${badge.cls}`}
                    >
                      {badge.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-primary-dark">
                    {p.log_count} ({p.contributor_count}人)
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {formatDate(isDeleted ? (p.deleted_at as string) : p.updated_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {isDeleted ? (
                      <span className="inline-flex items-center gap-1 text-text-muted">
                        <Trash2 className="h-4 w-4" /> 削除済み
                      </span>
                    ) : isArchived ? (
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          data-testid={`admin-planters-restore-button-${p.id}`}
                          onClick={() => setRestoreTarget(p)}
                          className="rounded border border-border bg-white px-3 py-1.5 text-caption font-semibold text-primary hover:bg-primary-light-bg"
                        >
                          復元
                        </button>
                        <button
                          type="button"
                          data-testid={`admin-planters-delete-button-${p.id}`}
                          onClick={() => setDeleteTarget(p)}
                          className="rounded border border-[#a6322c] px-3 py-1.5 text-caption font-semibold text-[#a6322c] hover:bg-[#fcebea]"
                        >
                          削除
                        </button>
                      </div>
                    ) : (
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          data-testid={`admin-planters-archive-button-${p.id}`}
                          onClick={() => setArchiveTarget(p)}
                          className="rounded border border-border bg-white px-3 py-1.5 text-caption font-semibold text-primary-dark hover:bg-bg"
                        >
                          アーカイブ
                        </button>
                        <button
                          type="button"
                          data-testid={`admin-planters-delete-button-${p.id}`}
                          onClick={() => setDeleteTarget(p)}
                          className="rounded border border-[#a6322c] px-3 py-1.5 text-caption font-semibold text-[#a6322c] hover:bg-[#fcebea]"
                        >
                          削除
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {data ? (
          <div className="border-t border-border px-4">
            <Pagination
              page={data.page}
              perPage={data.per_page}
              total={data.total}
              onPageChange={setPage}
            />
          </div>
        ) : null}
      </div>

      <ArchivePlanterDialog
        planter={archiveTarget}
        open={!!archiveTarget}
        onOpenChange={(o) => !o && setArchiveTarget(null)}
        onArchived={applyUpdate}
      />
      <RestorePlanterDialog
        planter={restoreTarget}
        open={!!restoreTarget}
        onOpenChange={(o) => !o && setRestoreTarget(null)}
        onRestored={applyUpdate}
      />
      <DeletePlanterDialog
        planter={deleteTarget}
        open={!!deleteTarget}
        onOpenChange={(o) => !o && setDeleteTarget(null)}
        onDeleted={applyDelete}
      />
    </div>
  );
}
