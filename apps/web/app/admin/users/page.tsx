"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Lock, Search } from "lucide-react";
import {
  ApiError,
  adminApi,
  type AdminUserItem,
  type AdminUserList,
} from "@/lib/api-client";
import { FilterChipGroup } from "@/components/admin/filter-chip-group";
import { Pagination } from "@/components/admin/pagination";
import { BanUserDialog } from "@/components/admin/ban-user-dialog";
import { UnbanUserDialog } from "@/components/admin/unban-user-dialog";

type StatusFilter = "all" | "normal" | "banned";

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "すべて" },
  { value: "normal", label: "正常" },
  { value: "banned", label: "BAN中" },
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

export default function AdminUsersPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<AdminUserList | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [banTarget, setBanTarget] = useState<AdminUserItem | null>(null);
  const [unbanTarget, setUnbanTarget] = useState<AdminUserItem | null>(null);

  const debouncedQ = useDebounced(q, 300);

  // Reset to page 1 when filters change.
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
      .listUsers({
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

  function applyUpdate(updated: AdminUserItem) {
    setData((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((it) => (it.id === updated.id ? updated : it)),
          }
        : prev,
    );
  }

  return (
    <div>
      <h1 className="text-heading-xl font-semibold text-primary-dark">
        ユーザー管理
      </h1>
      <p className="mt-1 text-body-m text-text-secondary">
        登録ユーザーの確認と BAN 操作を行います
      </p>

      {/* Toolbar */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-bg-card px-4 py-3">
        <div className="flex flex-1 flex-wrap items-center gap-3">
          <label className="relative w-80">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-text-muted" />
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="ユーザー名で検索"
              data-testid="admin-users-search-input"
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

      {/* Table */}
      <div className="mt-6 overflow-hidden rounded-lg border border-border bg-bg-card">
        <table className="w-full">
          <thead className="bg-bg text-left text-body-s text-text-secondary">
            <tr>
              <th className="px-4 py-3 font-semibold">ユーザー</th>
              <th className="px-4 py-3 font-semibold">ロール</th>
              <th className="px-4 py-3 font-semibold">投稿数</th>
              <th className="px-4 py-3 font-semibold">登録日</th>
              <th className="px-4 py-3 font-semibold">ステータス</th>
              <th className="px-4 py-3 text-right font-semibold">操作</th>
            </tr>
          </thead>
          <tbody className="text-body-s">
            {loading && !data ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-12 text-center text-text-muted"
                >
                  読み込み中…
                </td>
              </tr>
            ) : null}
            {error ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-12 text-center text-[#a6322c]"
                >
                  {error}
                </td>
              </tr>
            ) : null}
            {data && data.items.length === 0 && !loading && !error ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-12 text-center text-text-muted"
                >
                  該当するユーザーが見つかりませんでした
                </td>
              </tr>
            ) : null}
            {data?.items.map((u) => (
              <tr
                key={u.id}
                data-testid={`admin-users-row-${u.id}`}
                className={`border-t border-border ${
                  u.is_banned ? "bg-[#fcebea]/30" : ""
                }`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-light-bg text-body-s font-semibold text-primary">
                      {u.display_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-semibold text-primary-dark">
                        {u.display_name}
                        {u.is_self ? (
                          <span className="ml-1 text-text-muted">（自分）</span>
                        ) : null}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {u.role === "admin" ? (
                    <span className="rounded bg-primary-dark/10 px-2 py-0.5 text-caption font-semibold text-primary-dark">
                      Admin
                    </span>
                  ) : (
                    <span className="rounded border border-border px-2 py-0.5 text-caption text-text-secondary">
                      一般
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-primary-dark">
                  Planter {u.planter_count} / Log {u.log_count}
                </td>
                <td className="px-4 py-3 text-text-secondary">
                  {formatDate(u.created_at)}
                </td>
                <td className="px-4 py-3">
                  {u.is_banned ? (
                    <span className="rounded bg-[#fcebea] px-2 py-0.5 text-caption font-semibold text-[#a6322c]">
                      BAN中
                    </span>
                  ) : (
                    <span className="rounded bg-primary-light-bg px-2 py-0.5 text-caption font-semibold text-primary">
                      正常
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {u.is_self || u.role === "admin" ? (
                    <span
                      className="inline-flex h-8 w-9 items-center justify-center rounded border border-border bg-bg text-text-muted"
                      title={u.is_self ? "自分はBANできません" : "Admin はBANできません"}
                    >
                      <Lock className="h-4 w-4" aria-hidden />
                    </span>
                  ) : u.is_banned ? (
                    <button
                      type="button"
                      data-testid={`admin-users-unban-button-${u.id}`}
                      onClick={() => setUnbanTarget(u)}
                      className="rounded bg-primary px-3 py-1.5 text-caption font-semibold text-white hover:opacity-90"
                    >
                      BAN解除
                    </button>
                  ) : (
                    <button
                      type="button"
                      data-testid={`admin-users-ban-button-${u.id}`}
                      onClick={() => setBanTarget(u)}
                      className="rounded border border-[#a6322c] px-3 py-1.5 text-caption font-semibold text-[#a6322c] hover:bg-[#fcebea]"
                    >
                      BAN
                    </button>
                  )}
                </td>
              </tr>
            ))}
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

      <BanUserDialog
        user={banTarget}
        open={!!banTarget}
        onOpenChange={(o) => !o && setBanTarget(null)}
        onBanned={applyUpdate}
      />
      <UnbanUserDialog
        user={unbanTarget}
        open={!!unbanTarget}
        onOpenChange={(o) => !o && setUnbanTarget(null)}
        onUnbanned={applyUpdate}
      />
    </div>
  );
}
