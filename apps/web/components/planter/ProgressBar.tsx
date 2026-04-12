interface ProgressBarProps {
  progress: number;
  status: string;
}

export function ProgressBar({ progress, status }: ProgressBarProps) {
  const clampedProgress = Math.min(Math.max(progress, 0), 1);
  const isLouge = status === "louge";

  return (
    <div
      className="h-[3px] w-[120px] rounded-xs bg-primary-light-bg"
      data-testid="progress-bar"
    >
      <div
        className={`h-[3px] rounded-xs ${isLouge ? "bg-primary" : "bg-primary/50"}`}
        style={{ width: `${clampedProgress * 100}%` }}
      />
    </div>
  );
}
