"use client";

import { useState } from "react";
import { FollowListModal } from "./FollowListModal";

interface StatsRowProps {
  userId: string;
  stats: {
    insight_score: number;
    louge_count: number;
    follower_count: number;
    following_count: number;
  };
}

export function StatsRow({ userId, stats }: StatsRowProps) {
  const [modal, setModal] = useState<"followers" | "following" | null>(null);

  const items = [
    { label: "総合スコア", value: `${Math.round(stats.insight_score)}pt` },
    { label: "Louge貢献", value: `${stats.louge_count}件` },
    {
      label: "フォロワー",
      value: `${stats.follower_count}人`,
      onClick: () => setModal("followers"),
    },
    {
      label: "フォロー中",
      value: `${stats.following_count}人`,
      onClick: () => setModal("following"),
    },
  ];

  return (
    <>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4" data-testid="stats-row">
        {items.map((item) => (
          <button
            key={item.label}
            onClick={item.onClick}
            disabled={!item.onClick}
            className={`rounded-lg bg-bg p-3 text-left ${
              item.onClick ? "cursor-pointer hover:bg-primary-light-bg" : "cursor-default"
            }`}
          >
            <p className="text-caption text-text-muted">{item.label}</p>
            <p className="text-[20px] font-bold text-primary">{item.value}</p>
          </button>
        ))}
      </div>

      {modal && (
        <FollowListModal
          userId={userId}
          type={modal}
          onClose={() => setModal(null)}
        />
      )}
    </>
  );
}
