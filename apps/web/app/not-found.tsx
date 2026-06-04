import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-[720px] py-10">
      <h1 className="mb-3 text-heading-xl text-primary-dark">
        ページが見つかりません
      </h1>
      <p className="mb-6 text-body-m leading-relaxed text-primary-dark">
        お探しのページは存在しないか、移動した可能性があります。
      </p>
      <div className="flex flex-wrap gap-3">
        <Link
          href="/"
          className="rounded-md border border-primary px-4 py-2 text-body-m text-primary transition-colors hover:bg-primary-light-bg"
        >
          ホームに戻る
        </Link>
        <Link
          href="/explore"
          className="rounded-md border border-border px-4 py-2 text-body-m text-primary-dark transition-colors hover:bg-bg-card"
        >
          探索する
        </Link>
      </div>
      <div className="mt-10 border-t border-border pt-6">
        <h2 className="mb-3 text-heading-m text-primary-dark">規約</h2>
        <ul className="space-y-2 text-body-m">
          <li>
            <Link
              href="/rules/privacy-policy"
              className="text-primary underline hover:text-primary-dark"
            >
              プライバシーポリシー
            </Link>
          </li>
          <li>
            <Link
              href="/rules/terms-of-service"
              className="text-primary underline hover:text-primary-dark"
            >
              利用規約
            </Link>
          </li>
          <li>
            <Link
              href="/rules/contents-policy"
              className="text-primary underline hover:text-primary-dark"
            >
              コンテンツポリシー
            </Link>
          </li>
        </ul>
      </div>
    </div>
  );
}
