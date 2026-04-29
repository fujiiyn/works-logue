"use client";

import Link from "next/link";
import { MapPin, ExternalLink } from "lucide-react";
import { InitialAvatar } from "./InitialAvatar";
import { FollowButton } from "./FollowButton";

interface ProfileHeaderProps {
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
  };
  tags: { id: string; name: string; category: string }[];
  isFollowing: boolean;
  isOwnProfile: boolean;
}

export function ProfileHeader({
  user,
  tags,
  isFollowing,
  isOwnProfile,
}: ProfileHeaderProps) {
  if (!user) return null;

  return (
    <div>
      {/* Cover Image */}
      <div className="relative h-[180px] w-full overflow-hidden rounded-xl">
        {user.cover_url ? (
          <img
            src={user.cover_url}
            alt=""
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="h-full w-full bg-gradient-to-r from-[#214740] via-[#2e6157] to-[#387063]">
            <div className="absolute right-[100px] top-[-30px] h-[200px] w-[200px] rounded-full bg-white/5" />
            <div className="absolute right-0 bottom-0 h-[120px] w-[120px] rounded-full bg-white/5" />
            <div className="absolute left-[50px] bottom-0 h-[80px] w-[80px] rounded-full bg-white/5" />
          </div>
        )}
      </div>

      {/* Profile Card */}
      <div className="relative -mt-8 rounded-xl border border-border bg-bg-card p-6 shadow-[0px_2px_12px_0px_rgba(0,0,0,0.06)]">
        {/* Avatar */}
        <div className="absolute -top-12 left-6">
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.display_name}
              className="h-[88px] w-[88px] rounded-full border-4 border-bg-card object-cover"
              data-testid="profile-avatar"
            />
          ) : (
            <div className="rounded-full border-4 border-bg-card">
              <InitialAvatar
                displayName={user.display_name}
                userId={user.id}
                size={88}
              />
            </div>
          )}
        </div>

        {/* Actions (top right) */}
        <div className="flex justify-end gap-2">
          <FollowButton
            userId={user.id}
            initialIsFollowing={isFollowing}
            isOwnProfile={isOwnProfile}
          />
          {isOwnProfile && (
            <Link
              href="/profile/edit"
              className="flex h-[34px] items-center rounded-md border border-border bg-white px-4 text-body-s text-primary transition-colors hover:bg-primary-light-bg"
              data-testid="profile-edit-button"
            >
              編集
            </Link>
          )}
        </div>

        {/* User Info */}
        <div className="mt-4">
          <h1
            className="text-[22px] font-bold text-primary-dark"
            data-testid="profile-display-name"
          >
            {user.display_name}
          </h1>
          {user.headline && (
            <p className="mt-0.5 text-[14px] font-medium text-primary">
              {user.headline}
            </p>
          )}
          {user.bio && (
            <p className="mt-2 text-[13px] leading-relaxed text-text-secondary">
              {user.bio}
            </p>
          )}
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <span
                key={tag.id}
                className="rounded-full border border-border bg-primary-light-bg px-3 py-0.5 text-caption text-primary"
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}

        {/* Location + Social Links */}
        {(user.location || user.x_url || user.linkedin_url || user.wantedly_url || user.website_url) && (
          <div className="mt-3 flex flex-wrap items-center gap-3 text-body-s text-text-secondary">
            {user.location && (
              <span className="flex items-center gap-1">
                <MapPin size={13} strokeWidth={1.5} />
                {user.location}
              </span>
            )}
            {user.x_url && (
              <a
                href={user.x_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
                data-testid="profile-link-x"
              >
                𝕏
              </a>
            )}
            {user.linkedin_url && (
              <a
                href={user.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-primary hover:underline"
                data-testid="profile-link-linkedin"
              >
                in
              </a>
            )}
            {user.wantedly_url && (
              <a
                href={user.wantedly_url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-primary hover:underline"
                data-testid="profile-link-wantedly"
              >
                W
              </a>
            )}
            {user.website_url && (
              <a
                href={user.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
                data-testid="profile-link-website"
              >
                <ExternalLink size={13} strokeWidth={1.5} />
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
