# U7 Admin — Code Generation Plan

## Unit Context

- **Unit**: U7 Admin
- **依存**: U1 Foundation (User model, AuthMiddleware, get_current_user の汎用 BAN ガード), U2 Seed (planters), U3 Log & Score (logs, seed→sprout 自動昇格), U6 User & Follow (UserPublicResponse, AuthContext)
- **新規 DB マイグレーション**: **なし** (Q4=B / Q5=B 確定。`role` / `is_banned` / `banned_at` / `ban_reason` / `deleted_at` は `00001_create_tables.sql` 時点で既存)
- **Figma 真実源**: page `admin` (nodeId `420:159`)
- **Functional Design**: `aidlc-docs/construction/u7-admin/functional-design/` (domain-entities, business-rules, business-logic-model, frontend-components の 4 本)

## Code Location

- **API**: `apps/api/app/` (dependencies, routers, repositories, schemas)
- **API Tests**: `apps/api/app/tests/` (※ プロジェクト実体に合わせる。U6 plan の `apps/api/tests/` は誤記)
- **Web**: `apps/web/` (app, components, contexts, lib)
- **Web E2E**: `apps/web/e2e/`
- **Migrations**: 追加なし
- **Documentation**: `aidlc-docs/construction/u7-admin/code/` (markdown summaries のみ)
- **Operations doc**: `docs/operations.md` (新規)

## Design Decisions（Functional Design からの確定事項の再掲）

| # | 決定 | 根拠 |
|---|---|---|
| D1 | 新規 migration を切らない | Q4=B, Q5=B。AdminAuditLog テーブルは作らず Cloud Logging で代替 |
| D2 | `/admin` 画面・`/api/v1/admin/*` API は非 admin に **404** を返す | Q10=B。admin 画面の存在を秘匿 (BR-A01) |
| D3 | BAN ガードは `apps/api/app/dependencies.py:87-89` の汎用 ガードを再利用、個別ハンドラへ追加実装しない | 二重 TDD 防止 (Functional Design §7) |
| D4 | AdminLayout は `app/layout.tsx` を継承しない独立シェル (RightSidebar / Header / Sidebar 全部不使用) | BR-A19, Q6=A |
| D5 | BannedBanner は `app/layout.tsx` 直下に配置。AdminLayout には自動的に出ない (継承しないため) | BR-A02b |
| D6 | Server Component で auth を解決するため `apps/web/lib/auth-server.ts` を新設、`@supabase/ssr` を依存に追加 | FC-A01 前提 |
| D7 | typed confirmation はクライアント・サーバー両方で検証 (trim あり、大小文字区別あり) | BR-A12 |
| D8 | Planter 一覧の「すべて」フィルタは `status IN ('seed','sprout','louge') AND deleted_at IS NULL` (= フィードに出ているもののみ) | BR-A09b |
| D9 | アーカイブ復元時の status は MVP では `seed` 固定 (後続 Log で自動 sprout 昇格) | BR-A10 |
| D10 | SeedType の admin 操作は `description` 更新と `is_active` トグルのみ。`slug` / `name` / `sort_order` の編集 API は提供しない | BR-A15, Q4=B |
| D11 | Cloud Logging に `request_id` ContextVar を導入し、`admin.access` ログと操作ログを trace 紐付け | BR-A14 |
| D12 | `GET /users/me` のレスポンスに `is_banned` / `deleted_at` を追加 (UserResponse 拡張) | Functional Design §8、AuthContext と auth-server で必要 |
| D13 | TDD 必須 (CLAUDE.md): API ハンドラ・Repository・middleware は pytest 先行 (Red→Green→Refactor) | プロジェクト規約 |
| D14 | フロントは Figma 参照で実装後 Playwright E2E (admin 画面の smoke 1 本のみ MVP) | プロジェクト規約 |
| D15 | `is_self` 判定は API 側で付与する (Client へ admin user を引き渡さない) | FC-A04 責務分担 |
| D16 | フロント admin 画面は **デスクトップ専用** (min-width: 1024px)。モバイル幅では案内メッセージのみ | FC レスポンシブ方針 |
| D17 | Admin の全 admin 操作 API ハンドラから操作ログを `structlog` 経由で 1 回出力 | BR-A14 |
| D18 | AdminRepository は既存 UserRepository / PlanterRepository の上に薄いラッパーとして作る | Functional Design §6 |

---

## Steps

### Phase 1: API スキーマ拡張 (UserMeResponse)

- [x] **Step 1**: `UserResponse` に `is_banned: bool` と `deleted_at: datetime | None` を追加
  - 修正: `apps/api/app/schemas/user.py`
  - `UserResponse` のみ拡張 (UserPublicResponse は対象外。他人から `is_banned` は見せない)
  - TDD: `apps/api/app/tests/test_users.py` の `GET /users/me` テストに「`is_banned` / `deleted_at` フィールドが含まれる」アサーションを追加 (Red→Green)

### Phase 2: request_id ContextVar / 構造化ログ基盤

- [x] **Step 2**: request_id ミドルウェア + ContextVar
  - 新規: `apps/api/app/middleware/__init__.py`、`apps/api/app/middleware/request_id.py`
  - FastAPI middleware で UUID v7 (or v4) を生成、`ContextVar` に格納
  - structlog の `contextvars.bind_contextvars(request_id=...)` で全ログに自動付与
  - `apps/api/app/main.py` の `app.add_middleware(CORSMiddleware, ...)` の **後** に `app.add_middleware(RequestIdMiddleware)` を追加 (FastAPI の `add_middleware` は LIFO スタックのため、後に登録した方が **外側** = リクエスト到達順で先に走る。CORS プリフライトにも request_id を付けるため外側化)
  - TDD: 新規 `apps/api/app/tests/test_request_id_middleware.py` で「同一リクエスト内で request_id が共有される」「リクエスト間では別」を検証 (構造化ログのキャプチャ)

### Phase 3: AdminMiddleware (require_admin)

- [x] **Step 3**: `require_admin` Depends 関数とテスト
  - 新規: `apps/api/app/tests/test_admin_middleware.py` (TDD Red)
  - 検証ケース:
    - 未ログイン → 404 Not Found (401 ではない)
    - 一般ユーザー (role=user) → 404
    - BAN 中 admin → 404
    - deleted_at IS NOT NULL の admin → 404
    - 正常 admin → 通過 (200)
    - 通過時に Cloud Logging に `event=admin.access` が 1 回出力される (structlog cap_logs)
  - 新規: `apps/api/app/dependencies_admin.py` (`require_admin` を独立ファイルに置き dependencies.py を膨張させない)
    - `Depends(get_current_user)` の上に `role=='admin' AND not is_banned AND deleted_at IS NULL` を強制
    - 全条件不一致 → `HTTPException(404, detail="Not Found")` (admin 存在秘匿)
    - 通過時 `structlog.get_logger().info("admin.access", actor_user_id=..., path=..., method=...)`

### Phase 4: AdminRepository (TDD)

- [x] **Step 4**: AdminRepository テスト
  - 新規: `apps/api/app/tests/test_admin_repository.py`
  - メソッド別テストケース:
    - `get_dashboard_stats()`: 4 つの COUNT (total_users, total_planters, new_planters_today=JST 本日, pending_louge_count=sprout 全件)
    - `list_users(q, status, page, per_page)`: display_name 部分一致 (ILIKE 大小無視、q_pattern は `f"%{q.strip().lower()}%"` で前後空白除去)、status フィルタ (all/normal/banned)、ソート `created_at DESC`、ページング、planter_count / log_count の集計マージ (N+1 回避を 2 本の集計クエリで)、deleted_at IS NULL のみ
    - `ban_user(user, reason)`: 同一 UPDATE で 3 列更新 (BR-A03)、冪等 (既に BAN 中ならそのまま)
    - `unban_user(user)`: 同一 UPDATE で 3 列を NULL/false に戻す、冪等
    - `list_planters(q, status, page, per_page)`: q は `title ILIKE :q_pattern`（q_pattern は `f"%{q.strip().lower()}%"`）。status='all' は seed/sprout/louge AND deleted_at IS NULL、'deleted' は deleted_at IS NOT NULL、'archived' は status='archived'、その他は status=:status。ソートは status='deleted' のとき deleted_at DESC、それ以外 updated_at DESC。author / seed_type_name JOIN
    - `archive_planter(planter)`: status='archived'、updated_at=now()、冪等
    - `restore_planter(planter)`: status='archived' 以外なら例外、復元後は status='seed' (BR-A10)
    - `soft_delete_planter(planter)`: deleted_at=now()
    - `list_seed_types(status)`: ORDER BY sort_order ASC、status フィルタ (all/active/inactive)
    - `update_seed_type_description(seed_type, description)`: description のみ更新
    - `toggle_seed_type_active(seed_type)`: is_active を反転

- [x] **Step 5**: AdminRepository 実装
  - 新規: `apps/api/app/repositories/admin_repository.py`
  - 既存 UserRepository / PlanterRepository を呼び出すラッパーとして実装、admin 専用の集計と検索のみ本リポジトリに置く
  - `_q_pattern(q: str) -> str`: `f"%{q.strip().lower()}%"` (ILIKE と組み合わせる)
  - JST 判定: `func.timezone('Asia/Tokyo', func.now())` → `date_trunc('day', ...)`
  - 全テスト Green まで反復

### Phase 5: Admin スキーマ

- [x] **Step 6**: Admin Pydantic スキーマ
  - 新規: `apps/api/app/schemas/admin.py`
  - `AdminStatsResponse { total_users, total_planters, new_planters_today, pending_louge_count }`
  - `AdminAuthorSummary { id, display_name, avatar_url }`
  - `AdminUserItem { id, display_name, avatar_url, role, is_banned, banned_at, ban_reason, planter_count, log_count, created_at, is_self }`
  - `AdminUserListResponse { items, total, page, per_page }`
  - `AdminBanRequest { reason: str | None = None (max 500) }`
  - `AdminPlanterItem { id, title, status, seed_type_name, author: AdminAuthorSummary, log_count, contributor_count, created_at, updated_at, deleted_at }`
  - `AdminPlanterListResponse { items, total, page, per_page }`
  - `AdminPlanterDeleteRequest { confirm_title: str }`
  - `AdminSeedTypeItem { id, slug, name, description, sort_order, is_active, created_at }`
  - `AdminSeedTypeUpdateRequest { description: str }` (1〜1000 字、`field_validator` で trim 後の長さ検証)
  - `model_config = {"from_attributes": True}` を必要箇所に付与

### Phase 6: AdminRouter (TDD per endpoint)

- [x] **Step 7**: `GET /api/v1/admin/stats` テスト & 実装
  - テスト: `apps/api/app/tests/test_admin_router.py` を新規作成、最初のテスト群
    - 非 admin → 404
    - admin → 200 + 4 フィールド
    - new_planters_today は JST 本日の planter のみカウント (テストは UTC 跨ぎを意識して fixed-time fixture)
    - pending_louge_count は sprout 全件 (deleted_at NULL のみ)
  - 実装: `apps/api/app/routers/admin.py` を新規作成、`/api/v1/admin` prefix で `APIRouter(tags=["admin"])`、`stats` エンドポイント追加
  - `apps/api/app/main.py` に `app.include_router(admin.router, prefix="/api/v1")` を追加

- [x] **Step 8**: `GET /api/v1/admin/users` テスト & 実装
  - テスト追加 (test_admin_router.py に同居):
    - 一覧基本動作
    - q フィルタ (display_name 部分一致、大小無視)
    - status='banned' / 'normal' / 'all'
    - ページング (page/per_page、per_page>100 で 422 もしくは clamp; ここでは clamp 採用)
    - planter_count / log_count の値検証
    - is_self の付与 (リクエスト admin == item.id のとき true)
    - deleted_at IS NOT NULL のユーザーは除外
  - 実装: ハンドラ + AdminRepository 呼び出し + is_self 付与 + 構造化ログ `admin.access` (middleware で付与済) のみ。一覧操作自体は別途のログを出さない (operation log は変更操作のみ BR-A14)

- [x] **Step 9**: `POST /api/v1/admin/users/{user_id}/ban` テスト & 実装
  - テスト:
    - 正常: 200 + 更新後 AdminUserItem 返却、`is_banned=true`、`banned_at` 設定、`ban_reason` 保存
    - reason 省略 → `ban_reason=NULL`
    - reason が 500 字超 → 422
    - 自己 BAN → 400 "自分を BAN できません" (BR-A06)
    - admin BAN → 400 "admin ユーザーは BAN できません" (BR-A07)
    - 既に BAN 中 → 200 で現在値、`banned_at` は更新されない (冪等 BR-A08)
    - 存在しない user → 404
    - 構造化ログ `event=admin.user.ban` が 1 回出力、`actor_user_id` / `target_user_id` / `ban_reason` を含む
  - 実装: `update_user_ban` ハンドラ + AdminRepository.ban_user + structlog 出力

- [x] **Step 10**: `POST /api/v1/admin/users/{user_id}/unban` テスト & 実装
  - テスト:
    - 正常: 200 + 3 列が NULL/false に戻る
    - 既に解除済み → 200 (冪等)
    - 存在しない user → 404
    - 構造化ログ `event=admin.user.unban`
  - 実装: ハンドラ + AdminRepository.unban_user + structlog 出力

- [x] **Step 11**: `GET /api/v1/admin/planters` テスト & 実装
  - テスト:
    - status='all' フィルタ (seed/sprout/louge かつ deleted_at IS NULL のみ、archived 除外)
    - status='archived' / 'deleted' / 'seed' / 'sprout' / 'louge'
    - q (title 部分一致)
    - ソート: 'deleted' は deleted_at DESC、それ以外は updated_at DESC
    - author (display_name) / seed_type_name の JOIN 結果
    - ページング
  - 実装: ハンドラ + AdminRepository.list_planters

- [x] **Step 12**: `POST /api/v1/admin/planters/{planter_id}/archive` テスト & 実装
  - テスト:
    - 正常: status='archived' に遷移、更新後 AdminPlanterItem 返却
    - 既に archived → 200 (冪等)
    - deleted_at IS NOT NULL → 404
    - 存在しない → 404
    - 構造化ログ `event=admin.planter.archive`
  - 実装

- [x] **Step 13**: `POST /api/v1/admin/planters/{planter_id}/restore` テスト & 実装
  - テスト:
    - archived → 'seed' に復元、更新後 AdminPlanterItem 返却
    - status != archived → 400 "アーカイブされていません"
    - deleted_at IS NOT NULL → 404
    - 存在しない → 404
    - 構造化ログ `event=admin.planter.restore`
  - 実装

- [x] **Step 14**: `DELETE /api/v1/admin/planters/{planter_id}` テスト & 実装
  - テスト:
    - typed confirmation 一致 → 204 + deleted_at が設定される (ソフトデリート)
    - 不一致 (前後空白あり/大小違い) → 400 "タイトルが一致しません"
    - 存在しない → 404
    - 構造化ログ `event=admin.planter.delete` に title を含める (削除後の trace 用)
  - 実装

- [x] **Step 15**: `GET /api/v1/admin/seed-types` テスト & 実装
  - テスト: status='all'/'active'/'inactive'、ORDER BY sort_order ASC
  - 実装

- [x] **Step 16**: `PATCH /api/v1/admin/seed-types/{seed_type_id}` テスト & 実装
  - テスト:
    - description 更新成功
    - 1〜1000 字バリデーション (空文字 → 422 "説明は必須です"、1001 字 → 422)
    - trim 後の長さで判定
    - 存在しない → 404
    - 構造化ログ `event=admin.seed_type.update` に before/after を含める
  - 実装

- [x] **Step 17**: `POST /api/v1/admin/seed-types/{seed_type_id}/toggle-active` テスト & 実装
  - テスト:
    - true → false / false → true 反転
    - 存在しない → 404
    - 構造化ログ `event=admin.seed_type.update` に before/after を含める
  - **契約テスト追加 (BR-A17)**: `apps/api/app/tests/test_seed_types.py` に「`is_active=false` にトグル直後、公開エンドポイント `GET /api/v1/seed-types` のレスポンスから即座に消える」テストを 1 件追加。U2 既存実装 (`apps/api/app/routers/seed_types.py:20` の `is_active=true` フィルタ) を契約として固定する
  - 実装

### Phase 7: BAN ガード契約テスト (実装は既存のまま)

- [x] **Step 18**: 既存 `get_current_user` の BAN ガード契約テスト
  - 新規: `apps/api/app/tests/test_ban_guard_contract.py` (Functional Design §7 を契約として固定)
  - パラメトリックに以下を網羅:
    - BAN ユーザーが POST `/api/v1/planters` → 403
    - BAN ユーザーが POST `/api/v1/planters/{id}/logs` → 403
    - BAN ユーザーが PATCH `/api/v1/users/me` → 403
    - BAN ユーザーが POST `/api/v1/users/me/avatar` → 403
    - BAN ユーザーが POST `/api/v1/users/{id}/follow` → 403
    - BAN ユーザーが DELETE `/api/v1/users/{id}/follow` → 403
    - BAN ユーザーが POST `/api/v1/planters/{id}/follow` → 403
    - BAN ユーザーが DELETE `/api/v1/planters/{id}/follow` → 403
    - BAN ユーザーが GET `/api/v1/planters` → 200 (既存投稿表示は維持)
    - BAN ユーザーが GET `/api/v1/users/me` → 200
  - **個別ハンドラへの BAN チェック追加は禁止** (Functional Design §7)。テストが通れば既存ガードで足りる

### Phase 8: Web — auth-context 拡張 + Server 用 auth ヘルパ

- [x] **Step 19**: `AppUser` interface に `is_banned` / `deleted_at` を追加
  - 修正: `apps/web/contexts/auth-context.tsx`
  - `AppUser` interface に `is_banned: boolean` と `deleted_at: string | null` を追加
  - fetcher (`/users/me`) のレスポンスマッピングに含める

- [x] **Step 20**: `@supabase/ssr` 依存確認
  - **`apps/web/package.json:12` に `"@supabase/ssr": "^0.5.2"` が既に存在することを確認**するのみ
  - 追加 `npm install` は不要 (現行依存で実装可能)
  - もし将来的に未導入環境で実装する場合に備え、確認手順だけ Step として残す

- [x] **Step 21**: Server 用 `getCurrentUser` + `serverFetch` ヘルパ
  - 新規: `apps/web/lib/auth-server.ts`
  - `import { cookies } from "next/headers"` + `createServerClient` from `@supabase/ssr`
  - `ServerUser` interface: `{ id, display_name, role, is_banned, deleted_at, accessToken: string }` ← access_token もメンバとして返す
  - `getCurrentUser()`:
    1. cookies() から sb-access-token を取得 (Supabase ssr の仕様に従う)
    2. セッション検証
    3. 検証済 access_token を Authorization ヘッダーに乗せて `${API_URL}/api/v1/users/me` を fetch (`cache: "no-store"`)
    4. 成功時は `ServerUser` (access_token 含む) を返却。失敗時は null (例外を投げない、呼び出し側で notFound() ハンドリング)
  - **`serverFetch<T>(path: string, accessToken: string, init?: RequestInit): Promise<T>`** を同ファイルにエクスポート
    - Authorization Bearer ヘッダーを付与し `${API_URL}${path}` に fetch (`cache: "no-store"`)
    - 失敗時は status code を含むエラーをスロー (Step 24 / 28 で `notFound()` 判定に使う)
  - 環境変数: 既存の `NEXT_PUBLIC_API_URL` (or 同等) を使う
  - **このヘルパが Step 24 (AdminLayout) と Step 28 (AdminDashboard の stats fetch) の両方で再利用される**

### Phase 9: BannedBanner

- [x] **Step 22**: BannedBanner コンポーネント
  - 新規: `apps/web/components/layout/banned-banner.tsx`
  - "use client"
  - `useAuth()` から `user` を取得、`user?.is_banned` のときのみ render
  - 文言: 「あなたのアカウントは現在制限されています。投稿・編集・フォロー操作はできません。詳細は運営までお問い合わせください。」
  - 配色: `border-red-300 bg-red-50 text-red-900`、`role="alert"`、dismiss 不可
  - data-testid="banned-banner"

- [x] **Step 23**: ルートレイアウトに BannedBanner を挿入
  - 修正: `apps/web/app/layout.tsx`
  - `<Header />` の直下、`<div className="flex min-h-...">` の前に `<BannedBanner />` を挿入
  - import 追加

### Phase 10: AdminLayout / AdminShell / AdminHeader / AdminSidebar

- [x] **Step 24**: AdminLayout (Server Component) + AdminGuard
  - 新規: `apps/web/app/admin/layout.tsx`
  - Server Component: `getCurrentUser()` を呼び、admin 以外なら `notFound()` (BR-A01, Q10=B)
  - admin なら `<AdminShell user={user}>{children}</AdminShell>` を render
  - **`useRightSidebar` は呼ばない** (Right Sidebar は AdminShell でレンダリングしない、BR-A19)

- [x] **Step 25**: AdminShell (Client Component)
  - 新規: `apps/web/components/admin/admin-shell.tsx`
  - "use client"
  - `<div className="flex min-h-screen bg-cream">` 直下に `<AdminHeader user={user} />` + `<div className="flex flex-1">` + `<AdminSidebar />` + `<main className="flex-1 px-10 py-6">{children}</main>` + `</div>` + `</div>`
  - `bg-primary-dark` (#1F3833) ベース、サイドバーはダーク緑
  - Figma `422:159` を参照 (`get_design_context` で nodeId 取得)

- [x] **Step 26**: AdminHeader
  - 新規: `apps/web/components/admin/admin-header.tsx`
  - 蓮ロゴ + "Admin Panel" + (右側) avatar + display_name + "Admin" + "公開サイトに戻る" + "ログアウト"
  - ログアウト: `useAuth().signOut()` → `router.push("/login")`
  - data-testid: `admin-header`, `admin-header-logout`, `admin-header-back-to-site`

- [x] **Step 27**: AdminSidebar
  - 新規: `apps/web/components/admin/admin-sidebar.tsx`
  - `usePathname` で active 判定、active な NavItem に左 4px の teal アクセント線 (`bg-accent-teal`)
  - 項目: ダッシュボード `/admin`、ユーザー管理 `/admin/users`、Planter 管理 `/admin/planters`、SeedType 管理 `/admin/seed-types` (タグ管理は出さない、BR-A18)
  - Lucide アイコン: LayoutDashboard / Users / Sprout / Tag (or Flower2)
  - data-testid: `admin-sidebar`, `admin-sidebar-link-{key}`

### Phase 11: AdminDashboard `/admin`

- [x] **Step 28**: AdminDashboard ページ
  - 新規: `apps/web/app/admin/page.tsx`
  - Server Component で `getCurrentUser()` を呼び (Step 24 の AdminLayout で既に検証済だが、access_token 取得のため再度呼ぶ)、`serverFetch<AdminStatsResponse>("/api/v1/admin/stats", user.accessToken)` で stats を取得 (Step 21 のヘルパを利用)
  - Figma `424:159` 参照
  - StatsGrid 4 カード (Lucide: Users / Sprout / TrendingUp / Flower2)
  - data-testid: `admin-stats-card-{key}` (key=total_users, total_planters, new_planters_today, pending_louge_count)

### Phase 12: UserManagementPage `/admin/users`

- [x] **Step 29**: UserManagementPage Client Component
  - 新規: `apps/web/app/admin/users/page.tsx`
  - "use client"
  - state: q, status, page, items, total, loading, dialog
  - `useEffect` で fetch (q / status / page 変更時)
  - Figma `426:159` / `434:159` (empty) / `434:391` (loading) 参照
  - ToolbarRow: SearchInput (debounce 300ms) + FilterChipGroup (すべて/正常/BAN中)
  - UserTable: avatar+display_name / Role badge (Admin/User) / Status badge (正常/BAN中) / 投稿数 (planter_count + log_count) / 登録日 / アクション
    - 自分の行 (`is_self=true`) → 鍵アイコン + "（自分）"
    - role='admin' → 鍵アイコン
    - 正常 → [BAN] ボタン (赤系 outline)
    - BAN中 → [BAN解除] ボタン (緑系 outline)
  - Pagination (前後ボタン + ページ番号、MVP は簡易)
  - data-testid: `admin-users-search-input`, `admin-users-filter-chip-{key}`, `admin-users-row-{user_id}`, `admin-users-ban-button-{user_id}`, `admin-users-unban-button-{user_id}`

- [x] **Step 30**: BanUserDialog / UnbanUserDialog
  - 新規: `apps/web/components/admin/ban-user-dialog.tsx`、`apps/web/components/admin/unban-user-dialog.tsx`
  - Step 35 で新設する共通 Dialog コンポーネント (`apps/web/components/common/dialog.tsx`) を利用 + Textarea (BAN理由、500 字、省略可)
  - Figma `427:159` / `427:400` 参照
  - 成功時: 楽観更新 → API レスポンスで上書き
  - エラー時: トースト表示 (既存 toast util がなければ簡易 alert で MVP)
  - data-testid: `admin-ban-dialog`, `admin-ban-dialog-reason-input`, `admin-ban-dialog-confirm`, `admin-unban-dialog-confirm`

### Phase 13: PlanterManagementPage `/admin/planters`

- [x] **Step 31**: PlanterManagementPage Client Component
  - 新規: `apps/web/app/admin/planters/page.tsx`
  - "use client"
  - state: q, status, page, items, total, loading, dialog
  - Figma `428:159` / `434:678` (empty) / `434:949` (loading) 参照
  - ToolbarRow: SearchInput + FilterChipGroup [すべて | Seed | Sprout | Louge | アーカイブ | 削除済み]
    - 「すべて」のラベル下に小さく "= フィードに出ているもの" 補足 (BR-A09b)
  - PlanterTable: タイトル+seed_type_name / 投稿者 (avatar+display_name) / 状態バッジ / Logs (log_count + contributor_count) / 更新日 / アクション
    - seed/sprout/louge → [アーカイブ] [削除]
    - archived → [復元] [削除]
    - deleted → "削除済み" アイコン表示、操作ボタンなし
  - Pagination
  - data-testid: `admin-planters-row-{planter_id}`, `admin-planters-archive-button-{planter_id}`, `admin-planters-restore-button-{planter_id}`, `admin-planters-delete-button-{planter_id}`

- [x] **Step 32**: ArchivePlanterDialog / RestorePlanterDialog / DeletePlanterDialog
  - 新規: `apps/web/components/admin/archive-planter-dialog.tsx` (Step 35 の共通 Dialog 利用)
  - 新規: `apps/web/components/admin/restore-planter-dialog.tsx` (Step 35 の共通 Dialog 利用)
    - 補足文 "復元後の状態は Seed になります" (BR-A10)
  - 新規: `apps/web/components/admin/delete-planter-dialog.tsx` (Step 35 の共通 Dialog 利用)
    - typed confirmation: input.trim() === planter.title.trim() のときのみ削除ボタン enable (BR-A12 大小区別あり)
    - 警告文 (赤): "この操作は取り消せません"
  - Figma `432:159` / `432:435` / `432:713` 参照
  - data-testid: `admin-delete-planter-dialog-confirm-input`, `admin-delete-planter-dialog-confirm`

### Phase 14: SeedTypeAdminPage `/admin/seed-types`

- [x] **Step 33**: SeedTypeAdminPage Client Component
  - 新規: `apps/web/app/admin/seed-types/page.tsx`
  - "use client"
  - 補足テキスト: "新規追加・並び替え・名称変更は migration で行います" (BR-A15)
  - ToolbarRow: FilterChipGroup [すべて | 公開中 | 非公開]
  - SeedTypeTable: 並び順 / 名称 / slug (薄字) / 説明 (1行 truncate) / 公開状態 (Switch) / アクション ([説明を編集])
  - 楽観更新で is_active トグル
  - Figma `433:159` / `464:2` (編集モーダル) 参照
  - data-testid: `admin-seed-types-row-{seed_type_id}`, `admin-seed-types-toggle-{seed_type_id}`, `admin-seed-types-edit-{seed_type_id}`

- [x] **Step 34**: EditDescriptionDialog
  - 新規: `apps/web/components/admin/edit-description-dialog.tsx` (Step 35 の共通 Dialog 利用)
  - Read-only: name / slug / sort_order
  - Textarea: description (1〜1000 字、文字数カウンター)
  - 保存時 PATCH 呼び出し → 成功で閉じる、失敗でトースト
  - data-testid: `admin-edit-description-dialog-textarea`, `admin-edit-description-dialog-save`

### Phase 15: 共通 admin コンポーネント

- [x] **Step 35**: Dialog コンポーネント (新設)
  - 新規: `apps/web/components/common/dialog.tsx`
  - `apps/web/components/` 配下に共通 Dialog 実装が **存在しない** ため、本 Step で新設する (`@radix-ui/*` 依存も未導入のため自作)
  - 仕様:
    - `<Dialog open onOpenChange title description footer>{children}</Dialog>` 形式
    - 背景オーバーレイ (`fixed inset-0 bg-black/40`) + 中央配置のカード (`max-w-md bg-cream rounded-lg p-6 shadow-xl`)
    - ESC キー押下と背景クリックで `onOpenChange(false)` を呼ぶ
    - focus trap: モーダル内の最初の focusable 要素にフォーカス、Tab で循環
    - `aria-modal="true"`, `role="dialog"`, `aria-labelledby` (title), `aria-describedby` (description) を付与
    - body スクロールロック (open 中は `document.body.style.overflow = 'hidden'`)
    - data-testid: `dialog-overlay`, `dialog-content`, `dialog-close`
  - 実装規模目安: 60〜100 行 (依存追加なし、React の `useEffect` + `useRef` のみで実装)
  - **本 Step を Phase 15 の先頭に置く理由**: Step 30 / 32 / 34 の各 Dialog コンポーネントが本 Dialog に依存するため、Generation 順序として先に必要。ただし Step 番号は実装順 (Phase 通りの直列) であり、Step 30 を実装する前に Step 35 を先回り実装してよい (Generation Phase で柔軟に並び替える)

- [x] **Step 36**: Switch コンポーネント
  - 新規: `apps/web/components/common/switch.tsx`
  - **`@radix-ui/*` 依存ゼロのため自作で実装** (約 30 行)。`button[role="switch"][aria-checked]` ベース、Tailwind トランジション
  - `checked` / `onCheckedChange` / `disabled` / `data-testid` props
  - スタイル: checked = `bg-primary` (`#29736B`)、unchecked = `bg-gray-300`、つまみは `bg-white` で translate

- [x] **Step 37**: Pagination コンポーネント
  - 新規: `apps/web/components/admin/pagination.tsx`
  - `page` / `per_page` / `total` / `onPageChange` props
  - 「前へ / N ページ目 / 全 M 件 / 次へ」の簡易表示 (MVP)
  - data-testid: `pagination-prev`, `pagination-next`, `pagination-info`

- [x] **Step 38**: FilterChipGroup コンポーネント
  - 新規: `apps/web/components/admin/filter-chip-group.tsx`
  - `options: { value: string; label: string; suffix?: string }[]` / `value` / `onChange` props
  - active chip は primary 色背景、inactive は border のみ
  - data-testid: `filter-chip-{value}`

- [x] **Step 39**: api-client への admin エンドポイント追加
  - 修正: `apps/web/lib/api-client.ts`
  - `adminClient` (or `admin` namespace) に 11 エンドポイントを追加:
    - `getStats()` / `listUsers(params)` / `banUser(id, body)` / `unbanUser(id)`
    - `listPlanters(params)` / `archivePlanter(id)` / `restorePlanter(id)` / `deletePlanter(id, body)`
    - `listSeedTypes(params)` / `updateSeedTypeDescription(id, body)` / `toggleSeedTypeActive(id)`
  - 失敗時は status code を残してエラーをスロー (404 をハンドラ側で「秘匿」表示するため)

### Phase 16: 運用ドキュメント

- [x] **Step 40**: `docs/operations.md` 新規作成
  - 内容:
    - **初期 admin の作成 SQL**: `UPDATE users SET role = 'admin' WHERE auth_id = '<UUID>'`
    - **降格 SQL**: `UPDATE users SET role = 'user' WHERE id = '<UUID>'`
    - **緊急時の admin 無効化 SQL**: `UPDATE users SET role = 'user', is_banned = true, banned_at = now(), ban_reason = '...' WHERE id = '<UUID>'`
    - **タグ操作 (admin UI なし)**: migration を新規発行する旨
    - **email 検索 (admin UI なし)**: Supabase 管理画面の Authentication タブで対応
  - 出典として BR-A21 を引用
  - 本ドキュメントの位置付け (運用判断・SQL の単一の真実源) を冒頭に明記

### Phase 17: E2E (smoke)

- [x] **Step 41**: Playwright admin smoke テスト
  - 新規: `apps/web/e2e/admin.spec.ts`
  - 既存 test アカウント (`reference_test_accounts.md`) のうち 1 名を **手動 SQL で role='admin' に昇格**して使う前提 (Step 40 の SQL を流用、ローカル/ステージングのみ)
  - シナリオ:
    1. 一般ユーザーで `/admin` にアクセス → 404 ページ
    2. admin で `/admin` にアクセス → ダッシュボード 4 カード表示
    3. `/admin/users` で SearchInput に文字入力、フィルタチップ切り替え
    4. `/admin/planters` でフィルタを「アーカイブ」「削除済み」に切り替え
    5. `/admin/seed-types` で説明編集ダイアログを開く・閉じる (実保存はしない)
  - 削除・BAN・実 PATCH などの破壊的操作は smoke では実行しない (本番テストデータを汚さないため)

### Phase 18: ドキュメント

- [x] **Step 42**: 生成物サマリ markdown
  - 新規: `aidlc-docs/construction/u7-admin/code/code-summary.md`
  - 構成:
    - 生成 / 修正ファイル一覧 (パスと役割)
    - 11 エンドポイントと対応テストの索引
    - フロント画面と Figma nodeId / data-testid 対応表
    - BR-A## と実装箇所の対応表 (BR-A01〜A21)
    - 既知の制限 (mobile 非対応、admin UI からの降格機能なし、email 検索なし、新規 admin 払い出しは DB 直叩き)

---

## Story / Requirements Traceability

| BR / 設計項目 | 実装ステップ |
|---|---|
| BR-A01 (admin 認可・404 秘匿) | Step 3, 24 |
| BR-A02 (BAN ユーザーの行動制限) | Step 18 (契約テスト、実装は既存) |
| BR-A02b (BannedBanner) | Step 19, 22, 23 |
| BR-A03 (BAN 操作の原子性) | Step 4 (test), 5 |
| BR-A04 (ユーザー検索: display_name のみ) | Step 4, 5, 8, 29 |
| BR-A05 (BAN 理由 500 字) | Step 6, 9, 30 |
| BR-A06 (自己 BAN 禁止) | Step 9, 29 |
| BR-A07 (admin 同士 BAN 禁止) | Step 9, 29 |
| BR-A08 (BAN 冪等性) | Step 4, 5, 9, 10 |
| BR-A09 (archive vs delete) | Step 12, 13, 14, 31, 32 |
| BR-A09b (「すべて」フィルタ定義) | Step 4, 11, 31 |
| BR-A10 (復元時 status='seed') | Step 4, 5, 13, 32 |
| BR-A11 (deleted 復元 UI なし) | Step 31 |
| BR-A12 (typed confirmation) | Step 14, 32 |
| BR-A13 (フィード側整合) | 既存 (U2/U5)、本 unit では変更なし |
| BR-A14 (Cloud Logging) | Step 2, 3, 9, 10, 12, 13, 14, 16, 17 |
| BR-A15 (SeedType 編集スコープ) | Step 6, 16, 17, 33 |
| BR-A16 (description 1〜1000 字) | Step 6, 16, 34 |
| BR-A17 (is_active 即時反映) | Step 17, 33 |
| BR-A18 (Tags admin UI なし) | Step 27 (sidebar 項目に出さない), Step 40 |
| BR-A19 (AdminLayout 完全独立) | Step 24, 25 |
| BR-A20 (AdminSidebar 項目) | Step 27 |
| BR-A21 (admin 払い出し運用) | Step 40 |

---

## Total Steps: 42

## Estimated Scope

- 新規 API ファイル: 6 (middleware/request_id.py, dependencies_admin.py, repositories/admin_repository.py, schemas/admin.py, routers/admin.py, tests/test_admin_*.py x 4)
- 修正 API ファイル: 3 (schemas/user.py, main.py, tests/test_users.py 拡張、test_seed_types.py に契約テスト 1 件追加)
- 新規 Web ファイル: 約 19 (auth-server.ts, banned-banner.tsx, admin-shell.tsx, admin-header.tsx, admin-sidebar.tsx, admin/layout.tsx, admin/page.tsx, admin/users/page.tsx, admin/planters/page.tsx, admin/seed-types/page.tsx, ban/unban dialog x 2, archive/restore/delete dialog x 3, edit-description dialog, **dialog (共通)**, switch, pagination, filter-chip-group)
- 修正 Web ファイル: 3 (auth-context.tsx, app/layout.tsx, lib/api-client.ts) ← `package.json` は変更なし (Step 20 は確認のみに縮小)
- E2E: 1 (admin.spec.ts)
- ドキュメント: 2 (operations.md, code-summary.md)
- マイグレーション: なし (既存スキーマで完結)
- テスト追加: 約 6 ファイル + 既存 test_users.py / test_seed_types.py 拡張

## Single Source of Truth

このプランが Code Generation の唯一の真実源。本プランの Step 順に Red→Green→Refactor を遂行し、各 Step 完了時に [x] でマークする。
