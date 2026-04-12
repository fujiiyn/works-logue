import type { Metadata } from "next";
import { Inter, Noto_Sans_JP } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { AuthProvider } from "@/contexts/auth-context";
import { RightSidebarProvider } from "@/contexts/right-sidebar-context";
import { Header } from "@/components/header";
import { Sidebar } from "@/components/sidebar";
import { RightSidebar } from "@/components/right-sidebar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const notoSansJP = Noto_Sans_JP({
  subsets: ["latin"],
  variable: "--font-noto-sans-jp",
});

export const metadata: Metadata = {
  title: "Works Logue",
  description:
    "ビジネスの知恵を共創するプラットフォーム。現場の悩みや知恵を集め、AIがナレッジを開花させます。",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja" className={`${inter.variable} ${notoSansJP.variable}`}>
      <body>
        <AuthProvider>
          <RightSidebarProvider>
          <Header />
          <div
            className="flex min-h-[calc(100vh-3.5rem)]"
            data-testid="layout-container"
          >
            <Suspense>
              <Sidebar />
            </Suspense>
            <main className="min-w-0 flex-1 px-10 py-6 xl:ml-[92px]" data-testid="main-content">
              {children}
            </main>
            <RightSidebar />
          </div>
          </RightSidebarProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
