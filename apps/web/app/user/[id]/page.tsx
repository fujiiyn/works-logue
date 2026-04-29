"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api-client";
import { useRightSidebar } from "@/contexts/right-sidebar-context";
import { ProfileHeader } from "@/components/user/ProfileHeader";
import { StatsRow } from "@/components/user/StatsRow";
import { ContributionGraph } from "@/components/user/ContributionGraph";
import { ProfileTabs } from "@/components/user/ProfileTabs";
import { UserProfileSidebar } from "@/components/user/UserProfileSidebar";

interface UserProfileData {
  user: {
    id: string;
    display_name: string;
    headline: string | null;
    bio: string | null;
    avatar_url: string | null;
    cover_url: string | null;
    location: string | null;
    x_url: string | null;
    linkedin_url: string | null;
    wantedly_url: string | null;
    website_url: string | null;
    insight_score: number;
    created_at: string;
  };
  stats: {
    insight_score: number;
    louge_count: number;
    follower_count: number;
    following_count: number;
  };
  tags: { id: string; name: string; category: string }[];
  featured_contribution: {
    planter_id: string;
    planter_title: string;
    planter_status: string;
    total_score: number;
  } | null;
  is_following: boolean;
  is_own_profile: boolean;
}

export default function UserProfilePage() {
  const params = useParams();
  const userId = params.id as string;
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const { setContent } = useRightSidebar();

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    apiFetch<UserProfileData>(`/api/v1/users/${userId}`)
      .then(setProfile)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [userId]);

  // Inject sidebar content for this page; reset on unmount
  useEffect(() => {
    if (!userId) return;
    setContent(<UserProfileSidebar userId={userId} />);
    return () => setContent(null);
  }, [userId, setContent]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-[180px] animate-pulse rounded-xl bg-border" />
        <div className="h-[300px] animate-pulse rounded-xl bg-bg-card" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="py-20 text-center">
        <p className="text-heading-l text-primary-dark">
          ユーザーが見つかりませんでした
        </p>
        <p className="mt-2 text-body-m text-text-muted">
          削除されたか、存在しないユーザーです。
        </p>
      </div>
    );
  }

  return (
    <div data-testid="user-profile-page">
      <div className="space-y-6">
        <ProfileHeader
          user={profile.user}
          tags={profile.tags}
          isFollowing={profile.is_following}
          isOwnProfile={profile.is_own_profile}
        />

        <StatsRow userId={userId} stats={profile.stats} />

        <ContributionGraph userId={userId} />

        {/* Featured Contribution */}
        {profile.featured_contribution && (
          <div className="rounded-lg border border-border bg-bg-card p-4">
            <h3 className="mb-2 text-heading-m text-primary-dark">
              注目の貢献
            </h3>
            <a
              href={`/p/${profile.featured_contribution.planter_id}`}
              className="block hover:text-primary"
            >
              <p className="text-body-m font-medium text-primary-dark">
                {profile.featured_contribution.planter_title}
              </p>
              <p className="mt-1 text-body-s text-primary">
                +{Math.round(profile.featured_contribution.total_score)}pt
                獲得
              </p>
            </a>
          </div>
        )}

        <ProfileTabs userId={userId} />
      </div>
    </div>
  );
}
