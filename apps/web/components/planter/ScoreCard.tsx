"use client";

import { Sparkles, Loader2 } from "lucide-react";

interface ScoreCardProps {
  status: string;
  logCount: number;
  contributorCount: number;
  progress: number;
  scorePending?: boolean;
}

export function ScoreCard({
  status,
  logCount,
  contributorCount,
  progress,
  scorePending = false,
}: ScoreCardProps) {
  const isLouge = status === "louge";
  const progressPct = Math.min(Math.round(progress * 100), 100);
  const remainingPct = Math.max(100 - progressPct, 0);

  return (
    <div
      className="rounded-lg border border-border bg-bg-card p-5"
      data-testid="score-card"
    >
      <h3 className="mb-4 flex items-center gap-1.5 text-heading-m text-primary-dark">
        <Sparkles size={16} strokeWidth={1.5} className="text-primary" />
        開花まで
      </h3>

      {scorePending && (
        <div
          className="mb-3 flex items-center gap-2 rounded-md bg-primary-light-bg px-3 py-2 text-caption text-primary"
          data-testid="score-pending-indicator"
        >
          <Loader2 size={14} className="animate-spin" />
          スコアを計算中...
        </div>
      )}

      <div className="mb-3">
        <div className="h-[6px] w-full overflow-hidden rounded-xs bg-primary-light-bg">
          <div
            className={`h-[6px] rounded-xs transition-all ${
              isLouge ? "bg-primary" : "bg-primary/50"
            }`}
            style={{ width: `${isLouge ? 100 : progressPct}%` }}
          />
        </div>
        <div className="mt-1 flex items-baseline gap-1.5 text-body-s">
          <span className="font-semibold text-primary">
            {isLouge ? "開花済み" : `${progressPct}%`}
          </span>
          {!isLouge && (
            <span className="text-caption text-text-muted">
              Louge開花まであと{remainingPct}%
            </span>
          )}
        </div>
      </div>

      <div className="my-3 h-px bg-border" />

      <div className="space-y-2.5">
        <ScoreStat label="Log数" value={String(logCount)} />
        <ScoreStat label="貢献者数" value={String(contributorCount)} />
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
