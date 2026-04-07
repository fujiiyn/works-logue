# Unit of Work — Works Logue MVP

## 分解方針

- **Feature Slice（縦割り）**: 各ユニットは Frontend + Backend + DB を垂直に含む
- **DB スキーマ**: U1 で全テーブルを一括作成。後続ユニットは DB に依存せず実装に集中
- **Figma デザイン**: 全画面を一括で事前作成してから実装に入る
- **実装順序**: U1 → U2 → U3 → U4 → U5 → U6 → U7（依存関係順）

---

## U1: Foundation

**目的**: 全ユニット共通の基盤を構築。DB スキーマ全量・認証・レイアウト Shell・インフラ設定。

### スコープ

| レイヤー | 内容 |
|---|---|
| Database | 全テーブル定義（seed_types, planters, logs, users, tags, follows, notifications, planter_views, louge_score_snapshots, insight_score_events + 中間テーブル）、マイグレーション、SQLAlchemy モデル全量、seed_types 初期データ投入 |
| Backend | FastAPI アプリ初期化、AuthMiddleware（JWT検証）、Database（接続プール）、SupabaseAuthClient、SupabaseStorageClient、VertexAIClient |
| Frontend | Next.js プロジェクト初期化、LayoutShell（3カラム）、Header、Sidebar、RightSidebar、AuthProvider |
| Infra | Dockerfile（web/api）、環境変数設定、Supabase 接続設定 |

### 含まれるコンポーネント

- FC-01 LayoutShell, FC-02 Header, FC-03 Sidebar, FC-04 RightSidebar, FC-14 AuthProvider
- BC-01 AuthMiddleware, BC-16 SupabaseAuthClient, BC-17 SupabaseStorageClient, BC-18 VertexAIClient, BC-19 Database, BC-21 NotificationRepository
- DB-01 Models（全量）, DB-02 Migrations（全量）

### 完了条件

- `supabase/migrations/` に全テーブルのマイグレーションが存在
- FastAPI が起動し、認証付きエンドポイントのスケルトンが動作
- Next.js が起動し、3カラムレイアウトが表示される
- Supabase Auth でログイン/ログアウトが動作

---

## U2: Seed

**目的**: Seed 投稿と基本フィード（新着タブ）を実装。ユーザーが最初に体験するコアフロー。

### スコープ

| レイヤー | 内容 |
|---|---|
| Backend | PlanterRouter（CRUD + 新着フィード）、PlanterRepository、TagRepository |
| Frontend | SeedForm、TagSelector、PlanterCard、PlanterFeed（新着タブのみ）、ProgressBar |

### 含まれるコンポーネント

- FC-05 PlanterCard, FC-06 PlanterFeed（新着タブ）, FC-08 SeedForm, FC-10 TagSelector, FC-11 ProgressBar
- BC-02 PlanterRouter, BC-07 PlanterRepository, BC-10 TagRepository

### 依存

- U1（Foundation）: DB スキーマ、認証、レイアウト

### 完了条件

- ログイン済みユーザーが Seed を投稿できる
- ホームフィード（新着タブ）に Seed がカード形式で表示される
- タグ選択 UI が機能する
- 非ログインユーザーは閲覧のみ可能

---

## U3: Log & Score

**目的**: Log 投稿、スコアエンジン、Planter 状態遷移、AI ファシリテートを実装。成長サイクルのコア。

### スコープ

| レイヤー | 内容 |
|---|---|
| Backend | LogRouter、LogRepository、ScoreEngine（条件A/B）、AIFacilitator、ScorePipeline（オーケストレーション） |
| Frontend | PlanterDetail（Seed/Sprout 表示）、LogThread（スレッド表示 + 投稿フォーム） |

### 含まれるコンポーネント

- FC-07 PlanterDetail（Seed/Sprout 状態）, FC-09 LogThread
- BC-03 LogRouter, BC-08 LogRepository, BC-11 ScoreEngine, BC-15 AIFacilitator, BC-22 ScorePipeline

### 依存

- U1（Foundation）: DB、認証、VertexAIClient
- U2（Seed）: PlanterRepository、PlanterCard（状態遷移の反映）

### 完了条件

- Log を投稿するとスコアが再計算される
- 条件A の充足率が ProgressBar に反映される
- Planter の状態が seed → sprout に遷移する
- 条件B 不足時に AI ファシリテート Log が投稿される
- louge_score_snapshots にスコア履歴が保存される

---

## U4: Louge

**目的**: Louge 開花（AI 記事生成）とインサイトスコア計算を実装。集合知の結晶化。

### スコープ

| レイヤー | 内容 |
|---|---|
| Backend | LougeGenerator（Vertex AI 記事生成）、InsightScoreCalculator |
| Frontend | PlanterDetail（Louge 状態: 記事表示 + Seed 折りたたみ + 貢献者一覧） |

### 含まれるコンポーネント

- FC-07 PlanterDetail（Louge 状態の拡張）
- BC-12 LougeGenerator, BC-13 InsightScoreCalculator

### 依存

- U1（Foundation）: VertexAIClient、NotificationRepository
- U3（Log & Score）: ScorePipeline（開花トリガー）、ScoreEngine（条件判定）

### 完了条件

- 条件A AND 条件B を突破すると Louge 記事が生成される
- Planter の状態が sprout → louge に遷移する
- Louge ページにパターンランゲージ形式の記事が表示される
- 貢献者のインサイトスコアが更新される
- 通知イベントが DB に記録される

---

## U5: Feed & Search

**目的**: フィードの拡張（注目・開花済みタブ）と探索・検索機能を実装。

### スコープ

| レイヤー | 内容 |
|---|---|
| Backend | SearchRouter、FeedRanker、PlanterRouter 拡張（注目/開花済みタブ）、planter_views 集計 |
| Frontend | PlanterFeed 拡張（注目/開花済みタブ）、SearchExplore |

### 含まれるコンポーネント

- FC-06 PlanterFeed（タブ拡張）, FC-13 SearchExplore
- BC-05 SearchRouter, BC-14 FeedRanker

### 依存

- U1（Foundation）: DB
- U2（Seed）: PlanterRepository、PlanterFeed ベース

### 完了条件

- 注目タブが複合スコア（閲覧数 + Log 速度 + 構造充足率）でランキング表示
- 開花済みタブが Louge のみフィルタ表示
- 探索画面でタグフィルタ + キーワード検索 + 状態フィルタが機能

---

## U6: User & Follow

**目的**: ユーザープロフィールとフォロー機能を実装。

### スコープ

| レイヤー | 内容 |
|---|---|
| Backend | UserRouter、UserRepository、FollowRouter、FollowRepository |
| Frontend | UserProfile（表示・編集・投稿履歴・インサイトスコア） |

### 含まれるコンポーネント

- FC-12 UserProfile
- BC-04 UserRouter, BC-06 FollowRouter, BC-09 UserRepository, BC-20 FollowRepository

### 依存

- U1（Foundation）: DB、認証、SupabaseStorageClient（アバター）
- U2（Seed）: PlanterCard（フォロー中フィード表示）

### 完了条件

- プロフィールページに表示名・自己紹介・アバター・タグ・インサイトスコアが表示
- プロフィール編集が機能する
- Planter フォロー / ユーザーフォローが機能する
- フォロー中フィードに結果が表示される

---

## U7: Admin

**目的**: 管理者画面。ユーザー BAN/解除、Planter アーカイブ・削除、マスタデータ管理。

### スコープ

| レイヤー | 内容 |
|---|---|
| Backend | AdminRouter（ユーザー BAN/解除、Planter アーカイブ/削除、seed_types CRUD、tags CRUD）、AdminMiddleware（role=admin チェック） |
| Frontend | 管理画面（/admin 配下、admin 専用レイアウト） |

### 依存

- U1（Foundation）: DB スキーマ、認証（role チェック追加）

### 完了条件

- admin ユーザーがユーザーを BAN/解除できる
- admin ユーザーが Planter をアーカイブ・削除できる
- admin ユーザーが seed_types・tags のマスタデータを管理できる
- 非 admin ユーザーは /admin にアクセスできない

---

## コード構成戦略（Greenfield）

```
works-logue/
├── apps/
│   ├── web/                          ← Next.js (App Router)
│   │   ├── app/
│   │   │   ├── layout.tsx            ← FC-01 LayoutShell
│   │   │   ├── page.tsx              ← ホームフィード
│   │   │   ├── p/[id]/page.tsx       ← FC-07 PlanterDetail
│   │   │   ├── seed/new/page.tsx     ← FC-08 SeedForm
│   │   │   ├── explore/page.tsx      ← FC-13 SearchExplore
│   │   │   ├── user/[id]/page.tsx    ← FC-12 UserProfile
│   │   │   └── login/page.tsx        ← ログインページ
│   │   ├── components/
│   │   │   ├── layout/               ← Header, Sidebar, RightSidebar
│   │   │   ├── planter/              ← PlanterCard, PlanterFeed, ProgressBar
│   │   │   ├── seed/                 ← SeedForm
│   │   │   ├── log/                  ← LogThread
│   │   │   ├── auth/                 ← AuthProvider
│   │   │   └── common/               ← TagSelector
│   │   ├── lib/                      ← API クライアント、ユーティリティ
│   │   └── styles/                   ← グローバルCSS、Tailwind設定
│   │
│   └── api/                          ← FastAPI
│       ├── main.py                   ← アプリ初期化
│       ├── routers/                  ← BC-02~06 Router 層
│       ├── services/                 ← BC-11~15 Service 層
│       ├── repositories/             ← BC-07~10, 20, 21 Repository 層
│       ├── pipelines/                ← BC-22 ScorePipeline
│       ├── models/                   ← DB-01 SQLAlchemy Models
│       ├── schemas/                  ← Pydantic リクエスト/レスポンス
│       ├── middleware/               ← BC-01 AuthMiddleware
│       └── infra/                    ← BC-16~19 Infrastructure
│
├── supabase/
│   └── migrations/                   ← DB-02 マイグレーション
│
├── infra/                            ← Dockerfile, Cloud Run 設定
└── docs/                             ← 設計ドキュメント
```
