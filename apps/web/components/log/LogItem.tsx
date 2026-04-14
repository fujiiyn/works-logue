"use client";

import { MessageSquare } from "lucide-react";
import { formatRelativeTime } from "@/lib/format-time";

interface LogUser {
  id: string;
  display_name: string;
  avatar_url: string | null;
}

export interface LogData {
  id: string;
  planter_id: string;
  user: LogUser | null;
  body: string;
  parent_log_id: string | null;
  is_ai_generated: boolean;
  created_at: string;
}

interface LogItemProps {
  log: LogData;
  isReply?: boolean;
  onReply?: (logId: string) => void;
}

export function LogItem({ log, isReply = false, onReply }: LogItemProps) {
  const displayName = log.is_ai_generated
    ? "AI アシスタント"
    : log.user?.display_name ?? "Unknown";

  const avatarContent = log.is_ai_generated ? (
    <img
      src="/works-logue-logo-icon.png"
      alt="AI"
      className="h-7 w-7 rounded-full object-cover"
    />
  ) : log.user?.avatar_url ? (
    <img
      src={log.user.avatar_url}
      alt=""
      className="h-7 w-7 rounded-full object-cover"
    />
  ) : (
    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-light-bg text-[10px] font-medium text-primary">
      {displayName.charAt(0)}
    </span>
  );

  return (
    <div
      className={`flex gap-3 ${isReply ? "ml-10 pt-2" : "pt-3"}`}
      data-testid={isReply ? "log-reply" : "log-item"}
    >
      <div className="shrink-0">{avatarContent}</div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 text-body-s">
          <span
            className={`font-medium ${
              log.is_ai_generated
                ? "text-accent"
                : "text-text-secondary"
            }`}
          >
            {displayName}
          </span>
          <span className="text-text-sage">·</span>
          <span className="text-text-muted">
            {formatRelativeTime(log.created_at)}
          </span>
        </div>
        <p className="mt-1 max-w-[600px] text-[13px] leading-[1.7] text-text-secondary">
          {log.body}
        </p>
        {!isReply && onReply && (
          <button
            onClick={() => onReply(log.id)}
            className="mt-1 flex items-center gap-1 text-caption text-text-muted hover:text-primary"
            data-testid="log-reply-button"
          >
            <MessageSquare size={12} strokeWidth={1.5} />
            返信
          </button>
        )}
      </div>
    </div>
  );
}
