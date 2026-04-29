"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { ProgressBar } from "@/components/planter/ProgressBar";
import { formatRelativeTime } from "@/lib/format-time";

interface PlanterSummary {
  id: string;
  title: string;
  status: string;
  log_count: number;
  contributor_count: number;
  created_at: string;
}

interface LogItem {
  id: string;
  body: string;
  created_at: string;
  planter_id: string;
  planter_title: string;
  planter_status: string;
}

const TABS = [
  { key: "seeds", label: "Seed一覧" },
  { key: "logs", label: "Log一覧" },
  { key: "louges", label: "参加Louge" },
] as const;

interface ProfileTabsProps {
  userId: string;
}

export function ProfileTabs({ userId }: ProfileTabsProps) {
  const [activeTab, setActiveTab] = useState<string>("seeds");
  const [planters, setPlanters] = useState<PlanterSummary[]>([]);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(
    async (c: string | null, append: boolean) => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ limit: "20" });
        if (c) params.set("cursor", c);

        if (activeTab === "logs") {
          const data = await apiFetch<{
            logs: LogItem[];
            next_cursor: string | null;
          }>(`/api/v1/users/${userId}/logs?${params.toString()}`);
          setLogs((prev) => (append ? [...prev, ...data.logs] : data.logs));
          setCursor(data.next_cursor);
          setHasMore(data.next_cursor !== null);
        } else {
          params.set("tab", activeTab);
          const data = await apiFetch<{
            planters: PlanterSummary[];
            next_cursor: string | null;
          }>(`/api/v1/users/${userId}/planters?${params.toString()}`);
          setPlanters((prev) =>
            append ? [...prev, ...data.planters] : data.planters,
          );
          setCursor(data.next_cursor);
          setHasMore(data.next_cursor !== null);
        }
      } catch {
        setHasMore(false);
      } finally {
        setLoading(false);
      }
    },
    [userId, activeTab],
  );

  useEffect(() => {
    setPlanters([]);
    setLogs([]);
    setCursor(null);
    setHasMore(true);
    fetchData(null, false);
  }, [activeTab, fetchData]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          fetchData(cursor, true);
        }
      },
      { rootMargin: "200px" },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [cursor, hasMore, loading, fetchData]);

  return (
    <div data-testid="profile-tabs">
      {/* Tab bar */}
      <div className="flex gap-8 border-b border-border">
        {TABS.map((tab) => {
          const isActive = tab.key === activeTab;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`relative pb-2 text-[14px] transition-colors ${
                isActive
                  ? "font-bold text-primary"
                  : "font-normal text-text-muted"
              }`}
              data-testid={`profile-tab-${tab.key}`}
            >
              {tab.label}
              {isActive && (
                <span className="absolute bottom-0 left-0 h-[2px] w-full rounded-full bg-primary" />
              )}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="mt-4">
        {activeTab === "logs"
          ? logs.map((log) => (
              <Link
                key={log.id}
                href={`/p/${log.planter_id}`}
                className="block border-b border-border py-4"
              >
                <p className="mb-1 text-body-s text-text-muted">
                  {log.planter_title}
                </p>
                <p className="text-body-m text-primary-dark line-clamp-2">
                  {log.body}
                </p>
                <p className="mt-1 text-caption text-text-muted">
                  {formatRelativeTime(log.created_at)}
                </p>
              </Link>
            ))
          : planters.map((p) => (
              <Link
                key={p.id}
                href={`/p/${p.id}`}
                className="block border-b border-border py-4"
              >
                <div className="mb-1 flex items-center gap-1.5 text-caption text-text-muted">
                  <span
                    className={`inline-block rounded-sm px-[6px] py-[1px] font-medium ${
                      p.status === "louge"
                        ? "bg-primary text-white"
                        : "bg-primary-light-bg text-primary"
                    }`}
                  >
                    {p.status === "louge"
                      ? "Louge"
                      : p.status === "sprout"
                        ? "Sprout"
                        : "Seed"}
                  </span>
                  <span>{formatRelativeTime(p.created_at)}</span>
                </div>
                <h3 className="text-heading-m text-primary-dark">{p.title}</h3>
                <div className="mt-1 flex items-center justify-between">
                  <div className="flex gap-3 text-body-s text-text-muted">
                    <span>{p.log_count} logs</span>
                    <span>{p.contributor_count} contributors</span>
                  </div>
                </div>
              </Link>
            ))}

        {loading && (
          <div className="py-4 text-center text-body-s text-text-muted">
            読み込み中...
          </div>
        )}

        {!loading &&
          ((activeTab === "logs" && logs.length === 0) ||
            (activeTab !== "logs" && planters.length === 0)) && (
            <div className="py-12 text-center text-body-m text-text-muted">
              {activeTab === "seeds"
                ? "まだSeedを投稿していません"
                : activeTab === "logs"
                  ? "まだLogを投稿していません"
                  : "まだLougeに参加していません"}
            </div>
          )}

        <div ref={sentinelRef} className="h-1" />
      </div>
    </div>
  );
}
