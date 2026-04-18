# U5 Feed & Search - Code Generation Plan

## Unit Context

- **Unit**: U5 Feed & Search
- **Purpose**: フィードの拡張（注目・開花済みタブ）と探索・検索機能の実装
- **Dependencies (U1, U2)**:
  - Models: Planter, PlanterView, Tag, PlanterTag
  - Repositories: PlanterRepository, TagRepository, LogRepository
  - Frontend: PlanterFeed, PlanterCard, TagAccordionSelector, Sidebar
- **After this unit**: U6 User & Follow
- **DB Migration**: pg_trgm 拡張 + インデックス追加

## Reference Documents

- `aidlc-docs/construction/u5-feed-search/functional-design/business-rules.md`
- `aidlc-docs/construction/u5-feed-search/functional-design/domain-entities.md`
- `aidlc-docs/construction/u5-feed-search/functional-design/frontend-components.md`
- `CLAUDE.md` (Tech Stack, Code Quality Rules, Design Rules, Figma MCP)

## Implementation Order

**Backend first（TDD）→ Frontend（Figma MCP 参照）**

---

## Generation Steps

### Phase A: DB Migration

#### Step 1: マイグレーション追加

- [x] `supabase/migrations/00002_feed_search_indexes.sql` 新規作成
  - `CREATE EXTENSION IF NOT EXISTS pg_trgm`
  - `CREATE INDEX idx_planters_title_trgm ON planters USING gin (title gin_trgm_ops) WHERE deleted_at IS NULL`
  - `CREATE INDEX idx_planters_louge_generated_at ON planters (louge_generated_at DESC) WHERE status = 'louge' AND deleted_at IS NULL`

---

### Phase B: Backend — Service Layer (TDD)

#### Step 2: FeedRanker サービス (TDD)

- [x] **Test**: `apps/api/app/tests/test_feed_ranker.py`
  - rank_trending: 空リストで空結果
  - rank_trending: 単一 Planter でスコア計算
  - rank_trending: 複数 Planter で正しい並び順
  - rank_trending: view_count / log_velocity がゼロの場合の正規化
  - rank_trending: 同スコア時は created_at DESC
- [x] **Impl**: `apps/api/app/services/feed_ranker.py`
  - `FeedRanker` クラス
  - `rank_trending(planters, view_counts, log_velocities, window_hours) -> list[RankedPlanter]`
  - 重み: views=0.3, velocity=0.5, structure=0.2
  - min-max 正規化

---

### Phase C: Backend — Repository Layer (TDD)

#### Step 3: PlanterRepository 拡張 (TDD)

- [x] **Test**: `apps/api/app/tests/test_planter_repository_feed.py`
  - list_recent: 既存テストが引き続きパス（tab=recent）
  - list_trending_candidates: 直近 N 日間のアクティブ Planter を取得
  - list_bloomed: status='louge' のみ、louge_generated_at DESC
  - search: キーワード ILIKE フィルタ
  - search: タグ AND フィルタ
  - search: 状態フィルタ
  - search: 複合条件 AND 結合
  - search: カーソルページネーション
  - get_view_counts: planter_views から集計
- [x] **Impl**: `apps/api/app/repositories/planter_repository.py` 更新
  - `list_trending_candidates(window_days, limit)` 追加
  - `list_bloomed(limit, cursor_louge_generated_at, cursor_id)` 追加
  - `search(keyword, tag_ids, status, limit, cursor_created_at, cursor_id)` 追加
  - `get_view_counts(planter_ids, since)` 追加
  - `record_view(planter_id, user_id)` 追加

#### Step 4: LogRepository 拡張 (TDD)

- [x] **Test**: `apps/api/app/tests/test_log_repository_velocity.py`
  - get_log_velocities: 正しい集計
  - get_log_velocities: Log なしの Planter は 0.0
- [x] **Impl**: `apps/api/app/repositories/log_repository.py` 更新
  - `get_log_velocities(planter_ids, window_hours)` 追加

---

### Phase D: Backend — Router Layer (TDD)

#### Step 5: Planters Router 拡張（tab パラメータ対応）

- [x] **Test**: `apps/api/app/tests/test_planters_router_feed.py`
  - GET /planters?tab=recent: 既存動作維持
  - GET /planters?tab=trending: FeedRanker 経由のランキング
  - GET /planters?tab=bloomed: louge のみ表示
- [x] **Impl**: `apps/api/app/routers/planters.py` 更新
  - `list_planters` に `tab` クエリパラメータ追加（デフォルト: recent）
  - tab=trending: list_trending_candidates → get_view_counts → get_log_velocities → FeedRanker
  - tab=bloomed: list_bloomed

#### Step 6: SearchRouter 新規 (TDD)

- [x] **Test**: `apps/api/app/tests/test_search_router.py`
  - GET /search: キーワード検索
  - GET /search: タグフィルタ
  - GET /search: 状態フィルタ
  - GET /search: 複合条件
  - GET /search: ページネーション
  - GET /search: パラメータなし（全件新着順）
- [x] **Impl**: `apps/api/app/routers/search.py` 新規作成
  - `GET /api/v1/search` エンドポイント
  - PlanterRepository.search() を呼び出し
  - レスポンス: CursorPaginatedResponse

#### Step 7: View 記録エンドポイント

- [x] **Impl**: `apps/api/app/routers/planters.py` 更新
  - `POST /api/v1/planters/{planter_id}/view` エンドポイント追加
  - ログインユーザーのみ記録（未ログインは 204 で無視）
  - PlanterRepository.record_view() を呼び出し

#### Step 8: Router 登録

- [x] **Impl**: `apps/api/app/main.py` 更新
  - SearchRouter を登録

---

### Phase E: Backend 動作確認

#### Step 9: テスト実行・動作確認

- [x] `pytest apps/api/` 全テスト実行
- [x] 既存テストの回帰確認

---

### Phase F: Frontend — Figma MCP 参照 & 実装

#### Step 10: Figma デザイン参照

- [x] Figma MCP `get_design_context` で Explore ページ (nodeId: 217:12) を参照
- [x] Home ページ (nodeId: 12:3) のフィードタブ部分も確認

#### Step 11: PlanterFeed 拡張

- [x] `apps/web/components/planter/PlanterFeed.tsx` 更新
  - coming soon 削除、全タブ実機能化
  - tab パラメータを API に送信 (`/api/v1/planters?tab=...`)
  - タブ切り替え時にリスト・カーソルリセット＆再取得
  - 各タブ独立の loading/empty 状態

#### Step 12: Explore ページ新規作成

- [x] `apps/web/app/explore/page.tsx` 新規作成
  - SearchBar（キーワード入力、debounce 300ms）
  - TagFilter（TagAccordionSelector 再利用）
  - StatusFilter（seed/sprout/louge チップ）
  - 検索結果: PlanterCard リスト + 無限スクロール
  - API: `GET /api/v1/search`

#### Step 13: Sidebar 更新

- [x] `apps/web/components/sidebar.tsx` 更新
  - `/explore` リンク追加（Lucide `Search` アイコン）

#### Step 14: View 記録の組み込み

- [x] `apps/web/app/p/[id]/page.tsx` 更新
  - ページ表示時に `POST /api/v1/planters/{id}/view` を呼び出し（fire-and-forget）

---

### Phase G: 最終確認

#### Step 15: 全体テスト・レビュー

- [x] Backend テスト全パス確認
- [x] Frontend ビルド確認 (`npm run build`)
- [x] dev サーバー起動して動作確認
  - 新着タブ: 既存動作維持
  - 人気タブ: ランキング表示
  - 開花済みタブ: louge のみ表示
  - Explore ページ: 検索・フィルタ動作
