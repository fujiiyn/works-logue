# U7 Admin — Code Generation Summary

Code Generation Plan: `aidlc-docs/construction/plans/u7-admin-code-generation-plan.md` (Single Source of Truth)
Functional Design: `aidlc-docs/construction/u7-admin/functional-design/`
Total Steps: 42 / 42 完了

---

## 生成・修正ファイル

### API (`apps/api/`)

| パス | 役割 | Step |
|---|---|---|
| `app/schemas/user.py` | UserResponse に `is_banned` / `deleted_at` を追加 | 1 |
| `app/middleware/__init__.py` | middleware パッケージ | 2 |
| `app/middleware/request_id.py` | RequestId ミドルウェア + structlog contextvars 紐付け | 2 |
| `app/dependencies_admin.py` | `require_admin` Depends（全失敗 → 404 秘匿） | 3 |
| `app/repositories/admin_repository.py` | dashboard stats / users / planters / seed-types の集計と検索 | 4-5 |
| `app/schemas/admin.py` | Admin API の Pydantic スキーマ群 | 6 |
| `app/routers/admin.py` | 11 エンドポイント実装 | 7-17 |
| `app/main.py` | RequestId middleware と admin router を組込 | 2, 7 |

### API Tests (`apps/api/app/tests/`)

| パス | カバー範囲 | 件数 |
|---|---|---|
| `test_users.py` (拡張) | UserResponse の is_banned/deleted_at | +1 |
| `test_request_id_middleware.py` | request_id ContextVar の共有 / 分離 | 全 |
| `test_admin_middleware.py` | require_admin の 5 経路 + admin.access ログ | 7 |
| `test_admin_repository.py` | 4 stats / users / ban / unban / planters / state mutations / seed-types | 34 |
| `test_admin_router.py` | 11 エンドポイントのハッピー & エラー & ログ | 57 |
| `test_seed_types.py` (拡張) | BR-A17 契約: toggle-active 即時反映 | +1 |
| `test_ban_guard_contract.py` | BAN ユーザーの mutation=403 / read=200 | 10 |

### Web (`apps/web/`)

| パス | 役割 | Step |
|---|---|---|
| `contexts/auth-context.tsx` | AppUser に is_banned/deleted_at を追加 | 19 |
| `lib/auth-server.ts` | Server Component 用 `getCurrentUser` + `serverFetch` + `ServerFetchError` | 21 |
| `lib/api-client.ts` | `adminApi` 11 エンドポイント + `ApiError`, 型エクスポート | 39 |
| `components/layout/banned-banner.tsx` | BAN 中ユーザー向け常時バナー | 22 |
| `components/layout/public-chrome.tsx` | `/admin` 配下で public chrome をバイパス | 24 (派生) |
| `app/layout.tsx` | PublicChrome 経由のラップに変更 | 23 |
| `components/common/dialog.tsx` | 共通モーダル（背景ロック / focus trap / ESC） | 35 |
| `components/common/switch.tsx` | role=switch トグル（自作 30 行） | 36 |
| `components/admin/pagination.tsx` | 簡易ページネータ（前後 + 件数表示） | 37 |
| `components/admin/filter-chip-group.tsx` | チップ型フィルタ群 | 38 |
| `components/admin/stat-card.tsx` | ダッシュボード用スタットカード | 28 |
| `components/admin/admin-header.tsx` | Admin 専用ヘッダー（公開サイトに戻る / ログアウト） | 26 |
| `components/admin/admin-sidebar.tsx` | Admin 専用サイドバー（4 ナビ + アクセント線） | 27 |
| `components/admin/admin-shell.tsx` | Header + Sidebar + main の独立シェル（モバイル時は案内のみ） | 25 |
| `app/admin/layout.tsx` | Server Component AdminGuard（非 admin → notFound） | 24 |
| `app/admin/page.tsx` | Dashboard (stats fetch via serverFetch) | 28 |
| `app/admin/users/page.tsx` | UserManagement (検索 / フィルタ / 一覧 / BAN・解除) | 29 |
| `app/admin/planters/page.tsx` | PlanterManagement (検索 / フィルタ / アーカイブ・復元・削除) | 31 |
| `app/admin/seed-types/page.tsx` | SeedType マスタ (公開トグル / 説明編集) | 33 |
| `components/admin/ban-user-dialog.tsx` | BAN 確認ダイアログ（reason 500 字） | 30 |
| `components/admin/unban-user-dialog.tsx` | BAN 解除確認 | 30 |
| `components/admin/archive-planter-dialog.tsx` | アーカイブ確認 | 32 |
| `components/admin/restore-planter-dialog.tsx` | 復元確認（"復元後 = Seed" 注記） | 32 |
| `components/admin/delete-planter-dialog.tsx` | 削除確認（typed confirmation） | 32 |
| `components/admin/edit-description-dialog.tsx` | SeedType description 編集（1〜1000 字） | 34 |
| `e2e/admin.spec.ts` | Smoke E2E 5 シナリオ（破壊操作なし） | 41 |

### ドキュメント

| パス | 役割 | Step |
|---|---|---|
| `docs/operations.md` | admin 払い出し / 降格 / 緊急時 SQL / タグ / email 検索 / 構造化ログ | 40 |
| `aidlc-docs/construction/u7-admin/code/code-summary.md` | この文書 | 42 |

### マイグレーション

なし（既存 `00001_create_tables.sql` の `role` / `is_banned` / `banned_at` /
`ban_reason` / `deleted_at` カラムで完結）

---

## 11 エンドポイントと対応テスト

| メソッド + パス | ハンドラ | 主なテストクラス |
|---|---|---|
| `GET /api/v1/admin/stats` | `get_stats` | `TestGetStats` |
| `GET /api/v1/admin/users` | `list_users` | `TestListUsers` |
| `POST /api/v1/admin/users/{id}/ban` | `ban_user` | `TestBanUser` |
| `POST /api/v1/admin/users/{id}/unban` | `unban_user` | `TestUnbanUser` |
| `GET /api/v1/admin/planters` | `list_planters` | `TestListPlanters` |
| `POST /api/v1/admin/planters/{id}/archive` | `archive_planter` | `TestArchivePlanter` |
| `POST /api/v1/admin/planters/{id}/restore` | `restore_planter` | `TestRestorePlanter` |
| `DELETE /api/v1/admin/planters/{id}` | `delete_planter` | `TestDeletePlanter` |
| `GET /api/v1/admin/seed-types` | `list_admin_seed_types` | `TestListSeedTypes` |
| `PATCH /api/v1/admin/seed-types/{id}` | `update_admin_seed_type` | `TestUpdateSeedTypeDescription` |
| `POST /api/v1/admin/seed-types/{id}/toggle-active` | `toggle_admin_seed_type_active` | `TestToggleSeedTypeActive` |

---

## フロント画面と Figma nodeId / data-testid

| 画面 | パス | Figma nodeId | 主な data-testid |
|---|---|---|---|
| Layout shell | (全画面共通) | `422:159` | `admin-shell`, `admin-header`, `admin-sidebar`, `admin-sidebar-link-{key}`, `admin-header-logout`, `admin-header-back-to-site` |
| Dashboard | `/admin` | `424:159` | `admin-stats-card-total_users` 他 4 種 |
| Users | `/admin/users` | `426:159` | `admin-users-search-input`, `filter-chip-{all\|normal\|banned}`, `admin-users-row-{id}`, `admin-users-ban-button-{id}`, `admin-users-unban-button-{id}` |
| BAN dialog | (modal) | `427:159` | `admin-ban-dialog-reason-input`, `admin-ban-dialog-confirm`, `admin-unban-dialog-confirm` |
| Planters | `/admin/planters` | `428:159` | `admin-planters-row-{id}`, `admin-planters-archive-button-{id}`, `admin-planters-restore-button-{id}`, `admin-planters-delete-button-{id}`, `filter-chip-{all\|seed\|sprout\|louge\|archived\|deleted}` |
| Delete planter dialog | (modal) | `432:713` | `admin-delete-planter-dialog-confirm-input`, `admin-delete-planter-dialog-confirm` |
| SeedType マスタ | `/admin/seed-types` | `433:159` | `admin-seed-types-row-{id}`, `admin-seed-types-toggle-{id}`, `admin-seed-types-edit-{id}` |
| Edit description dialog | (modal) | `464:2` | `admin-edit-description-dialog-textarea`, `admin-edit-description-dialog-save` |

---

## ビジネスルール対応表（BR-A01〜A21）

| BR | 内容 | 実装箇所 |
|---|---|---|
| A01 | admin 認可・404 秘匿 | `dependencies_admin.py:30`, `app/admin/layout.tsx` |
| A02 | BAN ユーザーの行動制限 | `dependencies.py:92-94` (既存)、`test_ban_guard_contract.py` で契約固定 |
| A02b | BannedBanner | `components/layout/banned-banner.tsx` + `app/layout.tsx` 経由 |
| A03 | BAN 操作の原子性 | `admin_repository.py:170-176` |
| A04 | display_name 部分一致のみ | `admin_repository.py:109-110` |
| A05 | BAN 理由 500 字 | `schemas/admin.py:AdminBanRequest` (max_length=500) |
| A06 | 自己 BAN 禁止 | `routers/admin.py:ban_user` (`user_id == admin.id` で 400) |
| A07 | admin BAN 禁止 | `routers/admin.py:ban_user` (`target.role == 'admin'` で 400) |
| A08 | BAN 冪等 | `admin_repository.py:171-172` |
| A09 | archive vs delete 区別 | `admin_repository.py:archive_planter / soft_delete_planter` |
| A09b | 「すべて」= フィードに出ているもの | `admin_repository.py:200-204` (`status IN seed/sprout/louge AND deleted_at IS NULL`) |
| A10 | 復元時 status='seed' | `admin_repository.py:281-282` |
| A11 | deleted 復元 UI なし | `app/admin/planters/page.tsx` で削除済み行は操作ボタン非表示 |
| A12 | typed confirmation | `routers/admin.py:delete_planter` + `delete-planter-dialog.tsx` |
| A13 | フィード側整合 | 既存 (U2/U5)、本 unit 変更なし |
| A14 | Cloud Logging | `request_id.py` + `_logger.info("admin.*", ...)` 各ハンドラ |
| A15 | SeedType 編集スコープ | description 更新と is_active トグルのみ提供 |
| A16 | description 1〜1000 字 | `schemas/admin.py:AdminSeedTypeUpdateRequest._trim_and_validate` |
| A17 | is_active 即時反映 | `routers/seed_types.py:20` を契約として `test_seed_types.py` で固定 |
| A18 | Tags admin UI なし | `admin-sidebar.tsx` の NAV_ITEMS から除外、`docs/operations.md` で migration 運用 |
| A19 | AdminLayout 完全独立 | `components/layout/public-chrome.tsx` で `/admin` を bypass |
| A20 | AdminSidebar 項目 | `admin-sidebar.tsx:NAV_ITEMS` に 4 項目固定 |
| A21 | admin 払い出し運用 | `docs/operations.md` に SQL 集約 |

---

## 既知の制限・MVP スコープ

- **モバイル非対応**: AdminShell は `lg:` ブレークポイントでのみ chrome を render し、モバイル幅では案内メッセージのみ表示する（D16）
- **admin UI からの新規 admin 払い出し / 降格機能なし**: SQL 直叩き運用（BR-A21）
- **email 検索なし**: Supabase Authentication コンソールから引く（`docs/operations.md`）
- **タグ管理 UI なし**: migration で対応（BR-A18）
- **AdminAuditLog テーブルなし**: Cloud Logging に集約（D1）
- **Pagination は最小実装**: 前後ボタン + 現在ページ表示のみ。ページ番号 jumper や size selector は MVP 外
- **E2E は smoke のみ**: 破壊操作（実 BAN / 実削除）は本番テストデータを汚さないため Playwright では行わない。網羅は API テスト（57 件）でカバー

## テスト件数まとめ

- 新規ユニットテスト: **109 件**（Repository 34 + Router 57 + Middleware 7 + RequestId middleware + BAN 契約 10 + SeedType 契約 1）
- 全 API テスト: **350 件 全 Pass**
- Web TypeScript: エラー無し
- E2E: 5 シナリオ（手動 admin 昇格を前提）
