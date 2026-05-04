"use client";

import { Suspense, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Header } from "@/components/header";
import { Sidebar } from "@/components/sidebar";
import { RightSidebar } from "@/components/right-sidebar";
import { BannedBanner } from "@/components/layout/banned-banner";

export function PublicChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  // BR-A19 D4: admin routes use their own AdminShell — bypass the public chrome.
  if (pathname.startsWith("/admin")) {
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
          className="min-w-0 flex-1 px-10 py-6 xl:ml-[92px]"
          data-testid="main-content"
        >
          {children}
        </main>
        <RightSidebar />
      </div>
    </>
  );
}
