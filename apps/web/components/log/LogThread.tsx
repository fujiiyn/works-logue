"use client";

import { useState, useCallback } from "react";
import { Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
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

interface LogListResponse {
  items: LogWithReplies[];
  next_cursor: string | null;
  has_next: boolean;
}

interface LogThreadProps {
  planterId: string;
  onReply?: (logId: string) => void;
}

export function LogThread({ planterId, onReply }: LogThreadProps) {
  const [logs, setLogs] = useState<LogWithReplies[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasNext, setHasNext] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [initialLoaded, setInitialLoaded] = useState(false);

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
          nextCursor ? [...prev, ...data.items] : data.items,
        );
        setCursor(data.next_cursor);
        setHasNext(data.has_next);
      } catch {
        // silently fail
      } finally {
        setIsLoading(false);
        setInitialLoaded(true);
      }
    },
    [planterId],
  );

  // Load initial logs
  useState(() => {
    fetchLogs();
  });

  const addLog = useCallback((newLog: LogWithReplies) => {
    setLogs((prev) => [...prev, newLog]);
  }, []);

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
}

// Export addLog ref helper
export type LogThreadHandle = {
  addLog: (log: LogWithReplies) => void;
  refetch: () => void;
};
