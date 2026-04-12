# U1 Foundation — Code Generation Plan

## Unit Context

- **ユニット**: U1 Foundation
- **目的**: 全ユニットの土台。認証基盤・DB スキーマ・3カラムレイアウト・プロジェクト構造
- **依存**: なし（最初のユニット）
- **後続ユニット**: U2 Seed, U3 Log & Score, U4 Louge, U5 Feed & Search, U6 User & Follow, U7 Admin

## 参照ドキュメント

- `aidlc-docs/construction/U1-foundation/functional-design/domain-entities.md`
- `aidlc-docs/construction/U1-foundation/functional-design/business-rules.md`
- `aidlc-docs/construction/U1-foundation/functional-design/business-logic-model.md`
- `aidlc-docs/construction/U1-foundation/functional-design/frontend-components.md`
- `CLAUDE.md`（Tech Stack, Code Quality Rules, Design Rules）
- `docs/design-style.md`
- `docs/tags.md`

---

## Generation Steps

### Step 1: Project Structure Setup — Backend (apps/api)

- [x] FastAPI プロジェクトスキャフォールド作成
  - `apps/api/pyproject.toml` — 依存定義（fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, python-jose[cryptography], httpx, supabase, pydantic-settings）
  - `apps/api/app/__init__.py`
  - `apps/api/app/main.py` — FastAPI app factory, CORS, lifespan
  - `apps/api/app/config.py` — pydantic-settings で環境変数管理
  - `apps/api/app/dependencies.py` — get_db, get_current_user, get_optional_user
  - `apps/api/.env.example` — 環境変数テンプレート
- [x] ディレクトリ構造:
  ```
  apps/api/
  ├── pyproject.toml
  ├── .env.example
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── dependencies.py
  │   ├── models/          ← SQLAlchemy models
  │   ├── routers/         ← API endpoints
  │   ├── schemas/         ← Pydantic schemas
  │   ├── services/        ← SupabaseAuthClient, VertexAIClient 等
  │   └── tests/           ← pytest
  ```

### Step 2: Project Structure Setup — Frontend (apps/web)

- [x] Next.js App Router プロジェクト初期化
  - `apps/web/package.json`
  - `apps/web/tsconfig.json` — `strict: true`
  - `apps/web/next.config.ts`
  - `apps/web/tailwind.config.ts` — デザイントークン設定
  - `apps/web/postcss.config.mjs`
  - `apps/web/app/globals.css` — Tailwind directives + カスタム CSS 変数
  - `apps/web/app/layout.tsx` — Root layout (placeholder)
  - `apps/web/app/page.tsx` — Home page (placeholder)
  - `apps/web/.env.example`
- [x] Tailwind デザイントークン（Figma design-system 実測値、frontend-components.md 参照）:
  - Primary: `#29736B`, primary-dark: `#1F3833`, primary-light-bg: `#E0F0ED`, accent: `#00B4CC`
  - Background: bg `#F7F5ED`, bg-card `#FBF9F5`, border `#E5E3DB`
  - Text: text-secondary `#596B66`, text-muted `#99998F`, text-sage `#A6B89E`
  - borderRadius: xs 2px, sm 4px, md 6px, lg 10px
  - fontSize: display 28px, heading-xl 24px, heading-l 18px, heading-m 15px, body-m 13px, body-s 12px, caption 11px
  - icons: lucide-react, size 20px, strokeWidth 1.5
  - fontFamily: Inter + Noto Sans JP

### Step 3: Project Structure Setup — Supabase & Infra

- [x] `supabase/` ディレクトリ作成
  - `supabase/config.toml` — Supabase CLI 設定（placeholder）
- [x] `infra/` ディレクトリ作成
  - `infra/api/Dockerfile` — FastAPI 用
  - `infra/web/Dockerfile` — Next.js 用
- [x] ルートレベル設定
  - `.gitignore` 更新（node_modules, __pycache__, .env, .venv 等）

### Step 4: Database Migration — 全テーブル定義

- [x] `supabase/migrations/00001_create_tables.sql`
  - seed_types（マスタ）
  - users
  - planters
  - logs
  - tags
  - planter_tags
  - user_tags
  - planter_follows
  - user_follows
  - notifications
  - planter_views
  - louge_score_snapshots
  - insight_score_events
  - ai_configs
  - 全インデックス・CHECK 制約・UNIQUE 制約
  - `updated_at` 自動更新トリガー関数

### Step 5: Database Seed — マスタデータ投入

- [x] `supabase/migrations/00002_seed_master_data.sql`
  - seed_types 初期データ（8種）
  - ai_configs 初期データ（12 エントリ）
- [x] `supabase/migrations/00003_seed_tags.sql`
  - `docs/tags.md` 全タグを INSERT（階層構造を parent_tag_id で表現）
  - カテゴリ: industry, occupation, role, situation, skill, knowledge

### Step 6: SQLAlchemy Models

- [x] `apps/api/app/models/__init__.py`
- [x] `apps/api/app/models/base.py` — Base, TimestampMixin, SoftDeleteMixin
- [x] `apps/api/app/models/user.py` — User モデル
- [x] `apps/api/app/models/planter.py` — Planter モデル
- [x] `apps/api/app/models/log.py` — Log モデル
- [x] `apps/api/app/models/tag.py` — Tag, PlanterTag, UserTag モデル
- [x] `apps/api/app/models/follow.py` — PlanterFollow, UserFollow モデル
- [x] `apps/api/app/models/notification.py` — Notification モデル
- [x] `apps/api/app/models/planter_view.py` — PlanterView モデル
- [x] `apps/api/app/models/score.py` — LougeScoreSnapshot, InsightScoreEvent モデル
- [x] `apps/api/app/models/ai_config.py` — AiConfig モデル
- [x] `apps/api/app/models/seed_type.py` — SeedType モデル
- [x] 全モデルに domain-entities.md の制約を反映

### Step 7: Database Connection & Config

- [x] `apps/api/app/database.py` — AsyncEngine, async_sessionmaker, get_db
  - pool_size: 5, max_overflow: 10, pool_timeout: 30, pool_recycle: 1800
- [x] `apps/api/app/config.py` — Settings クラス（pydantic-settings）
  - DATABASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
  - GCP_PROJECT_ID, GCP_LOCATION, GOOGLE_APPLICATION_CREDENTIALS
  - CORS_ORIGINS

### Step 8: SupabaseAuthClient — TDD

- [x] **テスト先行**: `apps/api/app/tests/test_supabase_auth.py`
  - verify_token: 正常 JWT の検証
  - verify_token: 期限切れ JWT の拒否
  - verify_token: 不正署名 JWT の拒否
  - JWKS キャッシュの動作
- [x] **実装**: `apps/api/app/services/supabase_auth.py`
  - SupabaseAuthClient クラス
  - verify_token(), get_user_metadata()
  - JWKS キャッシュ（TTL 1時間）

### Step 9: AuthMiddleware — TDD

- [x] **テスト先行**: `apps/api/app/tests/test_auth_middleware.py`
  - get_current_user: 有効トークンで User 返却
  - get_current_user: トークンなしで 401
  - get_current_user: deleted_at ありで 403
  - get_current_user: 未登録ユーザーで自動作成（BR-02）
  - get_current_user: is_banned ユーザーの書き込み拒否
  - get_optional_user: トークンなしで None 返却
  - get_optional_user: 有効トークンで User 返却
- [x] **実装**: `apps/api/app/dependencies.py`
  - get_current_user(), get_optional_user()
  - BR-01, BR-02 のビジネスルール適用

### Step 10: Health Check & Users Router — TDD

- [x] **テスト先行**: `apps/api/app/tests/test_health.py`
  - GET /health: 200 OK
- [x] **テスト先行**: `apps/api/app/tests/test_users.py`
  - GET /api/v1/users/me: 認証済みでプロフィール返却
  - GET /api/v1/users/me: 未認証で 401
  - PATCH /api/v1/users/me: display_name, bio 更新
  - GET /api/v1/users/{id}: 公開プロフィール取得
- [x] **実装**:
  - `apps/api/app/routers/health.py`
  - `apps/api/app/routers/users.py`
  - `apps/api/app/schemas/user.py` — UserResponse, UserUpdate Pydantic スキーマ
- [x] テスト用フィクスチャ: `apps/api/app/tests/conftest.py`
  - AsyncClient, テスト用 DB セッション, JWT モック

### Step 11: FastAPI Main App Assembly

- [x] `apps/api/app/main.py` 完成
  - CORS 設定
  - Router 登録（health, users）
  - 構造化 JSON ログ設定
  - lifespan（DB エンジン起動/停止）

### Step 12: Frontend — Supabase Client & AuthProvider

- [x] `apps/web/lib/supabase.ts` — Supabase クライアント初期化
- [x] `apps/web/lib/api-client.ts` — FastAPI 呼び出し用 HTTP クライアント（JWT 自動付与）
- [x] `apps/web/contexts/auth-context.tsx` — AuthProvider (FC-14)
  - AuthContext type 定義
  - signIn(provider), signOut()
  - onAuthStateChange 監視
  - セッション復元

### Step 13: Frontend — LayoutShell (FC-01)

- [x] Figma デザインシステム参照（nodeId: 95:34）
- [x] Figma Home 画面参照（nodeId: 12:3）
- [x] `apps/web/app/layout.tsx` — LayoutShell 実装
  - 3カラムレスポンシブレイアウト（xl: 3col, md: 2col, sm: 1col）
  - AuthProvider ラップ
  - Inter + Noto Sans JP フォント設定
  - `data-testid` 付与

### Step 14: Frontend — Header (FC-02)

- [x] Figma 参照（nodeId: 12:3 から Header 部分）
- [x] `apps/web/components/header.tsx`
  - ロゴ（蓮の花アイコン + "Works Logue"）
  - "+Seed" CTA ボタン
  - ログインボタン / ユーザーアバター + ドロップダウン
  - モバイル: ハンバーガーメニュー + アイコンのみ
  - `data-testid` 付与

### Step 15: Frontend — Sidebar (FC-03)

- [x] `apps/web/components/sidebar.tsx`
  - ナビ項目: ホーム, フォロー中, 注目, 探索（Lucide アイコン）
  - アクティブ状態ハイライト（usePathname）
  - モバイルドロワー（fixed overlay）
  - `data-testid` 付与

### Step 16: Frontend — RightSidebar & About Card (FC-04)

- [x] `apps/web/components/right-sidebar.tsx`
  - About Works Logue カード
  - Stats（Seeds / Louges / Contributors — placeholder 値）
  - "Seed を投稿する" CTA
  - `hidden xl:block` レスポンシブ
  - `data-testid` 付与

### Step 17: Frontend — Login Page

- [x] Figma Login 画面参照（nodeId: 212:8）
- [x] `apps/web/app/login/page.tsx`
  - Works Logue ロゴ
  - "Google でログイン" ボタン
  - メール + パスワードフォーム
  - サインアップ切替
  - ?redirect= パラメータ対応
  - `data-testid` 付与

### Step 18: Infrastructure — Dockerfile & Config

- [x] `infra/api/Dockerfile` — Python FastAPI (multi-stage build)
- [x] `infra/web/Dockerfile` — Next.js (multi-stage build)
- [x] `apps/api/.env.example` 最終版
- [x] `apps/web/.env.example` 最終版

### Step 19: Documentation Summary

- [x] `aidlc-docs/construction/U1-foundation/code/code-summary.md`
  - 作成ファイル一覧
  - アーキテクチャ概要
  - ローカル開発手順

---

## テスト戦略（CLAUDE.md 準拠）

| 対象 | アプローチ | ツール |
|---|---|---|
| SupabaseAuthClient | TDD（テスト先行） | pytest + JWT モック |
| AuthMiddleware | TDD（テスト先行） | pytest + JWT モック |
| Users エンドポイント | TDD（テスト先行） | pytest + httpx AsyncClient |
| Health エンドポイント | TDD（テスト先行） | pytest + httpx AsyncClient |
| Frontend コンポーネント | Figma 参照で実装 → E2E は後続 | Playwright（Build & Test で） |

## Figma 参照計画

| Step | nodeId | 画面 |
|---|---|---|
| Step 13 | 95:34 | デザインシステム（カラー・タイポ・スペーシング） |
| Step 13 | 12:3 | Home（3カラムレイアウト確認） |
| Step 14 | 12:3 | Home（Header 部分） |
| Step 17 | 212:8 | Login |

## 合計

- **19 ステップ**
- Backend: Step 1, 4-11（9ステップ）
- Frontend: Step 2, 12-17（7ステップ）
- Infra: Step 3, 18（2ステップ）
- Docs: Step 19（1ステップ）
