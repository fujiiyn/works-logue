import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: number | string;
  caption?: string;
  testId?: string;
}

export function StatCard({
  icon: Icon,
  label,
  value,
  caption,
  testId,
}: StatCardProps) {
  return (
    <div
      data-testid={testId}
      className="rounded-lg border border-border bg-bg-card p-5"
    >
      <div className="flex items-center gap-2 text-text-secondary">
        <Icon className="h-5 w-5" aria-hidden />
        <span className="text-body-s">{label}</span>
      </div>
      <p className="mt-3 text-[28px] font-semibold leading-tight text-primary-dark">
        {typeof value === "number" ? value.toLocaleString("ja-JP") : value}
      </p>
      {caption ? (
        <p className="mt-3 text-caption text-text-muted">{caption}</p>
      ) : null}
    </div>
  );
}
