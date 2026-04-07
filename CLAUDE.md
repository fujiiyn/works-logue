# Works Logue — CLAUDE.md

## AI-DLC Workflow

このプロジェクトはAI-DLC（AI-Driven Development Lifecycle）で進める。
ワークフロールールに従い、INCEPTION → CONSTRUCTION の順で開発を推進すること。

@aidlc-rules/aws-aidlc-rules/core-workflow.md

---

## Project Overview

**Works Logue** は、ビジネスパーソンが現場の悩み・失敗・知恵を投稿（Seed）し、コメント（Log）の熱量が一定基準に達した時点でAIが集合知を記事（Louge）として開花させる、Wikipedia型のビジネスナレッジ共創プラットフォーム。貢献度をスキル通貨（Skill as a Currency）としてスコア化し、会社に依存しないポータブルなプロフェッショナル資産を可視化する。

詳細: @docs/business-plan.md

---

## Tech Stack

| レイヤー | 技術 |
|---|---|
| Frontend | Next.js (App Router) + TypeScript strict |
| Backend | Python FastAPI |
| Database | Supabase (PostgreSQL + Auth + Storage) |
| AI | Vertex AI (Google Cloud) |
| Deploy | Cloud Run (apps/web, apps/api それぞれ独立) |

---

## Repository Structure

```
works-logue/               ← monorepo
├── CLAUDE.md
├── apps/
│   ├── web/               ← Next.js
│   └── api/               ← FastAPI
├── packages/
│   └── shared/            ← 型定義・スキーマ共有（必要になったら追加）
├── supabase/              ← migrations, seed, types
├── infra/                 ← Dockerfile, Cloud Run設定
├── aidlc-rules/           ← AI-DLCワークフロールール（編集しない）
└── docs/
```

---

## Code Quality Rules

### TypeScript (apps/web)
- `strict: true` を必須とする
- ESLint + Prettier（デフォルト設定）
- テスト対象: Vertex AI呼び出し周り・主要APIルート・核心フロー（Seed→Log→Louge）のE2E（Playwright）

### Python (apps/api)
- Ruff（lint + format）
- mypy strict
- pytest でAPIエンドポイント + AIパイプラインをカバー

### 共通
- Cloud Run向けに**構造化JSONログ**を標準とする
- Supabaseのスキーマ変更は必ず `supabase/migrations/` でバージョン管理する

---

## Design Rules

デザインガイド: @docs/design-style.md

- カラー: ティールグリーン（#00B4CC）+ クリーム背景 + ダークフォレストグリーン（#1A5C42）
- アイコン: Lucide（絵文字は使わない）
- 雰囲気: ボタニカル・オーガニック

---

## Domain Vocabulary

| 用語 | 意味 |
|---|---|
| Planter | Seed・Log・Lougeを内包する成長の単位（内部概念・UI非表示） |
| Seed | Planterの起点となる問いの投下。Planter状態: `seed` |
| Log | Seedへのコメント・知恵の蓄積。Log投稿のたびにLougeスコアを再計算 |
| Sprout | Logが1件以上蓄積されたPlanter状態: `sprout`（内部でSprout 1〜3を区別） |
| Louge | Lougeスコアが開花閾値に達しAIが生成したナレッジ記事。Planter状態: `louge` |
| Fork | LougeをベースにSeedを再投稿すること（フェーズ2） |

タグ定義: @docs/tags.md

---

## Development Notes

- **一人開発**。パフォーマンス最適化・カバレッジ100%は初期フェーズでは不要
- greenfield（新規）プロジェクト
- AI-DLC の INCEPTION フェーズを必ず通してから実装に入ること

---

## Context Management

- コンパクション時は「変更ファイル一覧・未完了タスク・直近の設計判断」を必ず保持すること
- タスクが切り替わる場合は `/clear` を推奨

---

## CLAUDE.md Self-Improvement

- Claudeが繰り返し同じ間違いをした場合、または自分への指示が不明確だと判断した場合は、このファイルの該当箇所を修正・追記すること
- 削除基準: 「この行がなくてもClaudeが正しく動くか？」→ YESなら削除
- 追加基準: 「この行がないとClaudeが間違いを犯すか？」→ YESなら追加
