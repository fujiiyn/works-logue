"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { InitialAvatar } from "./InitialAvatar";
import { FollowButton } from "./FollowButton";

interface SimilarUser {
  id: string;
  display_name: string;
  headline: string | null;
  avatar_url: string | null;
  insight_score: number;
  common_tag_count: number;
  is_following: boolean;
}

interface UserProfileSidebarProps {
  userId: string;
}

export function UserProfileSidebar({ userId }: UserProfileSidebarProps) {
  const [similar, setSimilar] = useState<SimilarUser[]>([]);

  useEffect(() => {
    apiFetch<SimilarUser[]>(`/api/v1/users/${userId}/similar`)
      .then(setSimilar)
      .catch(() => {});
  }, [userId]);

  return (
    <div className="space-y-4" data-testid="user-profile-sidebar">
      {/* Badges (placeholder - future feature) */}
      <div className="rounded-lg border border-border bg-bg-card p-4">
        <h3 className="mb-3 text-heading-m text-primary-dark">バッジ</h3>
        <p className="text-body-s text-text-muted">
          バッジは今後のアップデートで追加予定です
        </p>
      </div>

      {/* Similar Users */}
      {similar.length > 0 && (
        <div className="rounded-lg border border-border bg-bg-card p-4">
          <h3 className="mb-3 text-heading-m text-primary-dark">
            似た専門性のユーザー
          </h3>
          <div className="space-y-2.5">
            {similar.map((u) => (
              <div key={u.id} className="flex items-center gap-2.5">
                <Link href={`/user/${u.id}`} className="shrink-0">
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
                  className="min-w-0 flex-1 truncate text-body-s font-medium text-text-secondary"
                >
                  {u.display_name}
                </Link>
                <FollowButton
                  userId={u.id}
                  initialIsFollowing={u.is_following}
                  size="sm"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
