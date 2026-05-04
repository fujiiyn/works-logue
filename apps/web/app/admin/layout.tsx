import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { getCurrentUser } from "@/lib/auth-server";
import { AdminShell } from "@/components/admin/admin-shell";

export default async function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  const user = await getCurrentUser();
  // BR-A01 / Q10=B: any non-admin (including unauthenticated) sees a 404,
  // not a 403, so /admin URLs cannot be probed.
  if (!user || user.role !== "admin" || user.is_banned || user.deleted_at) {
    notFound();
  }

  return (
    <AdminShell user={{ id: user.id, display_name: user.display_name }}>
      {children}
    </AdminShell>
  );
}
