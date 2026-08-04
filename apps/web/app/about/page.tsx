import type { Metadata } from "next";
import { Zen_Old_Mincho } from "next/font/google";
import { AboutLp } from "@/components/lp/about-lp";

// 見出し用の明朝。欧文のみ読み込み、和文はOS標準の明朝にフォールバックする
const zenOldMincho = Zen_Old_Mincho({
  subsets: ["latin"],
  weight: ["400", "600"],
  display: "swap",
  variable: "--font-zen-old-mincho",
});

export const metadata: Metadata = {
  title: "Works Logue とは | Business Knowledge Engineering",
  description:
    "現場の悩みや失敗を持ち寄り、AIの手を借りてひとつのナレッジへ編み上げる。Works Logue の出発点と、Seed から Logue へ至る知の循環について。",
};

export default function AboutPage() {
  return (
    <div className={zenOldMincho.variable}>
      <AboutLp />
    </div>
  );
}
