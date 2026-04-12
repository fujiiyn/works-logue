import Link from "next/link";
import { ProgressBar } from "./ProgressBar";
import { formatRelativeTime } from "@/lib/format-time";

interface PlanterCardProps {
  planter: {
    id: string;
    title: string;
    status: string;
    seed_type: { slug: string; name: string };
    user: { id: string; display_name: string; avatar_url: string | null };
    tags: { id: string; name: string; category: string }[];
    log_count: number;
    contributor_count: number;
    progress: number;
    created_at: string;
  };
}

const STATUS_LABELS: Record<string, string> = {
  seed: "Seed",
  sprout: "Sprout",
  louge: "Louge",
};

export function PlanterCard({ planter }: PlanterCardProps) {
  const isLouge = planter.status === "louge";
  const visibleTags = planter.tags.slice(0, 3);
  const extraCount = planter.tags.length - 3;

  return (
    <Link
      href={`/p/${planter.id}`}
      className="block border-b border-border py-[18px]"
      data-testid="planter-card"
    >
      {/* Top row: badge, seed type, user, time */}
      <div className="mb-1.5 flex items-center gap-1.5 text-caption text-text-muted">
        <span
          className={`inline-block rounded-sm px-[6px] py-[1px] text-caption font-medium ${
            isLouge
              ? "bg-primary text-white"
              : "bg-primary-light-bg text-primary"
          }`}
          data-testid="planter-card-badge"
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
      <h3 className="mb-2 text-[15px] font-medium leading-[1.55] text-primary-dark">
        {planter.title}
      </h3>

      {/* Tags */}
      {planter.tags.length > 0 && (
        <div className="mb-2.5 flex flex-wrap gap-1.5">
          {visibleTags.map((tag) => (
            <span
              key={tag.id}
              className="rounded-sm border border-border px-[8px] py-[3px] text-caption text-text-secondary"
            >
              {tag.name}
            </span>
          ))}
          {extraCount > 0 && (
            <span className="rounded-sm border border-border px-[8px] py-[3px] text-caption text-text-muted">
              +{extraCount}
            </span>
          )}
        </div>
      )}

      {/* Bottom row: stats + progress */}
      <div className="flex items-center justify-between">
        <div className="flex gap-3 text-body-s text-text-muted">
          <span>{planter.log_count} logs</span>
          <span>{planter.contributor_count} contributors</span>
        </div>
        <ProgressBar progress={planter.progress} status={planter.status} />
      </div>
    </Link>
  );
}
