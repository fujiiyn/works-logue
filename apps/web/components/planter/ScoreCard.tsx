"use client";

import { Sparkles, Loader2, Check, Circle } from "lucide-react";

interface StructureParts {
  context: boolean;
  problem: boolean;
  solution: boolean;
  name: boolean;
}

interface ScoreCardProps {
  status: string;
  structureFulfillment: number;
  maturityScore: number | null;
  logCount: number;
  contributorCount: number;
  progress: number;
  bloomThreshold: number;
  structureParts: StructureParts | null;
  scorePending?: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  seed: "Seed",
  sprout: "Sprout",
  louge: "Louge",
};

const STRUCTURE_PART_LABELS: { key: keyof StructureParts; label: string }[] = [
  { key: "context", label: "Context" },
  { key: "problem", label: "Problem" },
  { key: "solution", label: "Solution" },
  { key: "name", label: "Name" },
];

export function ScoreCard({
  status,
  structureFulfillment,
  maturityScore,
  logCount,
  contributorCount,
  progress,
  bloomThreshold,
  structureParts,
  scorePending = false,
}: ScoreCardProps) {
  const isLouge = status === "louge";
  const fulfillmentPct = Math.round(structureFulfillment * 100);

  // Summarize fulfilled parts for the detail text
  const fulfilledNames = structureParts
    ? STRUCTURE_PART_LABELS.filter((p) => structureParts[p.key]).map(
        (p) => p.label,
      )
    : [];
  const detailText =
    fulfilledNames.length === 0
      ? "未評価"
      : fulfilledNames.length === 4
        ? "全パーツ充足"
        : `${fulfilledNames.join("+")}のみ`;

  return (
    <div
      className="rounded-lg border border-border bg-bg-card p-5"
      data-testid="score-card"
    >
      <h3 className="mb-4 flex items-center gap-1.5 text-heading-m text-primary-dark">
        <Sparkles size={16} strokeWidth={1.5} className="text-primary" />
        開花スコア
      </h3>

      {/* Score pending indicator */}
      {scorePending && (
        <div
          className="mb-3 flex items-center gap-2 rounded-md bg-primary-light-bg px-3 py-2 text-caption text-primary"
          data-testid="score-pending-indicator"
        >
          <Loader2 size={14} className="animate-spin" />
          スコアを計算中...
        </div>
      )}

      {/* Structure fulfillment (Condition A) */}
      <div className="mb-3">
        <p className="mb-1 text-body-s text-text-secondary">
          構造充足度（条件A）
        </p>
        <div className="h-[6px] w-full overflow-hidden rounded-xs bg-primary-light-bg">
          <div
            className={`h-[6px] rounded-xs transition-all ${
              isLouge ? "bg-primary" : "bg-primary/50"
            }`}
            style={{ width: `${Math.min(fulfillmentPct, 100)}%` }}
          />
        </div>
        <div className="mt-1 flex items-center gap-1 text-body-s">
          <span className="font-semibold text-primary">{fulfillmentPct}%</span>
          <span className="text-caption text-text-muted">
            -- {detailText}
          </span>
        </div>
      </div>

      {/* Structure parts checklist */}
      {structureParts && (
        <div className="mb-3 space-y-1">
          {STRUCTURE_PART_LABELS.map(({ key, label }) => {
            const fulfilled = structureParts[key];
            return (
              <div
                key={key}
                className="flex items-center gap-2 text-caption"
                data-testid={`structure-part-${key}`}
              >
                {fulfilled ? (
                  <Check
                    size={12}
                    strokeWidth={2}
                    className="text-primary"
                  />
                ) : (
                  <Circle
                    size={12}
                    strokeWidth={1.5}
                    className="text-text-muted"
                  />
                )}
                <span
                  className={
                    fulfilled ? "text-text-secondary" : "text-text-muted"
                  }
                >
                  {label}
                </span>
              </div>
            );
          })}
        </div>
      )}

      <div className="my-3 h-px bg-border" />

      {/* Stats */}
      <div className="space-y-2.5">
        <ScoreStat label="Log数" value={String(logCount)} />
        <ScoreStat label="貢献者数" value={String(contributorCount)} />
        {maturityScore !== null && (
          <ScoreStat
            label="成熟度（条件B）"
            value={`${Math.round(maturityScore * 100)}%`}
          />
        )}
        <ScoreStat
          label="開花まで"
          value={
            isLouge
              ? "開花済み"
              : `${Math.round(progress * 100)}% / ${Math.round(bloomThreshold * 100)}%`
          }
        />
        <ScoreStat
          label="ステータス"
          value={STATUS_LABELS[status] ?? status}
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
