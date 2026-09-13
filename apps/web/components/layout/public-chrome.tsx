"use client";

import { Suspense, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Header } from "@/components/header";
import { Sidebar } from "@/components/sidebar";
import { RightSidebar, RightSidebarInline } from "@/components/right-sidebar";
import { BannedBanner } from "@/components/layout/banned-banner";

export function PublicChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  // BR-A19 D4: admin routes use their own AdminShell — bypass the public chrome.
  if (pathname.startsWith("/admin")) {
    return <>{children}</>;
  }

  // LP（/about）は独立したページ。ヘッダー・サイドバーを一切出さない。
  if (pathname === "/about") {
    return <>{children}</>;
  }

  return (
    <>
      <Header />
      <BannedBanner />
      <div
        className="flex min-h-[calc(100vh-3.5rem)]"
        data-testid="layout-container"
      >
        <Suspense>
          <Sidebar />
        </Suspense>
        <main
          className="min-w-0 flex-1 px-4 py-6 md:px-10 xl:ml-[92px]"
          data-testid="main-content"
        >
          {/* xl 未満は右カラムが消えるため、その中身を本文にインライン展開する */}
          <RightSidebarInline slot="top" />
          {children}
          <RightSidebarInline slot="bottom" />
        </main>
        <RightSidebar />
      </div>
    </>
  );
}
