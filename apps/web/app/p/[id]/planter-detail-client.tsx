"use client";

import { useEffect } from "react";
import { MessageSquare, Users, Sparkles } from "lucide-react";
import { formatRelativeTime } from "@/lib/format-time";
import { useRightSidebar } from "@/contexts/right-sidebar-context";

interface PlanterDetail {
  id: string;
  title: string;
  body: string;
  status: string;
  seed_type: { slug: string; name: string };
  user: { id: string; display_name: string; avatar_url: string | null };
  tags: { id: string; name: string; category: string }[];
  log_count: number;
  contributor_count: number;
  progress: number;
  diversity_score: number;
  structure_score: number;
  bloom_threshold: number;
  created_at: string;
}

const STATUS_LABELS: Record<string, string> = {
  seed: "Seed",
  sprout: "Sprout",
  louge: "Louge",
};

export function PlanterDetailClient({
  planter,
}: {
  planter: PlanterDetail;
}) {
  const isLouge = planter.status === "louge";
  const { setContent } = useRightSidebar();

  useEffect(() => {
    setContent(
      <ScoreCard planter={planter} isLouge={isLouge} />,
    );
    return () => setContent(null);
  }, [planter, isLouge, setContent]);

  return (
    <div className="-mb-6 flex min-h-[calc(100vh-3.5rem)] flex-col" data-testid="planter-detail">
      <div className="flex-1">
        {/* Meta row */}
        <div className="mb-3 flex items-center gap-1.5 text-caption text-text-muted">
          <span
            className={`inline-block rounded-sm px-[6px] py-[1px] text-caption font-medium ${
              isLouge
                ? "bg-primary text-white"
                : "bg-primary-light-bg text-primary"
            }`}
          >
            {STATUS_LABELS[planter.status] ?? planter.status}
          </span>
          <span>{planter.seed_type.name}</span>
          <span>·</span>
          {planter.user.avatar_url ? (
            <img
              src={planter.user.avatar_url}
              alt=""
              className="h-4 w-4 rounded-full object-cover"
            />
          ) : (
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary-light-bg text-[9px] text-primary">
              {planter.user.display_name.charAt(0)}
            </span>
          )}
          <span>{planter.user.display_name}</span>
          <span>·</span>
          <span>{formatRelativeTime(planter.created_at)}</span>
        </div>

        {/* Title */}
        <h1
          className="mb-4 text-[18px] font-semibold leading-[1.55] text-primary-dark"
          data-testid="planter-detail-title"
        >
          {planter.title}
        </h1>

        {/* Body */}
        <div className="mb-5 max-w-[700px]">
          <p className="whitespace-pre-wrap text-[14px] leading-[1.7] text-text-secondary">
            {planter.body}
          </p>
        </div>

        {/* Tags */}
        {planter.tags.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-1.5">
            {planter.tags.map((tag) => (
              <span
                key={tag.id}
                className="rounded-sm border border-border px-[8px] py-[3px] text-caption text-text-secondary"
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}

        {/* Stats */}
        <div className="mb-5 flex gap-3 text-body-s text-text-muted">
          <span className="flex items-center gap-1">
            <MessageSquare size={14} strokeWidth={1.5} />
            {planter.log_count} logs
          </span>
          <span className="flex items-center gap-1">
            <Users size={14} strokeWidth={1.5} />
            {planter.contributor_count} contributors
          </span>
        </div>

        {/* Divider */}
        <div className="mb-5 h-px bg-border" />

        {/* Logs section header */}
        <h2 className="mb-4 text-heading-m text-primary-dark">Logs</h2>

        <p className="py-8 text-center text-body-s text-text-muted">
          まだLogがありません
        </p>

      </div>

      {/* Bottom sticky input bar */}
      <div className="sticky bottom-0 z-30 -mx-10 border-t border-border bg-bg-page px-10 py-3">
        <div className="flex items-center gap-3">
          <div className="flex min-h-[40px] flex-1 items-center rounded-lg border border-border bg-white px-3.5 py-2.5 text-[13px] text-text-muted">
            あなたの経験や知恵を共有...
          </div>
          <button
            disabled
            className="rounded-md bg-primary/40 px-5 py-2.5 text-[13px] font-medium text-white"
            data-testid="planter-detail-log-submit"
          >
            Logを投稿
          </button>
        </div>
      </div>
    </div>
  );
}

function ScoreCard({
  planter,
  isLouge,
}: {
  planter: PlanterDetail;
  isLouge: boolean;
}) {
  return (
    <div className="rounded-lg border border-border bg-bg-card p-5">
      <h3 className="mb-4 flex items-center gap-1.5 text-heading-m text-primary-dark">
        <Sparkles size={16} strokeWidth={1.5} className="text-primary" />
        開花スコア
      </h3>

      <div className="mb-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-body-s text-text-secondary">
            構造充足度（条件A）
          </span>
          <span className="text-body-s font-medium text-primary">
            {Math.round((planter.structure_score ?? 0) * 100)}%
          </span>
        </div>
        <div className="h-[6px] w-full rounded-xs bg-primary-light-bg">
          <div
            className={`h-[6px] rounded-xs ${
              isLouge ? "bg-primary" : "bg-primary/50"
            }`}
            style={{
              width: `${Math.min(planter.structure_score ?? 0, 1) * 100}%`,
            }}
          />
        </div>
      </div>

      <div className="space-y-2.5">
        <ScoreStat label="Log数" value={String(planter.log_count)} />
        <ScoreStat
          label="貢献者数"
          value={String(planter.contributor_count)}
        />
        <ScoreStat
          label="多様性"
          value={`${Math.round((planter.diversity_score ?? 0) * 100)}%`}
        />
        <ScoreStat
          label="開花まで"
          value={
            isLouge
              ? "開花済み"
              : `${Math.round((planter.progress ?? 0) * 100)}%`
          }
        />
      </div>
    </div>
  );
}

function ScoreStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-body-s text-text-secondary">{label}</span>
      <span className="text-body-s font-medium text-primary">{value}</span>
    </div>
  );
}
