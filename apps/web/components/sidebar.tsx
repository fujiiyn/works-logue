"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Home, Users, TrendingUp, Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/auth-context";

const NAV_ITEMS = [
  { label: "ホーム", icon: Home, href: "/", tab: null, authRequired: false },
  {
    label: "フォロー中",
    icon: Users,
    href: "/?tab=following",
    tab: "following",
    authRequired: true,
  },
  {
    label: "注目",
    icon: TrendingUp,
    href: "/?tab=trending",
    tab: "trending",
    authRequired: false,
  },
  { label: "探索", icon: Search, href: "/explore", tab: null, authRequired: false },
];

export function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const currentTab = searchParams.get("tab");

  function isActive(item: (typeof NAV_ITEMS)[number]) {
    if (item.href === "/explore") return pathname === "/explore";
    if (item.tab) return pathname === "/" && currentTab === item.tab;
    return pathname === "/" && !currentTab;
  }

  // Listen for hamburger toggle event from Header
  useEffect(() => {
    function handleToggle() {
      setDrawerOpen((prev) => !prev);
    }
    window.addEventListener("toggle-sidebar", handleToggle);
    return () => window.removeEventListener("toggle-sidebar", handleToggle);
  }, []);

  const navContent = (
    <nav className="flex flex-col gap-1 py-4" data-testid="sidebar-nav">
      {NAV_ITEMS.map((item) => {
        if (item.authRequired && !user) return null;
        const active = isActive(item);
        const Icon = item.icon;
        return (
          <Link
            key={item.label}
            href={item.href}
            onClick={() => setDrawerOpen(false)}
            className={`mx-2 flex items-center gap-3 rounded-md px-3 py-2 text-body-m transition-colors ${
              active
                ? "bg-primary-light-bg/60 font-semibold text-primary"
                : "text-primary-dark hover:bg-primary-light-bg/30"
            }`}
            data-testid={`sidebar-nav-${item.label}`}
          >
            <Icon size={20} strokeWidth={1.5} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-52 shrink-0 border-r border-border bg-bg-card md:block"
        data-testid="sidebar"
      >
        {navContent}
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/30 md:hidden"
            onClick={() => setDrawerOpen(false)}
            data-testid="sidebar-overlay"
          />
          <aside
            className="fixed inset-y-0 left-0 z-50 w-60 bg-bg-card shadow-lg md:hidden"
            data-testid="sidebar-drawer"
          >
            <div className="flex items-center justify-end px-4 py-3">
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="メニューを閉じる"
                data-testid="sidebar-close"
              >
                <X size={20} strokeWidth={1.5} />
              </button>
            </div>
            {navContent}
          </aside>
        </>
      )}
    </>
  );
}
