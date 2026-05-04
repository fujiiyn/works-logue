"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft, LayoutDashboard, Sprout, Users, Wheat } from "lucide-react";

interface NavItem {
  key: string;
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  matchExact?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    key: "dashboard",
    href: "/admin",
    label: "ダッシュボード",
    icon: LayoutDashboard,
    matchExact: true,
  },
  {
    key: "users",
    href: "/admin/users",
    label: "ユーザー管理",
    icon: Users,
  },
  {
    key: "planters",
    href: "/admin/planters",
    label: "Planter 管理",
    icon: Sprout,
  },
  {
    key: "seed-types",
    href: "/admin/seed-types",
    label: "SeedType マスタ",
    icon: Wheat,
  },
];

interface AdminSidebarProps {
  user: {
    display_name: string;
  };
}

export function AdminSidebar({ user }: AdminSidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      data-testid="admin-sidebar"
      className="flex h-[calc(100vh-3.5rem)] w-52 shrink-0 flex-col border-r border-border bg-bg-card"
    >
      <div className="px-4 pb-4 pt-5">
        <p className="text-caption font-semibold text-text-secondary">
          管理者メニュー
        </p>
        <span className="mt-2 inline-block rounded bg-primary-dark px-1.5 py-0.5 text-[11px] font-semibold text-white">
          Admin
        </span>
        <p className="mt-2 text-caption text-text-secondary">
          {user.display_name}
        </p>
      </div>
      <div className="border-b border-border" />
      <nav className="flex-1 px-2 py-4">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = item.matchExact
              ? pathname === item.href
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <li key={item.key}>
                <Link
                  href={item.href}
                  data-testid={`admin-sidebar-link-${item.key}`}
                  aria-current={active ? "page" : undefined}
                  className={`relative flex items-center gap-3 rounded-md px-3 py-2.5 text-body-s ${
                    active
                      ? "bg-primary-light-bg font-semibold text-primary"
                      : "text-primary-dark hover:bg-bg"
                  }`}
                >
                  {active ? (
                    <span
                      aria-hidden
                      className="absolute -left-2 top-0 h-full w-0.5 rounded bg-primary"
                    />
                  ) : null}
                  <Icon className="h-5 w-5 shrink-0" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="border-t border-border px-4 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-body-s text-text-secondary hover:text-primary-dark"
        >
          <ArrowLeft className="h-4 w-4" />
          公開サイトに戻る
        </Link>
      </div>
    </aside>
  );
}
