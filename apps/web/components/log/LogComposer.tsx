"use client";

import { useState, useRef, useCallback } from "react";
import { X } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { apiFetch } from "@/lib/api-client";
import Link from "next/link";

interface LogCreateResponse {
  log: {
    id: string;
    planter_id: string;
    user: { id: string; display_name: string; avatar_url: string | null } | null;
    body: string;
    parent_log_id: string | null;
    is_ai_generated: boolean;
    created_at: string;
  };
  planter: {
    id: string;
    status: string;
    log_count: number;
    contributor_count: number;
    progress: number;
    structure_fulfillment: number;
    maturity_score: number | null;
    structure_parts: {
      context: boolean;
      problem: boolean;
      solution: boolean;
      name: boolean;
    } | null;
  };
  score_pending: boolean;
}

interface LogComposerProps {
  planterId: string;
  planterStatus: string;
  replyTo: { id: string; displayName: string } | null;
  onCancelReply: () => void;
  onLogCreated: (response: LogCreateResponse) => void;
}

export function LogComposer({
  planterId,
  planterStatus,
  replyTo,
  onCancelReply,
  onLogCreated,
}: LogComposerProps) {
  const { user } = useAuth();
  const [body, setBody] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInput = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxHeight = 5 * 24; // 5 lines approx
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, []);

  // Hide for louge status (after all hooks)
  if (planterStatus === "louge") return null;

  const handleSubmit = async () => {
    const trimmed = body.trim();
    if (!trimmed || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const payload: { body: string; parent_log_id?: string } = {
        body: trimmed,
      };
      if (replyTo) {
        payload.parent_log_id = replyTo.id;
      }

      const response = await apiFetch<LogCreateResponse>(
        `/api/v1/planters/${planterId}/logs`,
        { method: "POST", body: JSON.stringify(payload) },
      );

      setBody("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
      onCancelReply();
      onLogCreated(response);
    } catch {
      // TODO: error toast
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Not logged in
  if (!user) {
    return (
      <div
        className="sticky bottom-0 z-30 -mx-10 border-t border-border bg-bg-page px-10 py-3"
        data-testid="log-composer-login"
      >
        <div className="flex items-center justify-center gap-2">
          <Link
            href="/login"
            className="rounded-md bg-primary px-5 py-2.5 text-[13px] font-medium text-white hover:bg-primary/90"
          >
            ログインして参加する
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      className="sticky bottom-0 z-30 -mx-10 border-t border-border bg-bg-page px-10 py-3"
      data-testid="log-composer"
    >
      {/* Reply indicator */}
      {replyTo && (
        <div className="mb-2 flex items-center gap-2 text-caption text-text-muted">
          <span>
            {replyTo.displayName} に返信中
          </span>
          <button
            onClick={onCancelReply}
            className="hover:text-primary"
            data-testid="log-composer-cancel-reply"
          >
            <X size={14} />
          </button>
        </div>
      )}

      <div className="flex items-end gap-3">
        <textarea
          ref={textareaRef}
          value={body}
          onChange={(e) => {
            setBody(e.target.value);
            handleInput();
          }}
          onKeyDown={handleKeyDown}
          placeholder="あなたの経験や知恵を共有..."
          rows={1}
          className="min-h-[40px] max-h-[120px] flex-1 resize-none overflow-y-auto rounded-lg border border-border bg-white px-3.5 py-2.5 text-[13px] text-primary-dark placeholder:text-text-muted focus:border-primary focus:outline-none [&::-webkit-scrollbar]:w-[2px] [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-track]:my-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-text-muted/40 hover:[&::-webkit-scrollbar-thumb]:bg-text-muted [scrollbar-width:thin] [scrollbar-color:rgba(153,153,143,0.4)_transparent]"
          data-testid="log-composer-input"
        />
        <button
          onClick={handleSubmit}
          disabled={!body.trim() || isSubmitting}
          className="rounded-md bg-primary px-5 py-2.5 text-[13px] font-medium text-white hover:bg-primary/90 disabled:bg-primary/40 disabled:cursor-not-allowed"
          data-testid="log-composer-submit"
        >
          Logを投稿
        </button>
      </div>
    </div>
  );
}
