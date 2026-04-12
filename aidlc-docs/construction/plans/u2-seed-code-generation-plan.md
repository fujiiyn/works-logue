# U2 Seed — Code Generation Plan

## Unit Context

- **Unit**: U2 Seed
- **Purpose**: Seed 投稿と基本フィード（新着タブ）、オンボーディングフロー。ユーザーが最初に体験するコアフロー
- **Dependencies (U1 Foundation)**:
  - DB schema: planters, tags, planter_tags, seed_types, planter_follows, user_tags
  - Auth: get_current_user, get_optional_user
  - Layout: LayoutShell, Header, Sidebar, RightSidebar
  - API client: lib/api-client.ts
  - Auth context: contexts/auth-context.tsx
  - Models: User, Planter, Tag, SeedType, PlanterTag, UserTag, PlanterFollow
- **After this unit**: U3 Log & Score

## Reference Documents

- `aidlc-docs/construction/u2-seed/functional-design/domain-entities.md`
- `aidlc-docs/construction/u2-seed/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u2-seed/functional-design/business-rules.md`
- `aidlc-docs/construction/u2-seed/functional-design/frontend-components.md`
- `CLAUDE.md` (Tech Stack, Code Quality Rules, Design Rules, Figma MCP)

---

## Generation Steps

### Step 1: Database Migration -- onboarded_at

- [x] `supabase/migrations/00004_add_onboarded_at.sql`
  - `ALTER TABLE users ADD COLUMN onboarded_at TIMESTAMPTZ;`
- [x] `apps/api/app/models/user.py` -- User model に `onboarded_at` カラム追加

### Step 2: Backend Schemas -- Planter, SeedType, Tag

- [x] `apps/api/app/schemas/planter.py`
  - `PlanterCreateRequest` (title, body, seed_type_id, tag_ids)
  - `PlanterResponse` (full detail with body)
  - `PlanterCardResponse` (feed card, no body)
  - `CursorPaginatedResponse[T]` (items, next_cursor, has_next)
- [x] `apps/api/app/schemas/seed_type.py`
  - `SeedTypeResponse` (id, slug, name, description)
- [x] `apps/api/app/schemas/tag.py`
  - `TagResponse` (id, name, category)
  - `TagTreeNode` (id, name, category, is_leaf, children)
- [x] `apps/api/app/schemas/user.py` 更新
  - `UserResponse` に `onboarded_at` 追加
  - `UserUpdate` に `tag_ids`, `complete_onboarding` 追加
  - `UserPublicResponse` は変更なし（既に必要フィールドあり）

### Step 3: Backend Repository -- PlanterRepository (TDD)

- [x] **Test**: `apps/api/app/tests/test_planter_repository.py`
  - create: Planter 作成成功
  - get_by_id: 存在する Planter 取得
  - get_by_id: deleted_at ありで None
  - get_by_id: 存在しない ID で None
  - list_recent: created_at DESC ソート
  - list_recent: cursor ベースページネーション
  - list_recent: deleted_at / archived 除外
  - list_recent: limit + 1 件取得で has_next 判定
- [x] **Impl**: `apps/api/app/repositories/planter_repository.py`
  - `PlanterRepository` クラス
  - `create()`, `get_by_id()`, `list_recent()`

### Step 4: Backend Repository -- TagRepository, FollowRepository (TDD)

- [x] **Test**: `apps/api/app/tests/test_tag_repository.py`
  - list_by_category: カテゴリ指定で取得
  - list_by_category: カテゴリ未指定で全取得
  - list_by_category: is_active=false 除外
  - get_by_ids: 複数 ID 一括取得
  - attach_to_planter: PlanterTag 一括 INSERT
  - replace_user_tags: UserTag 全置換
- [x] **Impl**: `apps/api/app/repositories/tag_repository.py`
  - `TagRepository` クラス
  - `list_by_category()`, `get_by_ids()`, `attach_to_planter()`, `replace_user_tags()`
- [x] **Test**: `apps/api/app/tests/test_follow_repository.py`
  - follow_planter: PlanterFollow INSERT 成功
  - follow_planter: 重複時のハンドリング
- [x] **Impl**: `apps/api/app/repositories/follow_repository.py`
  - `FollowRepository` クラス
  - `follow_planter()`

### Step 5: Backend Router -- SeedType / Tag Endpoints (TDD)

- [x] **Test**: `apps/api/app/tests/test_seed_types.py`
  - GET /api/v1/seed-types: 200 + list of active seed types (sort_order ASC)
  - GET /api/v1/seed-types: is_active=false 除外
- [x] **Impl**: `apps/api/app/routers/seed_types.py`
  - `GET /api/v1/seed-types`
- [x] **Test**: `apps/api/app/tests/test_tags.py`
  - GET /api/v1/tags: 200 + tree structure
  - GET /api/v1/tags?category=occupation: カテゴリフィルタ
  - GET /api/v1/tags: is_active=false 除外
  - ツリー構築ロジック（parent-child 関係の検証）
- [x] **Impl**: `apps/api/app/routers/tags.py`
  - `GET /api/v1/tags`
  - `build_tree()` ヘルパー関数

### Step 6: Backend Router -- Planter Endpoints (TDD)

- [x] **Test**: `apps/api/app/tests/test_planters.py`
  - POST /api/v1/planters: 201 + PlanterResponse (正常系)
  - POST /api/v1/planters: 401 未認証
  - POST /api/v1/planters: 403 BAN ユーザー
  - POST /api/v1/planters: 400 invalid_seed_type
  - POST /api/v1/planters: 400 invalid_tags (non-leaf, inactive)
  - POST /api/v1/planters: 422 title empty / too long
  - POST /api/v1/planters: 422 body empty / too long
  - POST /api/v1/planters: 自動フォロー確認
  - GET /api/v1/planters: 200 + CursorPaginatedResponse
  - GET /api/v1/planters: カーソルページネーション
  - GET /api/v1/planters: 非認証でも取得可
  - GET /api/v1/planters/{id}: 200 + PlanterResponse
  - GET /api/v1/planters/{id}: 404 not found
  - GET /api/v1/planters/{id}: deleted_at ありで 404
- [x] **Impl**: `apps/api/app/routers/planters.py`
  - `POST /api/v1/planters` (create_planter)
  - `GET /api/v1/planters` (list_planters)
  - `GET /api/v1/planters/{planter_id}` (get_planter)
- [x] `apps/api/app/main.py` -- router 登録追加 (planters, seed_types, tags)

### Step 7: Backend -- Users Router 拡張 (TDD)

- [x] **Test**: `apps/api/app/tests/test_users.py` 追加テスト
  - PATCH /api/v1/users/me: tag_ids 設定（UserTag 全置換）
  - PATCH /api/v1/users/me: complete_onboarding=true で onboarded_at 設定
  - PATCH /api/v1/users/me: complete_onboarding 時 display_name 必須検証
  - PATCH /api/v1/users/me: invalid tag_ids (non-leaf, inactive) で 400
- [x] **Impl**: `apps/api/app/routers/users.py` 更新
  - PATCH /api/v1/users/me に tag_ids / complete_onboarding ロジック追加
- [x] `apps/api/app/schemas/user.py` 更新
  - UserResponse に onboarded_at
  - UserUpdate に tag_ids, complete_onboarding

### Step 8: Backend -- conftest 更新

- [x] `apps/api/app/tests/conftest.py` 更新
  - Repository テスト用フィクスチャ追加（test DB に SeedType / Tag マスタデータ投入）
  - Planter 作成用ヘルパーフィクスチャ

### Step 9: Frontend -- Figma 参照 & 共通コンポーネント

- [x] Figma 参照: Home 画面 (nodeId: 12:3) -- PlanterCard, PlanterFeed のデザイン確認
- [x] Figma 参照: Seed Detail (nodeId: 57:29) -- PlanterDetail のデザイン確認
- [x] Figma 参照: Seed 投稿 (nodeId: 78:6) -- SeedForm, TagSelector のデザイン確認
- [x] `apps/web/components/planter/ProgressBar.tsx` -- FC-11
  - progress: 0.0-1.0, status に応じたスタイル
  - data-testid 付与

### Step 10: Frontend -- PlanterCard & PlanterFeed

- [x] `apps/web/components/planter/PlanterCard.tsx` -- FC-05
  - Stage Badge, SeedType, Avatar, UserName, Time, Title, Tags, Meta, ProgressBar
  - カード全体リンク (/p/{id})
  - data-testid 付与
- [x] `apps/web/components/planter/PlanterFeed.tsx` -- FC-06
  - 3タブ: 新着(active) / 注目(coming soon) / 開花済み(coming soon)
  - Intersection Observer で無限スクロール
  - 空状態 UI
  - data-testid 付与

### Step 11: Frontend -- Home ページ更新

- [x] `apps/web/app/page.tsx` 更新
  - placeholder を PlanterFeed コンポーネントに置き換え
- [x] `apps/web/components/right-sidebar.tsx` 更新（必要に応じて）

### Step 12: Frontend -- TagSelector

- [x] `apps/web/components/common/TagSelector.tsx` -- FC-10
  - 6カテゴリタブ (industry / occupation / role / situation / skill / knowledge)
  - ツリービュー: Chevron 展開/折りたたみ、チェックボックス (leaf/parent)
  - 親チェック: 全子選択/indeterminate/未選択
  - 選択済みチップ (x で削除)
  - Props: selectedTagIds, onTagsChange, categories?
  - GET /api/v1/tags で全タグ取得 & キャッシュ
  - data-testid 付与

### Step 13: Frontend -- SeedForm & 投稿ページ

- [x] `apps/web/components/seed/SeedForm.tsx` -- FC-08
  - SeedType グリッド (2col x 4row)
  - Title input (max 200), Body textarea (max 10000)
  - TagSelector 連携 (右サイドバー or 本体内)
  - Client-side validation
  - POST /api/v1/planters → 成功時 /p/{id} へ遷移
  - data-testid 付与
- [x] `apps/web/app/seed/new/page.tsx`
  - SeedForm をメインエリアに配置
  - 認証チェック（未ログイン → /login?redirect=/seed/new）

### Step 14: Frontend -- PlanterDetail ページ

- [x] Figma 参照: Seed Detail (nodeId: 57:29)
- [x] `apps/web/app/p/[id]/page.tsx`
  - Server Component: GET /api/v1/planters/{id}
  - Stage Badge, SeedType, Title, User info, Body, Tags, ProgressBar
  - 右サイドバー: スコア表示 (progress, log_count, contributor_count, status)
  - 404 → notFound()
  - data-testid 付与

### Step 15: Frontend -- OnboardingPage

- [x] Figma 参照: Profile Setup (nodeId: 271:161)
- [x] `apps/web/app/onboarding/page.tsx`
  - Display name (required), Bio (optional)
  - TagSelector (全6カテゴリ)
  - PATCH /api/v1/users/me (complete_onboarding: true)
  - 成功時: redirect パラメータ先へ遷移
  - data-testid 付与

### Step 16: Frontend -- Auth Context 拡張

- [x] `apps/web/contexts/auth-context.tsx` 更新
  - AppUser に onboarded_at 追加
  - useEffect でオンボーディングリダイレクト判定
    - 未オンボーディング + 非閲覧ページ → /onboarding?redirect=...
    - 閲覧ページ (/, /p/*)、/login, /onboarding はスキップ
- [x] `apps/web/app/login/page.tsx` 更新（必要に応じて redirect チェーン対応）

### Step 17: Documentation Summary

- [x] `aidlc-docs/construction/u2-seed/code/code-summary.md`
  - 作成/更新ファイル一覧
  - API エンドポイント一覧
  - テストカバレッジサマリ

---

## Test Strategy (CLAUDE.md)

| Target | Approach | Tool |
|---|---|---|
| PlanterRepository | TDD | pytest |
| TagRepository | TDD | pytest |
| FollowRepository | TDD | pytest |
| Planter Endpoints | TDD | pytest + httpx AsyncClient |
| SeedType Endpoints | TDD | pytest + httpx AsyncClient |
| Tag Endpoints | TDD | pytest + httpx AsyncClient |
| Users Endpoints (extension) | TDD | pytest + httpx AsyncClient |
| Frontend Components | Figma reference -> implement | Playwright (Build & Test) |

## Figma Reference Plan

| Step | nodeId | Screen |
|---|---|---|
| Step 9 | 12:3 | Home (PlanterCard, Feed layout) |
| Step 9 | 57:29 | Seed Detail |
| Step 9 | 78:6 | Seed New (SeedForm, TagSelector) |
| Step 14 | 57:29 | Seed Detail (detailed) |
| Step 15 | 271:161 | Profile Setup (Onboarding) |

## Summary

- **17 steps**
- Backend: Step 1-8 (8 steps) -- Migration, Schemas, Repositories (TDD), Routers (TDD), conftest
- Frontend: Step 9-16 (8 steps) -- Figma ref, Components, Pages, Auth extension
- Docs: Step 17 (1 step)
