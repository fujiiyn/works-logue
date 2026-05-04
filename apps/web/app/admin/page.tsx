import { notFound } from "next/navigation";
import { Calendar, Flower2, Sprout, Users } from "lucide-react";
import { getCurrentUser, serverFetch } from "@/lib/auth-server";
import { StatCard } from "@/components/admin/stat-card";
import type { AdminStats } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function AdminDashboardPage() {
  // Layout already gates on admin role; we re-resolve to obtain the access
  // token without round-tripping through a context that we deliberately
  // skipped (BR-A19).
  const user = await getCurrentUser();
  if (!user || user.role !== "admin") {
    notFound();
  }

  let stats: AdminStats;
  try {
    stats = await serverFetch<AdminStats>(
      "/api/v1/admin/stats",
      user.accessToken,
    );
  } catch {
    notFound();
  }

  return (
    <div>
      <h1 className="text-heading-xl font-semibold text-primary-dark">
        ダッシュボード
      </h1>
      <p className="mt-1 text-body-m text-text-secondary">
        サービスの主要指標を確認できます
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          testId="admin-stats-card-total_users"
          icon={Users}
          label="総ユーザー数"
          value={stats.total_users}
        />
        <StatCard
          testId="admin-stats-card-total_planters"
          icon={Sprout}
          label="総 Planter 数"
          value={stats.total_planters}
        />
        <StatCard
          testId="admin-stats-card-new_planters_today"
          icon={Calendar}
          label="本日の新規 Planter"
          value={stats.new_planters_today}
          caption="JST 当日の集計"
        />
        <StatCard
          testId="admin-stats-card-pending_louge_count"
          icon={Flower2}
          label="開花待ち Sprout"
          value={stats.pending_louge_count}
        />
      </div>
    </div>
  );
}
