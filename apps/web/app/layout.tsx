import type { Metadata } from "next";
import { Inter, Noto_Sans_JP } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/auth-context";
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
          <Header />
          <div
            className="flex"
            data-testid="layout-container"
          >
            <Sidebar />
            <main className="mx-auto min-w-0 max-w-[960px] flex-1 px-10 py-6" data-testid="main-content">
              {children}
            </main>
            <RightSidebar />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
