"use client";

import {
  useState,
  useCallback,
  useEffect,
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
}

interface LogListResponse {
  items: LogWithReplies[];
  next_cursor: string | null;
  has_next: boolean;
}

interface RealtimeLogRow {
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
  function LogThread({ planterId, onReply, onRealtimeInsert }, ref) {
  const [logs, setLogs] = useState<LogWithReplies[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasNext, setHasNext] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [initialLoaded, setInitialLoaded] = useState(false);
  const userCacheRef = useRef<Map<string, UserLite>>(new Map());

  const fetchLogs = useCallback(
    async (nextCursor?: string | null) => {
      setIsLoading(true);
      try {
        const params = new URLSearchParams({ limit: "20" });
        if (nextCursor) params.set("cursor", nextCursor);

        const data = await apiFetch<LogListResponse>(
          `/api/v1/planters/${planterId}/logs?${params}`,
        );
        setLogs((prev) =>
          dedupeTree(nextCursor ? [...prev, ...data.items] : data.items),
        );
        setCursor(data.next_cursor);
        setHasNext(data.has_next);

        // Seed the user cache from initial logs
        for (const item of data.items) {
          if (item.user) userCacheRef.current.set(item.user.id, item.user);
          for (const r of item.replies) {
            if (r.user) userCacheRef.current.set(r.user.id, r.user);
          }
        }
      } catch {
        // silently fail
      } finally {
        setIsLoading(false);
        setInitialLoaded(true);
      }
    },
    [planterId],
  );

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

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
  // setLogs handles the eventual Realtime echo.
  useImperativeHandle(
    ref,
    () => ({
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

  if (!initialLoaded && isLoading) {
    return (
      <div className="flex justify-center py-8" data-testid="log-thread-loading">
        <Loader2 size={20} className="animate-spin text-text-muted" />
      </div>
    );
  }

  if (initialLoaded && logs.length === 0) {
    return (
      <p
        className="py-8 text-center text-body-s text-text-muted"
        data-testid="log-thread-empty"
      >
        まだLogがありません
      </p>
    );
  }

  return (
    <div data-testid="log-thread">
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

      {hasNext && (
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
              "もっと読み込む"
            )}
          </button>
        </div>
      )}
    </div>
  );
  },
);
