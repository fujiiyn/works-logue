import { Skeleton } from "@/components/common/Skeleton";

export default function PlanterDetailLoading() {
  return (
    <div data-testid="planter-detail-skeleton">
      {/* Meta row */}
      <div className="mb-3 flex items-center gap-2">
        <Skeleton className="h-[18px] w-10 rounded-sm" />
        <Skeleton className="h-3 w-12" />
        <Skeleton className="h-4 w-4 rounded-full" />
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-10" />
      </div>

      {/* Title */}
      <Skeleton className="mb-2 h-5 w-3/4" />
      <Skeleton className="mb-4 h-5 w-1/2" />

      {/* Body */}
      <div className="mb-5 max-w-[700px] space-y-2.5">
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-5/6" />
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-4/6" />
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-3/6" />
      </div>

      {/* Tags */}
      <div className="mb-4 flex gap-1.5">
        <Skeleton className="h-[22px] w-16 rounded-sm" />
        <Skeleton className="h-[22px] w-20 rounded-sm" />
        <Skeleton className="h-[22px] w-14 rounded-sm" />
      </div>

      {/* Stats */}
      <div className="mb-5 flex gap-3">
        <Skeleton className="h-3.5 w-14" />
        <Skeleton className="h-3.5 w-24" />
      </div>

      {/* Divider */}
      <div className="mb-5 h-px bg-border" />

      {/* Logs heading */}
      <Skeleton className="mb-4 h-5 w-12" />

      {/* Log skeletons */}
      {[0, 1, 2].map((i) => (
        <div key={i} className="mb-4 flex gap-2.5">
          <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-12" />
            </div>
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-4/5" />
          </div>
        </div>
      ))}
    </div>
  );
}
