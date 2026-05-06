"use client";

// NOTE: This component assumes the planter detail page uses page-level (window)
// scrolling — there is no internal scroll container. The bottom sentinel +
// IntersectionObserver (root: null), the initial scrollIntoView, and the
// prepend-height correction all rely on window being the scroll target. If
// LogThread is ever wrapped in an internal scroll container, the chat-UI
// behaviors here need to be reworked accordingly.

import {
  useState,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  forwardRef,
  useImperativeHandle,
} from "react";
import { Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { supabase } from "@/lib/supabase";
import { LogItem, type LogData } from "./LogItem";

interface LogWithReplies {
  id: string;
  planter_id: string;
  user: { id: string; display_name: string; avatar_url: string | null } | null;
  body: string;
  is_ai_generated: boolean;
  created_at: string;
  replies: LogData[];
}

export interface NewLogPayload {
  id: string;
  planter_id: string;
  user: { id: string; display_name: string; avatar_url: string | null } | null;
  body: string;
  parent_log_id: string | null;
  is_ai_generated: boolean;
  created_at: string;
}

export interface LogThreadHandle {
  addLog: (log: NewLogPayload) => void;
  scrollToBottom: (behavior?: ScrollBehavior) => void;
}

interface LogListResponse {
  items: LogWithReplies[];
  next_cursor: string | null;
  has_next: boolean;
}

export interface RealtimeLogRow {
  id: string;
  planter_id: string;
  user_id: string | null;
  body: string;
  parent_log_id: string | null;
  is_ai_generated: boolean;
  created_at: string;
  deleted_at: string | null;
}

interface UserLite {
  id: string;
  display_name: string;
  avatar_url: string | null;
}

interface LogThreadProps {
  planterId: string;
  onReply?: (logId: string) => void;
  // Fires every time a logs INSERT is delivered via Realtime, including
  // echoes of the user's own post. Used by the parent to flip the
  // "score calculating" indicator on as soon as a new log is committed
  // anywhere — score_pipeline is about to run for it.
  onRealtimeInsert?: (row: RealtimeLogRow) => void;
  // Fires when the bottom sentinel enters/leaves the viewport. The parent
  // uses this to gate the "new messages" jump-to-latest button.
  onAtBottomChange?: (atBottom: boolean) => void;
}

// Final-pass dedupe across the whole tree. Belt-and-suspenders: each insert
// path already checks before appending, but Fast Refresh / Strict Mode can
// briefly run two subscriptions in parallel, and parallel async setLogs
// calls can read the same prev snapshot before either commits. Filtering
// here guarantees the rendered list never has duplicate keys.
function dedupeTree(logs: LogWithReplies[]): LogWithReplies[] {
  const seen = new Set<string>();
  const out: LogWithReplies[] = [];
  for (const l of logs) {
    if (seen.has(l.id)) continue;
    seen.add(l.id);
    const replies: LogData[] = [];
    for (const r of l.replies) {
      if (seen.has(r.id)) continue;
      seen.add(r.id);
      replies.push(r);
    }
    out.push({ ...l, replies });
  }
  return out;
}

export const LogThread = forwardRef<LogThreadHandle, LogThreadProps>(
  function LogThread(
    { planterId, onReply, onRealtimeInsert, onAtBottomChange },
    ref,
  ) {
  const [logs, setLogs] = useState<LogWithReplies[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasNext, setHasNext] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [initialLoaded, setInitialLoaded] = useState(false);
  const [fetchError, setFetchError] = useState(false);
  // Bumped exactly once per successful prepend to drive the height-correction
  // effect. Decoupled from logs.length so unrelated changes (Realtime appends,
  // dedupe-collapsed paginations) cannot trigger or skip a stale correction.
  const [prependTick, setPrependTick] = useState(0);
  const userCacheRef = useRef<Map<string, UserLite>>(new Map());
  const bottomRef = useRef<HTMLDivElement | null>(null);
  // Document scrollHeight captured synchronously, just before setLogs commits a
  // paginated batch. Read once by the prepend-correction layout effect, then
  // cleared. Never set during initial fetches or Realtime inserts.
  const prevHeightRef = useRef<number | null>(null);
  // Initial scrollIntoView: jump to the bottom once after the first batch
  // mounts, then never again from this effect. Re-runs on planterId change.
  const didInitialScrollRef = useRef(false);

  const fetchLogs = useCallback(
    async (nextCursor?: string | null) => {
      setIsLoading(true);
      // Server returns DESC; we reverse to ASC so the rendered list reads
      // oldest → newest top-to-bottom, with the latest log immediately above
      // the composer. Pagination ("load older") prepends earlier batches.
      try {
        const params = new URLSearchParams({ limit: "20", order: "desc" });
        if (nextCursor) params.set("cursor", nextCursor);

        const data = await apiFetch<LogListResponse>(
          `/api/v1/planters/${planterId}/logs?${params}`,
        );
        const ascItems = [...data.items].reverse();

        // Capture height synchronously, AFTER the await resolves but BEFORE
        // setLogs commits the prepend. This window is single-threaded — no
        // Realtime callback can interleave between this read and the setLogs
        // below — so the captured value reflects the pre-prepend layout.
        if (nextCursor && ascItems.length > 0 && typeof window !== "undefined") {
          prevHeightRef.current = document.documentElement.scrollHeight;
        }

        setLogs((prev) =>
          dedupeTree(nextCursor ? [...ascItems, ...prev] : ascItems),
        );
        setCursor(data.next_cursor);
        setHasNext(data.has_next);
        setFetchError(false);

        // Trigger the correction effect even when dedupe collapsed everything,
        // so prevHeightRef is always cleared exactly once per pagination.
        if (nextCursor && ascItems.length > 0) {
          setPrependTick((t) => t + 1);
        }

        // Seed the user cache from initial logs
        for (const item of data.items) {
          if (item.user) userCacheRef.current.set(item.user.id, item.user);
          for (const r of item.replies) {
            if (r.user) userCacheRef.current.set(r.user.id, r.user);
          }
        }
      } catch {
        prevHeightRef.current = null;
        setFetchError(true);
      } finally {
        setIsLoading(false);
        setInitialLoaded(true);
      }
    },
    [planterId],
  );

  // Reset list + initial-scroll guard when navigating between planters so
  // the next planter's first batch lands the viewport at its latest log.
  useEffect(() => {
    didInitialScrollRef.current = false;
    setLogs([]);
    setInitialLoaded(false);
    setHasNext(true);
    setCursor(null);
    setFetchError(false);
    fetchLogs();
  }, [fetchLogs]);

  // Initial jump to the bottom (latest log) after the first batch mounts.
  // Use useLayoutEffect so the user never sees the "scrolled to top" frame.
  // window.scrollTo with the document's max scrollHeight is more reliable
  // than scrollIntoView({block:"end"}) because the sticky composer overlaps
  // the viewport bottom and scrollIntoView's idea of "in view" can stop
  // short. requestAnimationFrame retry covers late-arriving layout shifts.
  useLayoutEffect(() => {
    if (didInitialScrollRef.current) return;
    if (!initialLoaded || logs.length === 0) return;
    if (typeof window === "undefined") return;
    didInitialScrollRef.current = true;
    const jump = () => {
      window.scrollTo({
        top: document.documentElement.scrollHeight,
        behavior: "instant" as ScrollBehavior,
      });
    };
    jump();
    const raf = requestAnimationFrame(jump);
    return () => cancelAnimationFrame(raf);
  }, [initialLoaded, logs.length]);

  // Prepend correction: when fetchLogs prepended older logs, the document
  // scrollHeight grew above the user's viewport. Restore the previous visual
  // position by scrolling down by the height delta. Fires once per
  // successful pagination via prependTick — never on Realtime inserts.
  useLayoutEffect(() => {
    if (prependTick === 0) return;
    const baseline = prevHeightRef.current;
    prevHeightRef.current = null;
    if (baseline === null || typeof window === "undefined") return;
    const delta = document.documentElement.scrollHeight - baseline;
    if (delta > 0) {
      window.scrollBy(0, delta);
    }
  }, [prependTick]);

  // Track whether the bottom sentinel is in view. Drives the parent's
  // jump-to-latest button visibility. The sentinel is rendered
  // unconditionally below so this observer never targets a detached node.
  useEffect(() => {
    const el = bottomRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          onAtBottomChange?.(entry.isIntersecting);
        }
      },
      // root: null = viewport. Positive bottom rootMargin grows the effective
      // viewport downward by ~120px so the sentinel — which sits behind the
      // fixed composer at the very bottom of the page — still counts as
      // intersecting when the user is scrolled to the latest log.
      { root: null, rootMargin: "0px 0px 120px 0px", threshold: 0 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [onAtBottomChange]);

  const fetchUser = useCallback(
    async (userId: string): Promise<UserLite | null> => {
      const cached = userCacheRef.current.get(userId);
      if (cached) return cached;
      try {
        const data = await apiFetch<{ user: UserLite }>(
          `/api/v1/users/${userId}`,
        );
        userCacheRef.current.set(userId, data.user);
        return data.user;
      } catch {
        return null;
      }
    },
    [],
  );

  const handleInsert = useCallback(
    async (row: RealtimeLogRow) => {
      // Skip soft-deleted rows (defensive — RLS already filters)
      if (row.deleted_at) return;

      // Notify parent first — even if this is an echo of the user's own
      // post, the score pipeline is now running. Idempotent on the parent.
      onRealtimeInsert?.(row);

      // Resolve user info (null for AI-generated logs)
      let user: UserLite | null = null;
      if (row.user_id) {
        user = await fetchUser(row.user_id);
      }

      setLogs((prev) => {
        // Fast pre-check (skips a tree walk in the common case)
        if (prev.some((l) => l.id === row.id)) return prev;
        for (const l of prev) {
          if (l.replies.some((r) => r.id === row.id)) return prev;
        }

        let next: LogWithReplies[];
        if (row.parent_log_id) {
          next = prev.map((l) =>
            l.id === row.parent_log_id
              ? {
                  ...l,
                  replies: [
                    ...l.replies,
                    {
                      id: row.id,
                      planter_id: row.planter_id,
                      user,
                      body: row.body,
                      parent_log_id: row.parent_log_id,
                      is_ai_generated: row.is_ai_generated,
                      created_at: row.created_at,
                    },
                  ],
                }
              : l,
          );
        } else {
          next = [
            ...prev,
            {
              id: row.id,
              planter_id: row.planter_id,
              user,
              body: row.body,
              is_ai_generated: row.is_ai_generated,
              created_at: row.created_at,
              replies: [],
            },
          ];
        }
        return dedupeTree(next);
      });
    },
    [fetchUser, onRealtimeInsert],
  );

  // Imperative handle: parent can push the user's own freshly-posted log
  // into the list immediately (before Realtime echoes it back). Dedupe inside
  // setLogs handles the eventual Realtime echo. scrollToBottom is used by
  // the parent's jump-to-latest button and post-submit auto-scroll.
  useImperativeHandle(
    ref,
    () => ({
      scrollToBottom: (behavior: ScrollBehavior = "smooth") => {
        if (typeof window === "undefined") return;
        // window.scrollTo to documentElement.scrollHeight always lands at the
        // absolute end of the page, even when the sticky composer would
        // otherwise shadow scrollIntoView's "in-view" target.
        window.scrollTo({
          top: document.documentElement.scrollHeight,
          behavior,
        });
      },
      addLog: (log: NewLogPayload) => {
        if (log.user) {
          userCacheRef.current.set(log.user.id, log.user);
        }
        setLogs((prev) => {
          if (prev.some((l) => l.id === log.id)) return prev;
          for (const l of prev) {
            if (l.replies.some((r) => r.id === log.id)) return prev;
          }

          let next: LogWithReplies[];
          if (log.parent_log_id) {
            next = prev.map((l) =>
              l.id === log.parent_log_id
                ? {
                    ...l,
                    replies: [
                      ...l.replies,
                      {
                        id: log.id,
                        planter_id: log.planter_id,
                        user: log.user,
                        body: log.body,
                        parent_log_id: log.parent_log_id,
                        is_ai_generated: log.is_ai_generated,
                        created_at: log.created_at,
                      },
                    ],
                  }
                : l,
            );
          } else {
            next = [
              ...prev,
              {
                id: log.id,
                planter_id: log.planter_id,
                user: log.user,
                body: log.body,
                is_ai_generated: log.is_ai_generated,
                created_at: log.created_at,
                replies: [],
              },
            ];
          }
          return dedupeTree(next);
        });
      },
    }),
    [],
  );

  // Supabase Realtime subscription for new logs in this planter
  useEffect(() => {
    const channel = supabase
      .channel(`planter:${planterId}:logs`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "logs",
          filter: `planter_id=eq.${planterId}`,
        },
        (payload) => {
          handleInsert(payload.new as RealtimeLogRow);
        },
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [planterId, handleInsert]);

  // Render once for all states. The bottom sentinel is unconditionally
  // present so the IntersectionObserver target never detaches across
  // loading/empty/error/loaded transitions.
  const showLoading = !initialLoaded && isLoading;
  const showError = initialLoaded && fetchError && logs.length === 0;
  const showEmpty = initialLoaded && !fetchError && logs.length === 0;

  return (
    <div data-testid="log-thread">
      {showLoading && (
        <div className="flex justify-center py-8" data-testid="log-thread-loading">
          <Loader2 size={20} className="animate-spin text-text-muted" />
        </div>
      )}

      {showError && (
        <div
          className="flex flex-col items-center gap-2 py-8 text-body-s text-text-muted"
          data-testid="log-thread-error"
        >
          <p>Logの読み込みに失敗しました</p>
          <button
            onClick={() => fetchLogs()}
            className="text-primary hover:underline"
            data-testid="log-thread-retry"
          >
            再試行
          </button>
        </div>
      )}

      {showEmpty && (
        <p
          className="py-8 text-center text-body-s text-text-muted"
          data-testid="log-thread-empty"
        >
          まだLogがありません
        </p>
      )}

      {logs.map((log) => (
        <div key={log.id}>
          <LogItem
            log={{ ...log, parent_log_id: null }}
            onReply={onReply}
          />
          {log.replies.map((reply) => (
            <LogItem key={reply.id} log={reply} isReply />
          ))}
        </div>
      ))}

      {logs.length > 0 && hasNext && (
        <div className="pt-4 text-center">
          <button
            onClick={() => fetchLogs(cursor)}
            disabled={isLoading}
            className="text-body-s font-medium text-primary hover:underline disabled:opacity-50"
            data-testid="log-thread-load-more"
          >
            {isLoading ? (
              <Loader2 size={14} className="inline animate-spin" />
            ) : (
              "過去のLogを読み込む"
            )}
          </button>
        </div>
      )}

      <div ref={bottomRef} aria-hidden data-testid="log-thread-bottom" />
    </div>
  );
  },
);
