import type { Metadata } from "next";
import { Inter, Noto_Sans_JP } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/auth-context";
import { RightSidebarProvider } from "@/contexts/right-sidebar-context";
import { PublicChrome } from "@/components/layout/public-chrome";

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
            <PublicChrome>{children}</PublicChrome>
          </RightSidebarProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
