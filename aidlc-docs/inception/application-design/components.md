# Components Definition

## Overview

Works Logue MVP のコンポーネント定義。Frontend（Next.js App Router）と Backend（FastAPI）の2アプリケーション構成。

---

## Frontend Components（Next.js App Router）

### FC-01: Layout Shell

| 項目 | 内容 |
|---|---|
| 名前 | LayoutShell |
| 種別 | Server Component（App Router layout） |
| 責務 | 3カラムレイアウト（Header + Sidebar + Main + Right Sidebar）の共通構造を提供 |
| 配置 | `apps/web/app/layout.tsx` |

### FC-02: Header

| 項目 | 内容 |
|---|---|
| 名前 | Header |
| 種別 | Client Component（認証状態に応じた表示切替） |
| 責務 | ロゴ表示、通知ベル、ログイン/ログアウトボタン、「+ Seed」ボタン |
| 配置 | `apps/web/components/layout/Header.tsx` |

### FC-03: Sidebar

| 項目 | 内容 |
|---|---|
| 名前 | Sidebar |
| 種別 | Client Component（アクティブ状態の管理 + モバイルドロワー） |
| 責務 | 左ナビゲーション（ホーム・フォロー中・注目・探索）、アクティブ項目ハイライト |
| 配置 | `apps/web/components/layout/Sidebar.tsx` |

### FC-04: RightSidebar

| 項目 | 内容 |
|---|---|
| 名前 | RightSidebar |
| 種別 | Server Component |
| 責務 | コンテキストに応じた右パネル表示（About カード / 貢献者一覧） |
| 配置 | `apps/web/components/layout/RightSidebar.tsx` |

### FC-05: PlanterCard

| 項目 | 内容 |
|---|---|
| 名前 | PlanterCard |
| 種別 | Server Component |
| 責務 | フィード上の Planter カード1枚の表示（バッジ・タイトル・タグ・メタ情報・Progress Bar） |
| 配置 | `apps/web/components/planter/PlanterCard.tsx` |

### FC-06: PlanterFeed

| 項目 | 内容 |
|---|---|
| 名前 | PlanterFeed |
| 種別 | Server Component + Client Component（タブ切替） |
| 責務 | フィード表示（新着/人気/開花済みタブ）、PlanterCard のリスト描画、ページネーション |
| 配置 | `apps/web/components/planter/PlanterFeed.tsx` |

### FC-07: PlanterDetail

| 項目 | 内容 |
|---|---|
| 名前 | PlanterDetail |
| 種別 | Server Component（ページロード）+ Client Component（Log 投稿） |
| 責務 | Planter 個別ページ。状態に応じた表示切替（Seed/Sprout: Seed本文+Log一覧、Louge: 記事+Seed折りたたみ+Log一覧） |
| 配置 | `apps/web/app/p/[id]/page.tsx` |

### FC-08: SeedForm

| 項目 | 内容 |
|---|---|
| 名前 | SeedForm |
| 種別 | Client Component |
| 責務 | Seed 投稿フォーム（投稿タイプ選択・タイトル・本文・タグ選択） |
| 配置 | `apps/web/components/seed/SeedForm.tsx` |

### FC-09: LogThread

| 項目 | 内容 |
|---|---|
| 名前 | LogThread |
| 種別 | Client Component |
| 責務 | Log 一覧表示（スレッド形式・ネスト1段返信）、Log 投稿フォーム、AI ファシリテート Log の区別表示 |
| 配置 | `apps/web/components/log/LogThread.tsx` |

### FC-10: TagSelector

| 項目 | 内容 |
|---|---|
| 名前 | TagSelector |
| 種別 | Client Component |
| 責務 | 業界・職種・スキルタグの階層的選択UI。Seed投稿・プロフィール編集で共用 |
| 配置 | `apps/web/components/common/TagSelector.tsx` |

### FC-11: ProgressBar

| 項目 | 内容 |
|---|---|
| 名前 | ProgressBar |
| 種別 | Server Component |
| 責務 | 開花進捗の視覚化バー（3px高さ）。条件A（0〜50%）・条件B（50〜100%）の複合 progress を表示 |
| 配置 | `apps/web/components/planter/ProgressBar.tsx` |

### FC-12: UserProfile

| 項目 | 内容 |
|---|---|
| 名前 | UserProfile |
| 種別 | Server Component（プロフィール表示）+ Client Component（編集モード） |
| 責務 | プロフィール表示（表示名・自己紹介・アバター・タグ・インサイトスコア）、投稿履歴タブ |
| 配置 | `apps/web/app/user/[id]/page.tsx` |

### FC-13: SearchExplore

| 項目 | 内容 |
|---|---|
| 名前 | SearchExplore |
| 種別 | Client Component |
| 責務 | 探索画面。タグフィルタリング + キーワード検索 + Planter 状態フィルタ |
| 配置 | `apps/web/app/explore/page.tsx` |

### FC-14: AuthProvider

| 項目 | 内容 |
|---|---|
| 名前 | AuthProvider |
| 種別 | Client Component（React Context） |
| 責務 | Supabase Auth セッション管理。ログイン状態の保持と JWT トークンの提供 |
| 配置 | `apps/web/components/auth/AuthProvider.tsx` |

---

## Backend Components（FastAPI）

### BC-01: AuthMiddleware

| 項目 | 内容 |
|---|---|
| 名前 | AuthMiddleware |
| 種別 | FastAPI Dependency |
| 責務 | Supabase JWT の検証。リクエストから認証済みユーザーIDを抽出し、各エンドポイントに注入 |
| 配置 | `apps/api/middleware/auth.py` |

### BC-02: PlanterRouter

| 項目 | 内容 |
|---|---|
| 名前 | PlanterRouter |
| 種別 | FastAPI Router |
| 責務 | Planter（Seed）関連の RESTful エンドポイント群（CRUD + フィード取得） |
| 配置 | `apps/api/routers/planters.py` |

### BC-03: LogRouter

| 項目 | 内容 |
|---|---|
| 名前 | LogRouter |
| 種別 | FastAPI Router |
| 責務 | Log 関連の RESTful エンドポイント群（投稿・一覧取得・返信） |
| 配置 | `apps/api/routers/logs.py` |

### BC-04: UserRouter

| 項目 | 内容 |
|---|---|
| 名前 | UserRouter |
| 種別 | FastAPI Router |
| 責務 | ユーザープロフィール関連エンドポイント（取得・更新・投稿履歴） |
| 配置 | `apps/api/routers/users.py` |

### BC-05: SearchRouter

| 項目 | 内容 |
|---|---|
| 名前 | SearchRouter |
| 種別 | FastAPI Router |
| 責務 | 検索・探索エンドポイント（タグフィルタ + キーワード全文検索 + 状態フィルタ） |
| 配置 | `apps/api/routers/search.py` |

### BC-06: FollowRouter

| 項目 | 内容 |
|---|---|
| 名前 | FollowRouter |
| 種別 | FastAPI Router |
| 責務 | フォロー関連エンドポイント（Planter フォロー・ユーザーフォロー・フォロー中フィード） |
| 配置 | `apps/api/routers/follows.py` |

### BC-07: PlanterRepository

| 項目 | 内容 |
|---|---|
| 名前 | PlanterRepository |
| 種別 | Repository（データアクセス層） |
| 責務 | planters テーブルへの CRUD 操作。SQLAlchemy 経由 |
| 配置 | `apps/api/repositories/planter_repo.py` |

### BC-08: LogRepository

| 項目 | 内容 |
|---|---|
| 名前 | LogRepository |
| 種別 | Repository（データアクセス層） |
| 責務 | logs テーブルへの CRUD 操作。SQLAlchemy 経由 |
| 配置 | `apps/api/repositories/log_repo.py` |

### BC-09: UserRepository

| 項目 | 内容 |
|---|---|
| 名前 | UserRepository |
| 種別 | Repository（データアクセス層） |
| 責務 | users テーブルへの CRUD、プロフィール取得。SQLAlchemy 経由 |
| 配置 | `apps/api/repositories/user_repo.py` |

### BC-10: TagRepository

| 項目 | 内容 |
|---|---|
| 名前 | TagRepository |
| 種別 | Repository（データアクセス層） |
| 責務 | tags + 中間テーブルへの CRUD。タグ検索・フィルタリング。SQLAlchemy 経由 |
| 配置 | `apps/api/repositories/tag_repo.py` |

### BC-11: ScoreEngine

| 項目 | 内容 |
|---|---|
| 名前 | ScoreEngine |
| 種別 | Domain Service |
| 責務 | Louge スコアの計算ロジック。条件A（構造充足率）の軽量チェックと条件B（成熟度4観点）の本格スコアリングを実行。ポリシークラスとして閾値を外部設定化 |
| 配置 | `apps/api/services/score_engine.py` |

### BC-12: LougeGenerator

| 項目 | 内容 |
|---|---|
| 名前 | LougeGenerator |
| 種別 | Domain Service |
| 責務 | Vertex AI を呼び出し、Seed + Log 群からパターンランゲージ形式の Louge 記事を生成。開花判定トリガー後に BackgroundTasks で非同期実行 |
| 配置 | `apps/api/services/louge_generator.py` |

### BC-13: InsightScoreCalculator

| 項目 | 内容 |
|---|---|
| 名前 | InsightScoreCalculator |
| 種別 | Domain Service |
| 責務 | Louge 開花時に各 Log 投稿者の貢献度を数値化。insight_score_events への記録 |
| 配置 | `apps/api/services/insight_calculator.py` |

### BC-14: FeedRanker

| 項目 | 内容 |
|---|---|
| 名前 | FeedRanker |
| 種別 | Domain Service |
| 責務 | 「注目」フィードの複合スコア計算（閲覧数 + Log 投稿速度 + 構造充足率） |
| 配置 | `apps/api/services/feed_ranker.py` |

### BC-15: AIFacilitator

| 項目 | 内容 |
|---|---|
| 名前 | AIFacilitator |
| 種別 | Domain Service |
| 責務 | 条件B スコア不足時に AI ファシリテート Log を生成。Vertex AI 呼び出し。`is_ai_generated` フラグ付きで Log に保存 |
| 配置 | `apps/api/services/ai_facilitator.py` |

### BC-16: SupabaseAuthClient

| 項目 | 内容 |
|---|---|
| 名前 | SupabaseAuthClient |
| 種別 | Infrastructure（外部サービスラッパー） |
| 責務 | Supabase Auth API との通信。JWT 公開鍵取得・トークン検証 |
| 配置 | `apps/api/infra/supabase_auth.py` |

### BC-20: FollowRepository

| 項目 | 内容 |
|---|---|
| 名前 | FollowRepository |
| 種別 | Repository（データアクセス層） |
| 責務 | planter_follows / user_follows テーブルへの CRUD。投稿者自動フォロー・フォロー中フィード取得 |
| 配置 | `apps/api/repositories/follow_repo.py` |

### BC-21: NotificationRepository

| 項目 | 内容 |
|---|---|
| 名前 | NotificationRepository |
| 種別 | Repository（データアクセス層） |
| 責務 | notifications テーブルへの書き込み。Planter 状態変化・開花イベントを記録（通知送信はフェーズ2） |
| 配置 | `apps/api/repositories/notification_repo.py` |

### BC-22: ScorePipeline

| 項目 | 内容 |
|---|---|
| 名前 | ScorePipeline |
| 種別 | Orchestration Module（関数集） |
| 責務 | Log 投稿後のスコア計算フローを順番に実行する関数群。BackgroundTasks から呼ばれる。ScoreEngine・LougeGenerator・AIFacilitator をオーケストレーション |
| 配置 | `apps/api/pipelines/score_pipeline.py` |

### BC-17: SupabaseStorageClient

| 項目 | 内容 |
|---|---|
| 名前 | SupabaseStorageClient |
| 種別 | Infrastructure（外部サービスラッパー） |
| 責務 | Supabase Storage API との通信。アバター画像のアップロード・URL 取得 |
| 配置 | `apps/api/infra/supabase_storage.py` |

### BC-18: VertexAIClient

| 項目 | 内容 |
|---|---|
| 名前 | VertexAIClient |
| 種別 | Infrastructure（外部サービスラッパー） |
| 責務 | Vertex AI API との通信を抽象化。ScoreEngine・LougeGenerator・AIFacilitator が利用 |
| 配置 | `apps/api/infra/vertex_ai.py` |

### BC-19: Database

| 項目 | 内容 |
|---|---|
| 名前 | Database |
| 種別 | Infrastructure |
| 責務 | SQLAlchemy AsyncSession の管理。接続プール設定。FastAPI の依存関係注入で提供 |
| 配置 | `apps/api/infra/database.py` |

---

## Database Layer（Supabase / PostgreSQL）

### DB-01: SQLAlchemy Models

| 項目 | 内容 |
|---|---|
| 名前 | Models |
| 責務 | ORM モデル定義（planters, logs, users, tags, follows, notifications, planter_views, louge_score_snapshots, insight_score_events） |
| 配置 | `apps/api/models/` |

### DB-02: Supabase Migrations

| 項目 | 内容 |
|---|---|
| 名前 | Migrations |
| 責務 | DB スキーマのバージョン管理。全テーブル定義・インデックス・RLS ポリシー |
| 配置 | `supabase/migrations/` |
