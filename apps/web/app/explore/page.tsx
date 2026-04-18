"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { PlanterCard } from "@/components/planter/PlanterCard";
import { PlanterCardSkeleton } from "@/components/planter/PlanterCardSkeleton";
import { TagAccordionSelector } from "@/components/common/TagAccordionSelector";

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

interface SearchResponse {
  items: PlanterItem[];
  next_cursor: string | null;
}

const STATUS_OPTIONS = [
  { key: "", label: "すべて" },
  { key: "seed", label: "Seed" },
  { key: "sprout", label: "Sprout" },
  { key: "louge", label: "Louge" },
] as const;

export default function ExplorePage() {
  const [keyword, setKeyword] = useState("");
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [showTagFilter, setShowTagFilter] = useState(false);

  const [planters, setPlanters] = useState<PlanterItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [initialLoaded, setInitialLoaded] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const loadingRef = useRef(false);

  // Debounce keyword input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedKeyword(keyword), 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  const fetchResults = useCallback(
    async (currentCursor: string | null, append: boolean) => {
      if (loadingRef.current) return;
      loadingRef.current = true;
      setLoading(true);
      try {
        const params = new URLSearchParams({ limit: "20" });
        if (debouncedKeyword) params.set("keyword", debouncedKeyword);
        if (selectedStatus) params.set("status", selectedStatus);
        if (selectedTagIds.length > 0) {
          selectedTagIds.forEach((id) => params.append("tag_ids", id));
        }
        if (currentCursor) params.set("cursor", currentCursor);

        const data = await apiFetch<SearchResponse>(
          `/api/v1/search?${params.toString()}`,
        );

        setPlanters((prev) =>
          append ? [...prev, ...data.items] : data.items,
        );
        setCursor(data.next_cursor);
        setHasMore(data.next_cursor !== null);
      } catch {
        setHasMore(false);
      } finally {
        setLoading(false);
        loadingRef.current = false;
        setInitialLoaded(true);
      }
    },
    [debouncedKeyword, selectedStatus, selectedTagIds],
  );

  // Re-search on filter change
  useEffect(() => {
    setPlanters([]);
    setCursor(null);
    setHasMore(true);
    setInitialLoaded(false);
    fetchResults(null, false);
  }, [fetchResults]);

  // Infinite scroll
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingRef.current) {
          fetchResults(cursor, true);
        }
      },
      { rootMargin: "200px" },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [cursor, hasMore, fetchResults]);

  const activeFilterCount =
    (selectedStatus ? 1 : 0) + (selectedTagIds.length > 0 ? 1 : 0);

  return (
    <div data-testid="explore-page">
      <h1 className="mb-6 text-heading-m font-bold text-primary-dark">
        探索
      </h1>

      {/* Search bar */}
      <div className="mb-4 flex gap-2">
        <div className="relative flex-1">
          <Search
            size={18}
            strokeWidth={1.5}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
          />
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="キーワードで検索..."
            className="w-full rounded-lg border border-border bg-bg-card py-2.5 pl-10 pr-4 text-body-m text-primary-dark placeholder:text-text-muted focus:border-primary focus:outline-none"
            data-testid="explore-search-input"
          />
          {keyword && (
            <button
              onClick={() => setKeyword("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-primary-dark"
              data-testid="explore-search-clear"
            >
              <X size={16} strokeWidth={1.5} />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowTagFilter((prev) => !prev)}
          className={`flex items-center gap-1.5 rounded-lg border px-3 py-2.5 text-body-s transition-colors ${
            showTagFilter || activeFilterCount > 0
              ? "border-primary bg-primary-light-bg/60 text-primary"
              : "border-border bg-bg-card text-text-secondary hover:border-primary/50"
          }`}
          data-testid="explore-filter-toggle"
        >
          <SlidersHorizontal size={16} strokeWidth={1.5} />
          フィルタ
          {activeFilterCount > 0 && (
            <span className="ml-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] text-white">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* Status filter pills */}
      <div className="mb-4 flex flex-wrap gap-2">
        {STATUS_OPTIONS.map((opt) => {
          const isActive = selectedStatus === opt.key;
          return (
            <button
              key={opt.key}
              onClick={() => setSelectedStatus(opt.key)}
              className={`rounded-full px-4 py-1.5 text-body-s transition-colors ${
                isActive
                  ? "bg-primary text-white"
                  : "border border-border bg-bg-card text-text-secondary hover:border-primary/50"
              }`}
              data-testid={`explore-status-${opt.key || "all"}`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      {/* Tag filter (collapsible) */}
      {showTagFilter && (
        <div
          className="mb-4 rounded-lg border border-border bg-bg-card p-4"
          data-testid="explore-tag-filter"
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-body-s font-semibold text-primary-dark">
              タグで絞り込む
            </span>
            {selectedTagIds.length > 0 && (
              <button
                onClick={() => setSelectedTagIds([])}
                className="text-body-s text-text-muted hover:text-primary"
                data-testid="explore-tag-clear"
              >
                クリア
              </button>
            )}
          </div>
          <TagAccordionSelector
            selectedTagIds={selectedTagIds}
            onTagsChange={setSelectedTagIds}
          />
        </div>
      )}

      {/* Results */}
      {!initialLoaded ? (
        <div>
          {[0, 1, 2, 3, 4].map((i) => (
            <PlanterCardSkeleton key={i} />
          ))}
        </div>
      ) : planters.length === 0 ? (
        <div
          className="flex flex-col items-center py-16 text-center"
          data-testid="explore-empty"
        >
          <Search
            size={48}
            strokeWidth={1}
            className="mb-4 text-text-sage"
          />
          <p className="text-body-m text-text-secondary">
            {debouncedKeyword || selectedStatus || selectedTagIds.length > 0
              ? "条件に一致するSeedが見つかりませんでした。"
              : "まだSeedが投稿されていません。"}
          </p>
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
