# U3 Log & Score - Code Generation Plan

## Unit Context

- **Unit**: U3 Log & Score
- **Purpose**: Log 投稿、スコアエンジン（条件A/B）、Planter 状態遷移、AI ファシリテートの実装。成長サイクルのコア
- **Dependencies (U1 Foundation, U2 Seed)**:
  - DB schema: logs, louge_score_snapshots, insight_score_events, planters, users, planter_follows, notifications
  - Auth: get_current_user, get_optional_user
  - Models: Log, LougeScoreSnapshot, InsightScoreEvent, Planter, User, Notification
  - Repositories: PlanterRepository, FollowRepository
  - Infra: VertexAIClient (config scaffold のみ、実装は U3)
  - Frontend: PlanterDetail page, PlanterCard, ProgressBar, RightSidebarContext
- **After this unit**: U4 Louge

## Reference Documents

- `aidlc-docs/construction/u3-log-score/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u3-log-score/functional-design/domain-entities.md`
- `aidlc-docs/construction/u3-log-score/functional-design/business-rules.md`
- `aidlc-docs/construction/u3-log-score/functional-design/frontend-components.md`
- `CLAUDE.md` (Tech Stack, Code Quality Rules, Design Rules, Figma MCP)

## Implementation Order

**Backend first, Vertex AI 動作確認後に Frontend に着手。**

---

## Generation Steps

### Phase A: Backend -- DB & Schemas

#### Step 1: Database Migration

- [x] `supabase/migrations/00005_u3_log_score.sql`
  - `app_settings` テーブル作成 (key VARCHAR(100) PK, value JSONB, updated_at)
  - `louge_score_snapshots` に `structure_parts JSONB` カラム追加
  - `app_settings` にスコア設定の初期データ投入 (min_contributors=3, min_logs=5, bloom_threshold=0.7, bud_threshold=0.8)
- [x] `apps/api/app/models/app_setting.py` -- AppSetting モデル追加
- [x] `apps/api/app/models/__init__.py` 更新

#### Step 2: Backend Schemas

- [x] `apps/api/app/schemas/log.py` 新規作成
  - `LogCreate` (body: str, parent_log_id: UUID | None)
  - `LogResponse` (id, planter_id, user, body, parent_log_id, is_ai_generated, created_at)
  - `LogWithRepliesResponse` (LogResponse + replies: list[LogResponse])
  - `LogCreateResponse` (log, planter: PlanterScoreResponse, score_pending: bool)
- [x] `apps/api/app/schemas/score.py` 新規作成
  - `StructurePartsResponse` (context, problem, solution, name: bool)
  - `PlanterScoreResponse` (id, status, log_count, contributor_count, progress, structure_fulfillment, maturity_score, structure_parts)
  - `PlanterScoreWithPendingResponse` (score, score_pending, last_scored_at)
  - `ScoreSettingsResponse` (min_contributors, min_logs, bloom_threshold, bud_threshold)
- [x] `apps/api/app/schemas/planter.py` 更新
  - `PlanterResponse` に structure_fulfillment, maturity_score, structure_parts, bloom_threshold 追加

---

### Phase B: Backend -- Repository Layer (TDD)

#### Step 3: LogRepository (TDD)

- [x] **Test**: `apps/api/app/tests/test_log_repository.py`
  - create: Log 作成成功
  - create: AI 生成 Log (user_id=None, is_ai_generated=True)
  - get_by_id: 存在する Log 取得
  - get_by_id: deleted_at ありで None
  - list_by_planter: 古い順ソート、トップレベルのみ
  - list_by_planter: カーソルページネーション (ASC)
  - list_replies: parent_log_ids に対する返信一括取得
  - count_by_planter: Log 件数
  - count_contributors: DISTINCT user_id 件数
  - count_user_logs_since: 指定 Log 以降のユーザー Log 件数
  - get_all_by_planter: 全 Log 取得
- [x] **Impl**: `apps/api/app/repositories/log_repository.py`
  - `LogRepository` クラス
  - 上記全メソッド実装

#### Step 4: ScoreRepository, SettingsRepository (TDD)

- [x] **Test**: `apps/api/app/tests/test_score_repository.py`
  - create_snapshot: LougeScoreSnapshot 作成成功
  - create_snapshot: structure_parts JSONB 保存確認
  - get_latest_snapshot: 最新スナップショット取得
  - get_latest_snapshot: 存在しない場合 None
- [x] **Impl**: `apps/api/app/repositories/score_repository.py`
  - `ScoreRepository` クラス
- [x] **Test**: `apps/api/app/tests/test_settings_repository.py`
  - get_score_settings: DB から取得
  - get_score_settings: DB に設定なしでデフォルト値フォールバック
- [x] **Impl**: `apps/api/app/repositories/settings_repository.py`
  - `SettingsRepository` クラス

#### Step 5: PlanterRepository 拡張 (TDD)

- [x] **Test**: `apps/api/app/tests/test_planter_repository.py` 追加テスト
  - update_scores: structure_fulfillment, maturity_score, progress, status 更新
  - increment_log_count: log_count +1
  - update_contributor_count: contributor_count 更新
- [x] **Impl**: `apps/api/app/repositories/planter_repository.py` 更新
  - `update_scores()`, `increment_log_count()`, `update_contributor_count()` 追加

---

### Phase C: Backend -- Vertex AI Setup & Service Layer (TDD)

#### Step 6: Vertex AI セットアップ & 疎通確認

- [x] `apps/api/pyproject.toml` -- `google-cloud-aiplatform` 依存追加
- [x] `apps/api/app/infra/vertex_ai_client.py` 実装（google-genai SDK、gemini-2.5-flash / gemini-2.5-flash-lite）
  - `generate_json(prompt: str, system_instruction: str) -> dict` メソッド
  - JSON モード強制（レスポンスパース対応）
  - エラーハンドリング
- [x] `apps/api/.env.local` 更新 -- GCP_PROJECT_ID, GCP_LOCATION 設定
- [x] `apps/api/.env.example` 更新 -- U3 対応に更新
- [x] **疎通テスト**: Vertex AI (gemini-2.5-flash, gemini-2.5-flash-lite) への API 呼び出し成功確認

#### Step 7: ScoreEngine -- 条件A (TDD)

- [x] **Test**: `apps/api/app/tests/test_score_engine.py`
  - evaluate_structure: 全パーツ充足で fulfillment=1.0
  - evaluate_structure: 一部パーツ充足で正しい fulfillment 値
  - evaluate_structure: 全パーツ未充足で fulfillment=0.0
  - evaluate_structure: Vertex AI レスポンスのパースエラー時のフォールバック
- [x] **Impl**: `apps/api/app/services/score_engine.py`
  - `ScoreEngine` クラス（条件A: gemini-2.5-flash-lite、条件B: gemini-2.5-flash）
  - `evaluate_structure(seed_title, seed_body, logs) -> StructureResult`
  - Vertex AI プロンプト構築 & JSON パース

#### Step 8: ScoreEngine -- 条件B (TDD)

- [x] **Test**: `apps/api/app/tests/test_score_engine.py` 追加テスト
  - evaluate_maturity: 4観点スコアの正常返却
  - evaluate_maturity: total = 4観点平均の計算
  - evaluate_maturity: Vertex AI レスポンスのパースエラー時のフォールバック
- [x] **Impl**: `apps/api/app/services/score_engine.py` 追加
  - `evaluate_maturity(seed_title, seed_body, logs_with_users) -> MaturityResult`

#### Step 9: AIFacilitator (TDD)

- [x] **Test**: `apps/api/app/tests/test_ai_facilitator.py`
  - generate_facilitation: 最低スコア観点に基づくファシリテート文生成
  - generate_facilitation: 500文字以内の出力
  - should_facilitate: 前回ファシリテートから3件以上のユーザー Log で true
  - should_facilitate: 3件未満で false
  - should_facilitate: 初回（過去ファシリテートなし）で true
- [x] **Impl**: `apps/api/app/services/ai_facilitator.py`
  - `AIFacilitator` クラス
  - `generate_facilitation(seed, logs, maturity_scores) -> str`
  - `should_facilitate(planter_id, db) -> bool`

#### Step 10: ScorePipeline (TDD)

- [x] **Test**: `apps/api/app/tests/test_score_pipeline.py`
  - execute: 条件A のみ実行（最低参加ライン未達）
  - execute: 条件A + 条件B 実行（最低参加ライン到達）
  - execute: 条件B >= bloom_threshold で passed_maturity=true
  - execute: 条件B < bloom_threshold + ファシリテート条件で AI Log 投稿
  - execute: LougeScoreSnapshot が正しく保存される
  - execute: Planter の progress が正しく計算される
  - execute: エラー時に例外を吸収しログ出力（Log 投稿自体は成功済み）
- [x] **Impl**: `apps/api/app/pipelines/score_pipeline.py`
  - `ScorePipeline` クラス
  - `execute(planter_id, trigger_log_id)` -- バックグラウンド実行用
  - 独自 DB セッション管理

---

### Phase D: Backend -- Router Layer (TDD)

#### Step 11: LogRouter (TDD)

- [x] **Test**: `apps/api/app/tests/test_logs.py`
  - POST /planters/{id}/logs: 201 + LogCreateResponse (正常系)
  - POST /planters/{id}/logs: score_pending=true 確認
  - POST /planters/{id}/logs: 401 未認証
  - POST /planters/{id}/logs: 403 BAN ユーザー
  - POST /planters/{id}/logs: 404 Planter not found
  - POST /planters/{id}/logs: 400 planter_already_bloomed (status=louge)
  - POST /planters/{id}/logs: 400 invalid_parent_log (存在しない)
  - POST /planters/{id}/logs: 400 nested_reply_not_allowed (ネスト2段)
  - POST /planters/{id}/logs: 422 body empty / too long
  - POST /planters/{id}/logs: log_count, contributor_count 更新確認
  - POST /planters/{id}/logs: seed -> sprout 遷移確認
  - POST /planters/{id}/logs: 自動フォロー確認
  - GET /planters/{id}/logs: 200 + CursorPaginatedResponse (古い順)
  - GET /planters/{id}/logs: 返信 replies のネスト確認
  - GET /planters/{id}/logs: 非認証でも取得可
- [x] **Impl**: `apps/api/app/routers/logs.py`
  - `POST /api/v1/planters/{planter_id}/logs` (create_log)
  - `GET /api/v1/planters/{planter_id}/logs` (list_logs)

#### Step 12: Score & Settings Endpoints (TDD)

- [x] **Test**: `apps/api/app/tests/test_scores.py`
  - GET /planters/{id}/score: 200 + PlanterScoreWithPendingResponse
  - GET /planters/{id}/score: score_pending 判定（最新 Log > 最新 Snapshot → true）
  - GET /planters/{id}/score: Snapshot なし + Log あり → pending=true
  - GET /planters/{id}/score: Snapshot あり + Log なし → pending=false
  - GET /settings/score: 200 + ScoreSettingsResponse
  - GET /settings/score: DB 設定なしでデフォルト値
- [x] **Impl**: `apps/api/app/routers/scores.py` 新規作成
  - `GET /api/v1/planters/{planter_id}/score` (get_planter_score)
  - `GET /api/v1/settings/score` (get_score_settings)

#### Step 13: PlanterRouter 拡張 & main.py 更新

- [x] `apps/api/app/routers/planters.py` 更新
  - `GET /api/v1/planters/{planter_id}` レスポンスに structure_fulfillment, maturity_score, structure_parts, bloom_threshold 追加
- [x] `apps/api/app/main.py` 更新
  - logs router 登録
  - scores router 登録
- [x] `apps/api/app/tests/conftest.py` 更新
  - Log テスト用フィクスチャ追加
  - app_settings テスト用フィクスチャ追加
  - Vertex AI モックフィクスチャ追加

#### Step 14: Backend 動作確認

- [x] 全 pytest 実行 & パス確認 (124/124 passed)
- [x] 開発サーバー起動 & ルート登録確認 (全エンドポイント登録済み)
- [ ] 手動 API テスト (Vertex AI 実動作 -- デプロイ後に実施)
  - Log 投稿 → スコア計算がバックグラウンドで実行されるか
  - Vertex AI 呼び出しが実際に動作するか
  - score polling エンドポイントが正しく pending 状態を返すか
  - 条件A の構造パーツが正しく判定されるか

---

### Phase E: Frontend

#### Step 15: Figma 参照 & LogThread コンポーネント

- [x] Figma 参照: Seed Detail (nodeId: 57:29) -- Log 表示エリアのデザイン確認
- [x] `apps/web/components/log/LogItem.tsx` 新規作成
  - Log 1件の表示（アバター、ユーザー名、時間、本文、返信リンク）
  - AI アシスタント表示（is_ai_generated=true: ロゴアイコン + "AI アシスタント"）
  - data-testid 付与
- [x] `apps/web/components/log/LogThread.tsx` 新規作成 -- FC-09
  - トップレベル Log の一覧（古い順）
  - 返信のインデント表示
  - 「もっと読み込む」ボタン（カーソルページネーション）
  - data-testid 付与

#### Step 16: Log 投稿フォーム（Sticky Input Bar）

- [x] `apps/web/components/log/LogComposer.tsx` 新規作成
  - 画面下部固定（sticky）
  - テキスト入力（自動拡張、最大5行）
  - 送信ボタン（空テキスト時 disabled）
  - 未ログイン時: 「ログインして参加する」ボタン
  - Planter status='louge' 時: 非表示
  - 返信モード: parent_log_id を保持、返信先の表示
  - POST /api/v1/planters/{id}/logs 呼び出し
  - 投稿後: onLogCreated コールバックでスコア polling 開始
  - data-testid 付与

#### Step 17: ScoreCard 拡張

- [x] `apps/web/components/planter/ScoreCard.tsx` に抽出（現在は planter-detail-client.tsx にインライン）
  - 構造パーツチェックリスト追加 (Context/Problem/Solution/Name)
  - スコア計算中インジケーター（scorePending=true 時にスピナー + テキスト）
  - Louge/Sprout/Seed 状態別の表示ロジック
  - data-testid 付与

#### Step 18: PlanterDetail ページ拡張

- [x] `apps/web/app/p/[id]/page.tsx` 更新
  - PlanterResponse の拡張フィールド対応
  - bloom_threshold を settings API から取得
- [x] `apps/web/app/p/[id]/planter-detail-client.tsx` 更新
  - LogThread コンポーネント統合
  - LogComposer 統合（sticky input bar）
  - Log 投稿後のスコア polling ロジック（3秒→5秒→10秒、最大3回）
  - ScoreCard を外部コンポーネントに置換
  - Right Sidebar 更新（ScoreCard に構造パーツ詳細）

#### Step 19: PlanterCard 拡張

- [x] `apps/web/components/planter/PlanterCard.tsx` 確認済み（変更不要）
  - Sprout 状態のバッジ表示: 既存の STATUS_LABELS で対応済み
  - progress バーの実値連動: ProgressBar コンポーネントで対応済み

---

### Phase F: Documentation

#### Step 20: Documentation Summary

- [x] `aidlc-docs/construction/u3-log-score/code/code-summary.md`
  - 作成/更新ファイル一覧
  - API エンドポイント一覧
  - Vertex AI 設定手順
  - テストカバレッジサマリ

---

## Test Strategy (CLAUDE.md)

| Target | Approach | Tool |
|---|---|---|
| LogRepository | TDD | pytest |
| ScoreRepository | TDD | pytest |
| SettingsRepository | TDD | pytest |
| PlanterRepository (拡張) | TDD | pytest |
| ScoreEngine (条件A/B) | TDD | pytest (Vertex AI モック) |
| AIFacilitator | TDD | pytest (Vertex AI モック) |
| ScorePipeline | TDD | pytest (Vertex AI モック) |
| LogRouter | TDD | pytest + httpx AsyncClient |
| ScoreRouter | TDD | pytest + httpx AsyncClient |
| Vertex AI 疎通 | 手動テスト | 実際の API 呼び出し |
| Frontend Components | Figma reference -> implement | Playwright (Build & Test) |

## Figma Reference Plan

| Step | nodeId | Screen |
|---|---|---|
| Step 15 | 57:29 | Seed Detail (Log 表示エリア) |

## Summary

- **20 steps** (4 phases)
- Phase A: DB & Schemas (Step 1-2)
- Phase B: Repository Layer TDD (Step 3-5)
- Phase C: Vertex AI + Service Layer TDD (Step 6-10)
- Phase D: Router Layer TDD + 動作確認 (Step 11-14)
- Phase E: Frontend (Step 15-19)
- Phase F: Documentation (Step 20)
- **Backend 完了 & Vertex AI 動作確認 (Step 14) の後に Frontend (Step 15) に着手**
