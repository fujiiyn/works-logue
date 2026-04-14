"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Sprout } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { PlanterCard } from "./PlanterCard";
import { PlanterCardSkeleton } from "./PlanterCardSkeleton";

interface PlanterItem {
  id: string;
  title: string;
  status: string;
  seed_type: { slug: string; name: string };
  user: { id: string; display_name: string; avatar_url: string | null };
  tags: { id: string; name: string; category: string }[];
  log_count: number;
  contributor_count: number;
  progress: number;
  created_at: string;
}

interface PlanterListResponse {
  items: PlanterItem[];
  next_cursor: string | null;
}

const TABS = [
  { key: "latest", label: "新着" },
  { key: "popular", label: "人気" },
  { key: "bloomed", label: "開花済み" },
] as const;

export function PlanterFeed() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<string>("latest");
  const [planters, setPlanters] = useState<PlanterItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [initialLoaded, setInitialLoaded] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const fetchPlanters = useCallback(
    async (currentCursor: string | null, append: boolean) => {
      if (loading) return;
      setLoading(true);
      try {
        const params = new URLSearchParams({ limit: "20" });
        if (currentCursor) params.set("cursor", currentCursor);

        const data = await apiFetch<PlanterListResponse>(
          `/api/v1/planters?${params.toString()}`,
        );

        setPlanters((prev) => (append ? [...prev, ...data.items] : data.items));
        setCursor(data.next_cursor);
        setHasMore(data.next_cursor !== null);
      } catch {
        // API not available yet - show empty state
        setHasMore(false);
      } finally {
        setLoading(false);
        setInitialLoaded(true);
      }
    },
    [loading],
  );

  // Initial load
  useEffect(() => {
    fetchPlanters(null, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Intersection Observer for infinite scroll
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          fetchPlanters(cursor, true);
        }
      },
      { rootMargin: "200px" },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [cursor, hasMore, loading, fetchPlanters]);

  return (
    <div data-testid="planter-feed">
      {/* Tabs */}
      <div className="mb-4 flex gap-4 border-b border-border pb-2">
        {TABS.map((tab) => {
          const isActive = tab.key === activeTab;
          const isComingSoon = tab.key !== "latest";

          return (
            <button
              key={tab.key}
              onClick={() => {
                if (!isComingSoon) setActiveTab(tab.key);
              }}
              className={`relative pb-1 text-body-m transition-colors ${
                isActive
                  ? "font-semibold text-primary"
                  : "font-normal text-text-sage"
              } ${isComingSoon ? "cursor-default" : "cursor-pointer"}`}
              data-testid={`planter-feed-tab-${tab.key}`}
              disabled={isComingSoon}
            >
              {tab.label}
              {isComingSoon && (
                <span className="ml-1 text-[10px] text-text-muted">
                  (coming soon)
                </span>
              )}
              {isActive && (
                <span className="absolute bottom-0 left-0 h-[2px] w-full rounded-full bg-primary" />
              )}
            </button>
          );
        })}
      </div>

      {/* Feed */}
      {!initialLoaded ? (
        <div>
          {[0, 1, 2, 3, 4].map((i) => (
            <PlanterCardSkeleton key={i} />
          ))}
        </div>
      ) : planters.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-center">
          <Sprout
            size={48}
            strokeWidth={1}
            className="mb-4 text-text-sage"
          />
          <p className="mb-4 text-body-m text-text-secondary">
            まだSeedが投稿されていません。最初のSeedを蒔いてみましょう。
          </p>
          <button
            onClick={() => router.push("/seed/new")}
            className="rounded-md bg-primary px-4 py-2 text-body-m text-white transition-colors hover:bg-primary-dark"
            data-testid="planter-feed-empty-cta"
          >
            Seedを蒔く
          </button>
        </div>
      ) : (
        <>
          {planters.map((planter) => (
            <PlanterCard key={planter.id} planter={planter} />
          ))}

          {loading && (
            <div>
              <PlanterCardSkeleton />
              <PlanterCardSkeleton />
            </div>
          )}

          <div ref={sentinelRef} className="h-1" />
        </>
      )}
    </div>
  );
}
