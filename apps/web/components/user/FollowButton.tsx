"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";

interface FollowButtonProps {
  userId: string;
  initialIsFollowing: boolean;
  isOwnProfile?: boolean;
  size?: "sm" | "md";
}

export function FollowButton({
  userId,
  initialIsFollowing,
  isOwnProfile = false,
  size = "md",
}: FollowButtonProps) {
  const { user } = useAuth();
  const router = useRouter();
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);
  const [isLoading, setIsLoading] = useState(false);

  if (isOwnProfile) return null;

  async function handleClick() {
    if (!user) {
      router.push("/login");
      return;
    }

    setIsLoading(true);
    const prev = isFollowing;
    setIsFollowing(!prev);

    try {
      if (prev) {
        await apiFetch(`/api/v1/users/${userId}/follow`, { method: "DELETE" });
      } else {
        await apiFetch(`/api/v1/users/${userId}/follow`, { method: "POST" });
      }
    } catch {
      setIsFollowing(prev);
    } finally {
      setIsLoading(false);
    }
  }

  const sizeClasses =
    size === "sm"
      ? "h-[22px] px-2 text-[10px] rounded"
      : "h-[34px] px-4 text-[13px] rounded-md";

  if (isFollowing) {
    return (
      <button
        onClick={handleClick}
        disabled={isLoading}
        className={`border border-border bg-white font-medium text-primary transition-colors hover:bg-primary-light-bg ${sizeClasses}`}
        data-testid="follow-button"
      >
        フォロー中
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`bg-primary font-bold text-white transition-colors hover:bg-primary-dark ${sizeClasses}`}
      data-testid="follow-button"
    >
      フォロー
    </button>
  );
}
