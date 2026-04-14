import { Skeleton } from "@/components/common/Skeleton";

export function PlanterCardSkeleton() {
  return (
    <div className="border-b border-border py-[18px]">
      {/* Meta row */}
      <div className="mb-1.5 flex items-center gap-2">
        <Skeleton className="h-[18px] w-10 rounded-sm" />
        <Skeleton className="h-3 w-12" />
        <Skeleton className="h-4 w-4 rounded-full" />
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-10" />
      </div>

      {/* Title */}
      <Skeleton className="mb-1 h-4 w-4/5" />
      <Skeleton className="mb-2 h-4 w-3/5" />

      {/* Tags */}
      <div className="mb-2.5 flex gap-1.5">
        <Skeleton className="h-[22px] w-16 rounded-sm" />
        <Skeleton className="h-[22px] w-20 rounded-sm" />
        <Skeleton className="h-[22px] w-14 rounded-sm" />
      </div>

      {/* Bottom stats + progress */}
      <div className="flex items-center justify-between">
        <div className="flex gap-3">
          <Skeleton className="h-3 w-14" />
          <Skeleton className="h-3 w-24" />
        </div>
        <Skeleton className="h-[3px] w-[120px] rounded-full" />
      </div>
    </div>
  );
}
