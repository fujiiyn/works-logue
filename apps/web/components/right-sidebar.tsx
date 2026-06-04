"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Sprout } from "lucide-react";
import { useRightSidebar } from "@/contexts/right-sidebar-context";
import { getPublicStats, type PublicStats } from "@/lib/api-client";

export function RightSidebar() {
  const { content } = useRightSidebar();
  return (
    <aside
      className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-[300px] shrink-0 py-6 pr-6 xl:block"
      data-testid="right-sidebar"
    >
      {content ?? (
        <>
          <AboutCard />
          <SiteRulesFooter />
        </>
      )}
    </aside>
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

const FOOTER_YEAR = new Date().getFullYear();

function SiteRulesFooter() {
  return (
    <div
      className="mt-4 px-1 text-caption leading-relaxed text-text-secondary"
      data-testid="site-rules-footer"
    >
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <Link
          href="/rules/privacy-policy"
          className="underline decoration-text-secondary/40 underline-offset-2 hover:text-primary hover:decoration-primary"
        >
          プライバシーポリシー
        </Link>
        <span aria-hidden="true">·</span>
        <Link
          href="/rules/terms-of-service"
          className="underline decoration-text-secondary/40 underline-offset-2 hover:text-primary hover:decoration-primary"
        >
          利用規約
        </Link>
        <span aria-hidden="true">·</span>
        <Link
          href="/rules/contents-policy"
          className="underline decoration-text-secondary/40 underline-offset-2 hover:text-primary hover:decoration-primary"
        >
          コンテンツポリシー
        </Link>
      </div>
      <div className="mt-1 text-text-muted">Works Logue © {FOOTER_YEAR}</div>
    </div>
  );
}
