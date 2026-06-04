"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function RulesError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[rules] failed to render markdown document", error);
  }, [error]);

  return (
    <div className="mx-auto max-w-[720px] py-10">
      <h1 className="mb-3 text-heading-xl text-primary-dark">表示エラー</h1>
      <p className="mb-6 text-body-m leading-relaxed text-primary-dark">
        規約ページの表示に失敗しました。お手数ですが、時間を置いて再度お試しください。
      </p>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-md border border-primary px-4 py-2 text-body-m text-primary transition-colors hover:bg-primary-light-bg"
        >
          再読み込み
        </button>
        <Link
          href="/"
          className="rounded-md border border-border px-4 py-2 text-body-m text-primary-dark transition-colors hover:bg-bg-card"
        >
          ホームに戻る
        </Link>
      </div>
    </div>
  );
}
