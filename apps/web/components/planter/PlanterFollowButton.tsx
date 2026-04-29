"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";

interface PlanterFollowButtonProps {
  planterId: string;
  initialIsFollowing: boolean;
  size?: "sm" | "md";
}

export function PlanterFollowButton({
  planterId,
  initialIsFollowing,
  size = "sm",
}: PlanterFollowButtonProps) {
  const { user } = useAuth();
  const router = useRouter();
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);
  const [isLoading, setIsLoading] = useState(false);
  const fetchedRef = useRef(false);

  useEffect(() => {
    // Server-side fetch happens without auth headers (is_following always false).
    // Sync once when authenticated user becomes available; never re-run thereafter
    // so optimistic updates aren't overwritten by a stale refetch.
    if (!user || fetchedRef.current) return;
    fetchedRef.current = true;
    apiFetch<{ is_following: boolean }>(`/api/v1/planters/${planterId}`)
      .then((res) => setIsFollowing(res.is_following))
      .catch(() => {});
  }, [user, planterId]);

  async function handleClick() {
    if (!user) {
      router.push("/login");
      return;
    }

    setIsLoading(true);
    const prev = isFollowing;
    setIsFollowing(!prev);

    try {
      const method = prev ? "DELETE" : "POST";
      await apiFetch(`/api/v1/planters/${planterId}/follow`, { method });
    } catch {
      setIsFollowing(prev);
    } finally {
      setIsLoading(false);
    }
  }

  const sizeClasses =
    size === "sm"
      ? "h-[22px] px-2 text-[10px] rounded"
      : "h-[28px] px-3 text-[12px] rounded-md";

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`border border-primary font-medium transition-colors ${sizeClasses} ${
        isFollowing
          ? "bg-primary-light-bg text-primary"
          : "bg-transparent text-primary hover:bg-primary-light-bg"
      }`}
      data-testid="planter-follow-button"
    >
      {isFollowing ? "フォロー中" : "+ フォロー"}
    </button>
  );
}
