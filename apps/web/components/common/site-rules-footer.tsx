"use client";

import { Fragment } from "react";
import Link from "next/link";

const LINKS = [
  { href: "/about", label: "Works Logue とは" },
  { href: "/rules/privacy-policy", label: "プライバシーポリシー" },
  { href: "/rules/terms-of-service", label: "利用規約" },
  { href: "/rules/contents-policy", label: "コンテンツポリシー" },
];

const FOOTER_YEAR = new Date().getFullYear();

interface SiteRulesFooterProps {
  /** inline: 中黒区切りの折り返し1行（右カラム用） / stack: 縦積み（左ナビ・ドロワー用） */
  orientation?: "inline" | "stack";
  /** 右カラムと左ナビで同時に DOM に載るため、testid は呼び出し側で衝突を避ける */
  testId?: string;
  className?: string;
  onNavigate?: () => void;
}

export function SiteRulesFooter({
  orientation = "inline",
  testId = "site-rules-footer",
  className = "mt-4 px-1",
  onNavigate,
}: SiteRulesFooterProps) {
  const isStack = orientation === "stack";
  return (
    <div
      className={`text-caption leading-relaxed text-text-secondary ${className}`}
      data-testid={testId}
    >
      <div
        className={
          isStack
            ? "flex flex-col gap-1.5"
            : "flex flex-wrap items-center gap-x-2 gap-y-1"
        }
      >
        {LINKS.map((link, index) => (
          <Fragment key={link.href}>
            {!isStack && index > 0 && <span aria-hidden="true">·</span>}
            <Link
              href={link.href}
              onClick={onNavigate}
              className="underline decoration-text-secondary/40 underline-offset-2 hover:text-primary hover:decoration-primary"
            >
              {link.label}
            </Link>
          </Fragment>
        ))}
      </div>
      <div className="mt-1 text-text-muted">Works Logue © {FOOTER_YEAR}</div>
    </div>
  );
}
