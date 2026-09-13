"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Sprout } from "lucide-react";
import {
  useRightSidebar,
  type RightSidebarSlot,
} from "@/contexts/right-sidebar-context";
import { SiteRulesFooter } from "@/components/common/site-rules-footer";
import { getPublicStats, type PublicStats } from "@/lib/api-client";

export function RightSidebar() {
  const { content, target } = useRightSidebar();
  return (
    <aside
      className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-[300px] shrink-0 overflow-y-auto py-6 pr-6 xl:block"
      data-testid="right-sidebar"
    >
      {/*
        デフォルト表示は従来どおり SSR させる（幅判定で包むと、ハイドレーション
        まで右カラムが空になる）。ページ注入分だけを target で絞り、
        RightSidebarInline との二重マウントを防ぐ。
      */}
      {content ? target === "aside" && content : <AboutCard />}
      {/* ページ固有の内容に差し替わってもフッターは常に残す */}
      <SiteRulesFooter />
    </aside>
  );
}

/**
 * xl 未満で右カラムが display:none になる分の受け皿。ページが setContent で
 * 注入したコンテンツを本文の指定位置にインライン展開する。
 * デフォルトの AboutCard は本文に混ぜない（サービス紹介であり、
 * 本文を押しのけてまで出すものではないため）。規約リンクは左ナビ／ドロワー側に出る。
 */
export function RightSidebarInline({ slot }: { slot: RightSidebarSlot }) {
  const { content, target } = useRightSidebar();
  if (target !== slot) return null;
  return (
    <div
      className={slot === "top" ? "mb-6" : "mt-8"}
      data-testid={`right-sidebar-inline-${slot}`}
    >
      {content}
    </div>
  );
}

function AboutCard() {
  const [stats, setStats] = useState<PublicStats | null>(null);

  useEffect(() => {
    let cancelled = false;
    getPublicStats()
      .then((s) => {
        if (!cancelled) setStats(s);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const fmt = (n: number | undefined) =>
    n === undefined ? "--" : n.toLocaleString();

  return (
    <div
      className="rounded-lg border border-border bg-bg-card p-5"
      data-testid="about-card"
    >
      <h3 className="mb-3 text-heading-m text-primary-dark">
        About Works Logue
      </h3>
      <p className="mb-4 text-body-s leading-relaxed text-text-secondary">
        ビジネスの「集合知」を、みんなで育てるプラットフォーム。現場の悩みや知恵をSeedとして投稿し、対話を通じて「動くビジネス百科事典」を編纂します。
      </p>

      <div className="mb-4 flex gap-5">
        <Stat label="Seeds" value={fmt(stats?.seeds)} />
        <Stat label="Logues" value={fmt(stats?.logues)} />
        <Stat label="Contributors" value={fmt(stats?.contributors)} />
      </div>

      <Link
        href="/seed/new"
        className="flex w-full items-center justify-center gap-2 rounded-md border border-primary bg-white py-2 text-body-m text-primary transition-colors hover:bg-primary-light-bg"
        data-testid="about-card-seed-button"
      >
        <Sprout size={16} strokeWidth={1.5} />
        Seedを投稿する
      </Link>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-heading-m text-primary">{value}</span>
      <span className="text-caption text-text-muted">{label}</span>
    </div>
  );
}
