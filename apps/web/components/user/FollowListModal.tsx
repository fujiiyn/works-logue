"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { apiFetch } from "@/lib/api-client";
import { InitialAvatar } from "./InitialAvatar";
import { FollowButton } from "./FollowButton";

interface FollowUser {
  id: string;
  display_name: string;
  headline: string | null;
  avatar_url: string | null;
  insight_score: number;
  is_following: boolean;
}

interface FollowListResponse {
  users: FollowUser[];
  next_cursor: string | null;
}

interface FollowListModalProps {
  userId: string;
  type: "followers" | "following";
  onClose: () => void;
}

export function FollowListModal({
  userId,
  type,
  onClose,
}: FollowListModalProps) {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<FollowUser[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const fetchPage = useCallback(
    async (c: string | null) => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ limit: "20" });
        if (c) params.set("cursor", c);
        const data = await apiFetch<FollowListResponse>(
          `/api/v1/users/${userId}/${type}?${params.toString()}`,
        );
        setUsers((prev) => (c ? [...prev, ...data.users] : data.users));
        setCursor(data.next_cursor);
        setHasMore(data.next_cursor !== null);
      } catch {
        setHasMore(false);
      } finally {
        setLoading(false);
      }
    },
    [userId, type],
  );

  useEffect(() => {
    fetchPage(null);
  }, [fetchPage]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          fetchPage(cursor);
        }
      },
      { rootMargin: "100px" },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [cursor, hasMore, loading, fetchPage]);

  // Optimistic unfollow: remove from list (D17)
  function handleUnfollow(targetId: string) {
    setUsers((prev) => prev.filter((u) => u.id !== targetId));
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div
        className="w-full max-w-md rounded-xl border border-border bg-bg-card shadow-lg"
        data-testid="follow-list-modal"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-heading-m text-primary-dark">
            {type === "followers" ? "フォロワー" : "フォロー中"}
          </h2>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-primary-light-bg"
            data-testid="follow-list-modal-close"
          >
            <X size={18} strokeWidth={1.5} />
          </button>
        </div>

        {/* List */}
        <div className="max-h-[60vh] overflow-y-auto p-2">
          {users.map((u) => (
            <div
              key={u.id}
              className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-primary-light-bg"
            >
              <Link href={`/user/${u.id}`} onClick={onClose} className="shrink-0">
                {u.avatar_url ? (
                  <img
                    src={u.avatar_url}
                    alt=""
                    className="h-[22px] w-[22px] rounded-full object-cover"
                  />
                ) : (
                  <InitialAvatar
                    displayName={u.display_name}
                    userId={u.id}
                    size={22}
                  />
                )}
              </Link>
              <Link
                href={`/user/${u.id}`}
                onClick={onClose}
                className="min-w-0 flex-1"
              >
                <p className="truncate text-body-s font-medium text-text-secondary">
                  {u.display_name}
                </p>
              </Link>
              <FollowButton
                userId={u.id}
                initialIsFollowing={u.is_following}
                isOwnProfile={currentUser?.id === u.id}
                size="sm"
              />
            </div>
          ))}

          {loading && (
            <div className="py-4 text-center text-body-s text-text-muted">
              読み込み中...
            </div>
          )}

          {!loading && users.length === 0 && (
            <div className="py-8 text-center text-body-s text-text-muted">
              {type === "followers"
                ? "まだフォロワーがいません"
                : "まだ誰もフォローしていません"}
            </div>
          )}

          <div ref={sentinelRef} className="h-1" />
        </div>
      </div>

      {/* Backdrop */}
      <div className="fixed inset-0 -z-10" onClick={onClose} />
    </div>
  );
}
