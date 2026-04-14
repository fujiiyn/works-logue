"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { Skeleton } from "@/components/common/Skeleton";
import { SeedForm } from "@/components/seed/SeedForm";

function SeedFormSkeleton() {
  return (
    <div>
      {/* Title */}
      <Skeleton className="mb-2 h-7 w-48" />
      <Skeleton className="mb-6 h-4 w-96" />

      {/* Seed type grid */}
      <Skeleton className="mb-2 h-4 w-40" />
      <div className="mb-4 grid grid-cols-2 gap-2.5">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-[60px] rounded-lg" />
        ))}
      </div>

      {/* Title input */}
      <Skeleton className="mb-4 h-[42px] rounded-md" />

      {/* Body textarea */}
      <Skeleton className="mb-2 h-4 w-12" />
      <Skeleton className="mb-4 h-[130px] rounded-md" />

      {/* Tags */}
      <Skeleton className="mb-2.5 h-4 w-8" />
      <Skeleton className="mb-4 h-[200px] rounded-md" />

      {/* Buttons */}
      <div className="flex justify-end gap-3">
        <Skeleton className="h-[42px] w-24 rounded-lg" />
        <Skeleton className="h-[42px] w-28 rounded-lg" />
      </div>
    </div>
  );
}

export default function SeedNewPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login?redirect=/seed/new");
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return <SeedFormSkeleton />;
  }

  if (!user) {
    return null;
  }

  return <SeedForm />;
}
