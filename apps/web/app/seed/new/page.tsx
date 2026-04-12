"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { SeedForm } from "@/components/seed/SeedForm";

export default function SeedNewPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login?redirect=/seed/new");
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="py-16 text-center text-body-m text-text-muted">
        読み込み中...
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <SeedForm />;
}
