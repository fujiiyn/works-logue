"use client";

import type { ReactNode } from "react";
import { AdminHeader } from "./admin-header";
import { AdminSidebar } from "./admin-sidebar";

interface AdminShellProps {
  user: {
    id: string;
    display_name: string;
  };
  children: ReactNode;
}

export function AdminShell({ user, children }: AdminShellProps) {
  return (
    <div className="flex min-h-screen flex-col bg-bg" data-testid="admin-shell">
      <AdminHeader user={user} />
      {/* Mobile fallback: admin UI is desktop-only (FC レスポンシブ方針 D16) */}
      <div className="flex min-h-[calc(100vh-3.5rem)] flex-1 lg:hidden">
        <main className="flex-1 px-6 py-6 text-primary-dark">
          <p className="text-body-m">
            管理画面はデスクトップ環境（横幅 1024px 以上）でご利用ください。
          </p>
        </main>
      </div>
      <div className="hidden flex-1 lg:flex">
        <AdminSidebar user={user} />
        <main className="min-w-0 flex-1 px-10 py-6">{children}</main>
      </div>
    </div>
  );
}
