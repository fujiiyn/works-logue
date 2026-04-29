"use client";

import Link from "next/link";
import { Sprout } from "lucide-react";
import { Skeleton } from "@/components/common/Skeleton";
import { PlanterFollowButton } from "@/components/planter/PlanterFollowButton";
import { LougeCopyButton } from "./LougeCopyButton";

interface Contributor {
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  insight_score_earned: number;
  log_count: number;
  is_seed_author: boolean;
}

interface ContributorsSidebarProps {
  contributors: Contributor[];
  logCount: number;
  contributorCount: number;
  lougeContent: string;
  planterId: string;
  isFollowing: boolean;
  loading?: boolean;
}

function ContributorSkeleton() {
  return (
    <div className="flex items-start gap-2.5">
      <Skeleton className="h-7 w-7 shrink-0 rounded-full" />
      <div className="flex-1 min-w-0">
        <Skeleton className="mb-1 h-3 w-20" />
        <Skeleton className="h-2.5 w-12" />
      </div>
      <Skeleton className="h-3 w-8 shrink-0" />
    </div>
  );
}

export function ContributorsSidebar({
  contributors,
  logCount,
  contributorCount,
  lougeContent,
  planterId,
  isFollowing,
  loading = false,
}: ContributorsSidebarProps) {
  const showSkeleton = loading && contributors.length === 0;

  return (
    <div
      className="rounded-lg border border-border bg-card p-4"
      data-testid="contributors-sidebar"
    >
      <h3 className="mb-3 text-[13px] font-bold text-primary-dark">貢献者</h3>

      <div className="space-y-3">
        {showSkeleton ? (
          <>
            <ContributorSkeleton />
            <ContributorSkeleton />
            <ContributorSkeleton />
          </>
        ) : (
          contributors.map((contributor) => (
            <div key={contributor.user_id} className="flex items-start gap-2.5">
              {/* Avatar */}
              {contributor.avatar_url ? (
                <img
                  src={contributor.avatar_url}
                  alt=""
                  className="h-7 w-7 shrink-0 rounded-full object-cover"
                />
              ) : (
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-light-bg text-[11px] font-medium text-primary">
                  {contributor.display_name.charAt(0)}
                </span>
              )}

              {/* Info */}
              <div className="flex-1 min-w-0">
                <Link
                  href={`/user/${contributor.user_id}`}
                  className="block truncate text-[11px] font-medium text-primary-dark hover:text-primary hover:underline"
                >
                  {contributor.display_name}
                </Link>
                <p className="text-[10px] text-text-muted">
                  {contributor.is_seed_author ? (
                    <span className="inline-flex items-center gap-0.5">
                      <Sprout size={10} strokeWidth={1.5} />
                      Seed投稿
                    </span>
                  ) : (
                    <>{contributor.log_count} logs</>
                  )}
                </p>
              </div>

              {/* Score */}
              <span className="shrink-0 text-[11px] font-bold text-primary">
                {Math.round(contributor.insight_score_earned * 100)}pt
              </span>
            </div>
          ))
        )}
      </div>

      {/* Stats */}
      <div className="mt-3 flex items-center gap-3 rounded-md bg-bg-page px-3 py-2.5">
        <p className="text-[11px] font-bold text-primary-dark">
          {logCount} logs · {contributorCount} contributors
        </p>
        <PlanterFollowButton
          planterId={planterId}
          initialIsFollowing={isFollowing}
        />
      </div>

      {/* Progress bar (100%) */}
      <div className="mt-2 h-1.5 w-full rounded-full bg-border">
        <div className="h-full w-full rounded-full bg-primary" />
      </div>

      {/* Copy button */}
      <div className="mt-3">
        <LougeCopyButton content={lougeContent} />
      </div>
    </div>
  );
}
