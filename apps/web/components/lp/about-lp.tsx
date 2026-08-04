"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, type ReactNode } from "react";
import {
  ArrowRight,
  ChevronDown,
  Flower2,
  GitFork,
  Leaf,
  Network,
  Sprout,
} from "lucide-react";

const HERO_IMAGE = "/img/lp-background.jpg";

/** 円周上に等間隔で並ぶ 5 つの段階。Fork から Seed へ還って一周する */
const CYCLE = [
  {
    key: "Seed",
    ja: "種",
    angle: -90,
    side: "top",
    icon: Sprout,
    body: "誰かの悩みや、小さな気づき。世界で初めて文字になる一次情報。",
  },
  {
    key: "Log",
    ja: "記録",
    angle: -18,
    side: "right",
    icon: Leaf,
    body: "「うちも似たことがあった」という現場の実践知。",
  },
  {
    key: "Logic",
    ja: "論理",
    angle: 54,
    side: "right",
    icon: Network,
    body: "Log が集まり、構造化していくプロセス。",
  },
  {
    key: "Logue",
    ja: "対話",
    angle: 126,
    side: "left",
    icon: Flower2,
    body: "ひとつの大きなナレッジ（集合知）として開花する。",
  },
  {
    key: "Fork",
    ja: "派生",
    angle: 198,
    side: "left",
    icon: GitFork,
    body: "現場で実践し、その発見をまた次の Seed へ。",
  },
] as const;

const HORIZON = [
  {
    title: "スキルの資産化",
    note: "Skill as a Currency",
    body: "プラットフォームへの貢献を、所属企業に依存しない「個人のポータブルな価値（ポートフォリオ）」として、社会的に認められる形へと育てます。",
  },
  {
    title: "あらゆる境界を越えた共創",
    note: null,
    body: "業界、職種、会社の壁を越え、あちこちで起きている「車輪の再発明」を防ぎます。正解のない実務課題を抱える誰もが参加できる場所へ。",
  },
  {
    title: "現場と現場をつなぐインフラ",
    note: null,
    body: "単なる情報収集の場ではなく、同じ壁にぶつかった者同士が出会い、次の一歩を共に踏み出せる「コレクティブ・インテリジェンス（集合知）」の基盤となります。",
  },
] as const;

export function AboutLp() {
  const rootRef = useRef<HTMLElement>(null);

  useRevealOnScroll(rootRef);

  return (
    <main ref={rootRef} data-testid="about-lp">
      {/* ── Hero: 創業の問いそのものを掲げる ───────────────── */}
      <section
        className="relative flex min-h-[100svh] flex-col justify-end overflow-hidden"
        data-testid="about-hero"
      >
        <Image
          src={HERO_IMAGE}
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-center"
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(31,56,51,0.16)_0%,rgba(31,56,51,0.42)_42%,rgba(31,56,51,0.7)_62%,rgba(31,56,51,0.93)_100%)]"
        />

        <div className="relative mx-auto w-full max-w-[1030px] px-6 pb-16 pt-24 md:px-12 md:pb-24">
          <p className="lp-hero-in font-mincho text-[13px] tracking-[0.22em] text-bg/80">
            Works Logue とは
          </p>
          <h1 className="lp-hero-in mt-5 font-mincho text-[clamp(26px,4.8vw,56px)] font-normal leading-[1.5] text-bg [animation-delay:120ms]">
            なぜ、一般的なビジネスの世界には
            <br className="hidden sm:block" />
            「技術ブログ」がないのだろう？
          </h1>
          <p className="lp-hero-in mt-7 max-w-[40em] text-[15px] leading-[2] text-bg/85 [animation-delay:260ms] md:text-[16px]">
            現場の悩みや失敗を持ち寄り、AI の手を借りてひとつのナレッジへ編み上げる。Works
            Logue は、ビジネス・ナレッジ・エンジニアリングのためのプラットフォームです。
          </p>

          <p className="lp-hero-in mt-14 flex items-center gap-2 text-[11px] tracking-[0.18em] text-bg/70 [animation-delay:420ms]">
            <ChevronDown size={16} strokeWidth={1.5} className="lp-cue" />
            READ ON
          </p>
        </div>
      </section>

      {/* ── 01 出発点 ─────────────────────────────────────── */}
      <Section eyebrow="Origin" title="エンジニアの文化に惹かれ、違和感を覚えた">
        <P>
          私はエンジニアではありません。しかし、仕事を通じてエンジニアの方々と関わる中で、彼らが持つ独自のカルチャーに強く惹かれていきました。
        </P>
        <P>
          オープンソースの精神、失敗を隠さずに共有する文化、「やってみた」という気軽な投稿、そして
          GitHub
          を通じた知の共創。そこには「困ったことは、隠さず言っていい」という心理的安全性と、誰かの試行錯誤が全体の共有財産へと昇華されていく、非常に成熟したエコシステムがありました。
        </P>
        <P>同時に、強い違和感を覚えました。</P>
        <P>
          一般的なビジネスの世界には、こうした文化がほとんどありません。営業、人事、マーケティング……現場で起きている無数の悩みや泥臭い工夫は、個人の頭の中やクローズドな議事録の中に閉じ込められ、誰にも知られることなく静かに消えていきます。
        </P>

        <blockquote
          className="my-12 border-l border-primary pl-6 lp-rise md:pl-8"
          data-reveal
        >
          <p className="font-mincho text-[clamp(20px,2.8vw,30px)] leading-[1.8] text-primary-dark">
            ビジネスパーソンにも、技術ブログのような場所が
            <br className="hidden md:block" />
            あってもいいのではないか。
          </p>
        </blockquote>

        <P>
          一人の天才のひらめきではなく、現場に立つすべての人の知恵を持ち寄れば、仕事はもっと前に進められる。この想いが、Works
          Logue の出発点です。
        </P>
      </Section>

      {/* ── 02 一次情報 ───────────────────────────────────── */}
      <Section eyebrow="Primary source" title="生成AIには、絶対に作れないもの">
        <P>
          私たちが日々直面する実務の壁を突破する鍵は、現場の生々しい「一次情報」にあります。
        </P>
        <P>
          現在、生成AIは凄まじいスピードで進化しています。しかし、AI
          のすごさの正体は「すでに公開された情報を、上手に探してまとめる力」です。世の中に存在する一次情報のうち、文字として公開されているのは、ほんの氷山の一角にすぎません。機密性や「わざわざ書くほどでもない」という理由で、本当の失敗談や生々しい解決策の多くは、誰の目にも触れることなく終わっています。
        </P>
        <P>
          生成AIは、既存の情報を合成することはできても、
          <strong className="font-semibold text-primary-dark">
            「まだ誰も言語化していない現場の経験そのもの」
          </strong>
          を新しく生み出すことはできません。
        </P>
        <P>
          私たちが Works Logue
          で実現することは、「AIには絶対に作れない」これまで一度も文字にならなかった現場の固有の経験そのものを「集める」ことです。
        </P>
      </Section>

      {/* ── 03 設計思想（反転バンド） ────────────────────────── */}
      <Section
        eyebrow="By design"
        title="アテンション・エコノミーからの脱却。『良いインターネット』を創る"
        tone="dark"
      >
        <P tone="dark">
          今のインターネットの多くは、「読まれること」「目立つこと」自体が報酬になる構造（アテンション・エコノミー）を持っています。極端な意見や対立を煽る言葉が拡散され、純粋な知恵が埋もれてしまう。
        </P>
        <P tone="dark">
          Works Logue
          は、この構造とは明確に違う設計を選びました。評価の軸は「どれだけ拡散されたか」ではなく、
          <strong className="font-semibold text-bg">
            「どれだけ本質的な対話（Logue）の開花に貢献したか」
          </strong>
          というインサイト・スコアです。見知らぬ大勢の目を引くためではなく、同じ悩みに向き合っている「具体的な誰か」に向けて書かれた知恵が評価される。
        </P>
        <P tone="dark">
          対立を煽り、時間と思考を消費させる場所ではなく、純粋な知の生産と共有が行われる、健全で生産的な空間。私たちはこれを、ビジネスの新しいインフラとして根付かせます。
        </P>
      </Section>

      {/* ── 04 仕組み（シグネチャ: 円環図） ───────────────────── */}
      <Section eyebrow="The cycle" title="種から花へ。Works Logue の仕組み">
        <P>
          Works
          Logue（ワークス・ローグ）は、誰かの仕事の悩みや違和感から出発し、現場の実践知を集め、AI
          のサポートによってひとつのナレッジへと統合していく「ビジネス・ナレッジ・エンジニアリング」プラットフォームです。
        </P>
        <P>
          単なるブログのように「記事」を書くのではなく、知恵が育つプロセスそのものを設計しています。
        </P>

        <CycleDiagram />

        <P>
          生まれた Logue
          は完成品ではありません。ユーザーはそれを自分の現場に持ち帰り、実践し（Fork）、そこで得た新たな発見や壁を、また次の
          Seed
          としてプラットフォームに還す。花からこぼれた種が、新しい対話を芽吹かせていく。この
          <strong className="font-semibold text-primary-dark">
            「後退しない知の循環」
          </strong>
          こそが、私たちの核です。
        </P>
      </Section>

      {/* ── 05 これから ──────────────────────────────────── */}
      <Section eyebrow="What's next" title="これから一緒に実現したいこと">
        <P>
          Works Logue
          は、まだ芽吹いたばかりのサービスです。今後、私たちは以下の未来を実現していきます。
        </P>

        <div className="mt-12 grid gap-8 md:grid-cols-3 md:gap-10">
          {HORIZON.map((item) => (
            <div
              key={item.title}
              className="border-t border-primary/30 pt-5 lp-rise"
              data-reveal
            >
              <h3 className="font-mincho text-[18px] leading-snug text-primary-dark">
                {item.title}
              </h3>
              {item.note && (
                <p className="mt-1.5 text-[11px] tracking-[0.14em] text-primary">
                  {item.note}
                </p>
              )}
              <p className="mt-3 text-[14px] leading-[1.95] text-text-secondary md:text-[15px]">
                {item.body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* ── 結び ─────────────────────────────────────────── */}
      <section className="relative overflow-hidden" data-testid="about-closing">
        <Image
          src={HERO_IMAGE}
          alt=""
          fill
          sizes="100vw"
          className="object-cover object-bottom"
        />
        <div aria-hidden="true" className="absolute inset-0 bg-[#1F3833]/85" />

        <div className="relative mx-auto max-w-[1030px] px-6 py-20 md:px-12 md:py-28">
          <p
            className="font-mincho text-[clamp(22px,3.6vw,38px)] leading-[1.6] text-bg lp-rise"
            data-reveal
          >
            個人の中に眠る暗黙知を、
            <br className="hidden sm:block" />
            世界を前に進める力へ。
          </p>

          <div className="mt-12 lp-rise" data-reveal>
            <Link
              href="/"
              className="inline-flex items-center gap-3 rounded-md bg-bg px-9 py-5 font-mincho text-[17px] text-primary-dark transition-colors hover:bg-white md:text-[18px]"
              data-testid="about-cta-start"
            >
              Works Logue を始める
              <ArrowRight size={18} strokeWidth={1.5} className="text-primary" />
            </Link>
          </div>

          <div className="mt-16 border-t border-bg/20 pt-6">
            <p className="font-mincho text-[15px] tracking-[0.04em] text-bg">
              Works Logue
              <span className="ml-3 text-[11px] tracking-[0.18em] text-bg/60">
                Business Knowledge Engineering
              </span>
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-caption text-bg/70">
              <Link href="/" className="hover:text-bg">
                ホーム
              </Link>
              <Link href="/rules/privacy-policy" className="hover:text-bg">
                プライバシーポリシー
              </Link>
              <Link href="/rules/terms-of-service" className="hover:text-bg">
                利用規約
              </Link>
              <Link href="/rules/contents-policy" className="hover:text-bg">
                コンテンツポリシー
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

/* ── 円環図 ─────────────────────────────────────────────── */

const RADIUS = 50; // 円の半径（正方形コンテナに対する %。円がコンテナ枠と一致する）
const NODE_GAP = 18; // ノードを避けるための弧の余白（度）

function polar(deg: number) {
  const rad = (deg * Math.PI) / 180;
  return {
    x: 50 + RADIUS * Math.cos(rad),
    y: 50 + RADIUS * Math.sin(rad),
  };
}

const ARCS = CYCLE.map((stage, i) => {
  const next = CYCLE[(i + 1) % CYCLE.length];
  const from = polar(stage.angle + NODE_GAP);
  const nextAngle =
    next.angle > stage.angle ? next.angle : next.angle + 360; // Fork → Seed で一周する
  const to = polar(nextAngle - NODE_GAP);
  return `M ${from.x.toFixed(2)} ${from.y.toFixed(2)} A ${RADIUS} ${RADIUS} 0 0 1 ${to.x.toFixed(2)} ${to.y.toFixed(2)}`;
});

function StageIcon({ stage }: { stage: (typeof CYCLE)[number] }) {
  const Icon = stage.icon;
  const isBloom = stage.key === "Logue";
  return (
    <span
      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-bg ${
        isBloom
          ? "border border-primary/60 bg-primary-light-bg"
          : "border border-primary/25"
      }`}
    >
      <Icon
        size={21}
        strokeWidth={1.4}
        className={isBloom ? "text-primary" : "text-primary/75"}
      />
    </span>
  );
}

function StageText({ stage }: { stage: (typeof CYCLE)[number] }) {
  return (
    <>
      <p className="font-mincho text-[16px] leading-none text-primary-dark">
        {stage.key}
        <span className="ml-2 text-[11px] text-text-muted">{stage.ja}</span>
      </p>
      <p className="mt-2 text-[13px] leading-[1.8] text-text-secondary">
        {stage.body}
      </p>
    </>
  );
}

function CycleDiagram() {
  return (
    <div className="my-14 lp-rise" data-reveal data-testid="about-cycle">
      {/* 円環（デスクトップ） */}
      <div className="relative mx-auto hidden h-[480px] w-full max-w-[900px] md:block">
        {/* Seed の説明が円の上に入るので、円は下寄せにして上に余白を確保する */}
        <div className="absolute bottom-0 left-1/2 h-[360px] w-[360px] -translate-x-1/2">
          <svg
            viewBox="0 0 100 100"
            className="absolute inset-0 h-full w-full overflow-visible text-primary/40"
            aria-hidden="true"
          >
            <defs>
              <marker
                id="lp-cycle-arrow"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto"
              >
                <path
                  d="M 0.5 1 L 8.5 5 L 0.5 9"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </marker>
            </defs>
            {ARCS.map((d) => (
              <path
                key={d}
                d={d}
                fill="none"
                stroke="currentColor"
                strokeWidth="0.45"
                markerEnd="url(#lp-cycle-arrow)"
              />
            ))}
          </svg>

          {CYCLE.map((stage) => {
            const { x, y } = polar(stage.angle);
            return (
              <div
                key={stage.key}
                data-stage={stage.key}
                className="absolute h-12 w-12 -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${x}%`, top: `${y}%` }}
              >
                <StageIcon stage={stage} />
                <div
                  className={
                    stage.side === "right"
                      ? "absolute left-full top-1/2 ml-[22px] w-[210px] -translate-y-1/2"
                      : stage.side === "left"
                        ? "absolute right-full top-1/2 mr-[22px] w-[210px] -translate-y-1/2 text-right"
                        : "absolute bottom-full left-1/2 mb-[22px] w-[280px] -translate-x-1/2 text-center"
                  }
                >
                  <StageText stage={stage} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 縦の並び（モバイル） */}
      <ul className="space-y-7 md:hidden">
        {CYCLE.map((stage) => (
          <li key={stage.key} data-stage={stage.key} className="flex gap-4">
            <StageIcon stage={stage} />
            <div className="pt-1">
              <StageText stage={stage} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ── レイアウト部品 ──────────────────────────────────────── */

function Section({
  eyebrow,
  title,
  tone = "light",
  children,
}: {
  eyebrow: string;
  title: string;
  tone?: "light" | "dark";
  children: ReactNode;
}) {
  const dark = tone === "dark";
  return (
    <section
      className={`py-16 md:py-24 ${dark ? "bg-primary-dark" : ""}`}
      data-tone={tone}
    >
      <div className="mx-auto max-w-[1030px] px-6 md:px-12">
        <p
          className={`text-[11px] uppercase tracking-[0.22em] lp-rise ${
            dark ? "text-text-sage" : "text-primary"
          }`}
          data-reveal
        >
          {eyebrow}
        </p>
        <h2
          className={`mt-4 max-w-[24em] font-mincho text-[clamp(23px,3.2vw,34px)] font-normal leading-[1.55] lp-rise ${
            dark ? "text-bg" : "text-primary-dark"
          }`}
          data-reveal
        >
          {title}
        </h2>
        <div className="mt-9">{children}</div>
      </div>
    </section>
  );
}

function P({
  tone = "light",
  children,
}: {
  tone?: "light" | "dark";
  children: ReactNode;
}) {
  return (
    <p
      className={`mb-6 text-[16px] leading-[2.05] last:mb-0 md:text-[17px] lp-rise ${
        tone === "dark" ? "text-bg/85" : "text-text-secondary"
      }`}
      data-reveal
    >
      {children}
    </p>
  );
}

/**
 * data-reveal を持つ要素を、ビューポート進入時に一度だけ表示する。
 * 隠す指定は data-lp-ready が付いてから効くため、JS 非実行環境では本文がそのまま残る。
 */
function useRevealOnScroll(rootRef: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const targets = Array.from(
      root.querySelectorAll<HTMLElement>("[data-reveal]"),
    );
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    if (prefersReducedMotion || typeof IntersectionObserver === "undefined") {
      return;
    }

    root.dataset.lpReady = "true";

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.setAttribute("data-revealed", "true");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.1 },
    );

    targets.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [rootRef]);
}
