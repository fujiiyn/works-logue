# U4 Louge - Code Generation Plan

## Unit Context

- **Unit**: U4 Louge
- **Purpose**: Louge 開花（AI 記事生成）、インサイトスコア計算、開花後 UI の実装
- **Dependencies (U1, U3)**:
  - Models: Planter (louge_content, louge_generated_at), InsightScoreEvent, Notification, User (insight_score)
  - Services: ScoreEngine, ScorePipeline, VertexAIClient
  - Repositories: PlanterRepository, LogRepository, ScoreRepository
  - Frontend: PlanterDetail page, ScoreCard, LogThread, LogComposer
- **After this unit**: U5 Feed & Search
- **DB Migration**: 不要（既存スキーマで完結）

## Reference Documents

- `aidlc-docs/construction/u4-louge/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u4-louge/functional-design/business-rules.md`
- `aidlc-docs/construction/u4-louge/functional-design/domain-entities.md`
- `aidlc-docs/construction/u4-louge/functional-design/frontend-components.md`
- `CLAUDE.md` (Tech Stack, Code Quality Rules, Design Rules, Figma MCP)

## Implementation Order

**Backend first、Vertex AI 動作確認後に Frontend に着手。**

---

## Generation Steps

### Phase A: Backend -- Schemas

#### Step 1: Response Schemas

- [x] `apps/api/app/schemas/planter.py` 更新
  - `PlanterResponse` に `louge_content`, `louge_generated_at`, `bloom_pending` フィールド追加
  - `bloom_pending` は導出値: `status == "louge" and louge_content is None`
- [x] `apps/api/app/schemas/contributor.py` 新規作成
  - `ContributorResponse` (user_id, display_name, avatar_url, insight_score_earned, log_count, is_seed_author)
  - `ContributorsListResponse` (contributors: list[ContributorResponse])

---

### Phase B: Backend -- Service Layer (TDD)

#### Step 2: LougeGenerator (TDD)

- [x] **Test**: `apps/api/app/tests/test_louge_generator.py`
  - generate: Vertex AI から JSON レスポンスを受け取り Markdown を組み立て
  - generate: 脚注方式の出典セクション生成
  - generate: Vertex AI エラー時に None を返す
  - bloom: 記事生成 → Planter 更新 → インサイトスコア計算 → 通知記録の全フロー
  - bloom: 記事生成失敗時に louge_content=None のまま（status は louge を維持）
- [x] **Impl**: `apps/api/app/services/louge_generator.py`
  - `LougeGenerator` クラス
  - `generate(planter_id, db) -> str | None` -- Vertex AI で記事生成、Markdown を返す
  - `bloom(planter_id, db) -> None` -- 開花処理のオーケストレーション
  - Vertex AI システムプロンプト（パターンランゲージ形式、脚注出典、日本語）

#### Step 3: InsightScoreCalculator (TDD)

- [x] **Test**: `apps/api/app/tests/test_insight_calculator.py`
  - calculate: 各 Log の貢献度を Vertex AI が 0.0-1.0 で評価
  - calculate: AI 生成 Log (is_ai_generated=True) を除外
  - calculate: Seed 投稿者にボーナス 1.0 を付与
  - apply: InsightScoreEvent を DB に一括保存
  - apply: users.insight_score に score_delta を加算
  - calculate: Vertex AI エラー時のフォールバック（全 Log に均等スコア 0.5）
- [x] **Impl**: `apps/api/app/services/insight_calculator.py`
  - `InsightScoreCalculator` クラス
  - `calculate(planter_id, louge_content, db) -> list[InsightScoreEvent]`
  - `apply(events, db) -> None`

#### Step 4: ScorePipeline 拡張

- [x] **Test**: `apps/api/app/tests/test_score_pipeline.py` 追加テスト
  - execute: passed_maturity=True 時に LougeGenerator.bloom() が呼ばれる
  - execute: bloom 後に status="louge", progress=1.0 に更新
  - execute: bloom 中のエラーでも Planter の status は louge のまま
- [x] **Impl**: `apps/api/app/pipelines/score_pipeline.py` 更新
  - `passed_maturity=True` 時に LougeGenerator.bloom() を呼び出し
  - 状態遷移: `sprout` → `louge`、progress = 1.0
  - `louge_content` は bloom() 内で非同期更新

---

### Phase C: Backend -- Repository & Router Layer (TDD)

#### Step 5: PlanterRepository 拡張 (TDD)

- [x] **Test**: `apps/api/app/tests/test_planter_repository.py` 追加テスト
  - update_louge_content: louge_content と louge_generated_at を更新
- [x] **Impl**: `apps/api/app/repositories/planter_repository.py` 更新
  - `update_louge_content(planter_id, content, generated_at)` 追加

#### Step 6: InsightScoreRepository (TDD)

- [x] **Test**: `apps/api/app/tests/test_insight_repository.py` 新規
  - create_events: InsightScoreEvent の一括保存
  - get_by_planter: Planter の貢献者スコアを集計
  - update_user_scores: users.insight_score に加算
- [x] **Impl**: `apps/api/app/repositories/insight_repository.py` 新規
  - `InsightScoreRepository` クラス

#### Step 7: ContributorsRouter (TDD)

- [x] **Test**: `apps/api/app/tests/test_contributors.py` 新規
  - GET /planters/{id}/contributors: 200 + ContributorsListResponse（Louge 状態）
  - GET /planters/{id}/contributors: 404（Planter が louge 状態でない場合）
  - GET /planters/{id}/contributors: 貢献スコア降順ソート確認
  - GET /planters/{id}/contributors: Seed 投稿者に is_seed_author=true
- [x] **Impl**: `apps/api/app/routers/contributors.py` 新規
  - `GET /api/v1/planters/{planter_id}/contributors`

#### Step 8: Log 投稿制限 & PlanterRouter 拡張

- [x] **Test**: `apps/api/app/tests/test_logs.py` 追加テスト（既存テストで louge 制限確認済み）
  - POST /planters/{id}/logs: status=louge 時に 400 "planter_already_bloomed" 確認（既存テストの確認）
- [x] **Impl**: `apps/api/app/routers/planters.py` 更新
  - `GET /api/v1/planters/{planter_id}` レスポンスに louge_content, louge_generated_at, bloom_pending 追加
- [x] `apps/api/app/main.py` 更新
  - contributors router 登録

#### Step 9: Backend 動作確認

- [x] 全 pytest 実行 & パス確認 (143/143 passed)
- [ ] 開発サーバー起動 & ルート登録確認（デプロイ後に実施）
- [ ] 手動 API テスト（Vertex AI 実動作、デプロイ後に実施）
  - 条件A AND 条件B 突破時に Louge 記事が生成されるか
  - InsightScoreEvent が正しく記録されるか
  - contributors エンドポイントが正しく返るか

---

### Phase D: Frontend

#### Step 10: Figma 参照 & LougeArticle コンポーネント

- [x] Figma 参照: Louge Detail (nodeId: 213:10) -- 開花状態のデザイン確認
- [x] `apps/web/components/louge/LougeArticle.tsx` 新規作成
  - Markdown → HTML レンダリング（react-markdown）
  - 生成日時の表示
  - data-testid 付与

#### Step 11: ContributorsSidebar コンポーネント

- [x] `apps/web/components/louge/ContributorsSidebar.tsx` 新規作成
  - 貢献者一覧（アバター、名前、スコア、Seed 投稿者バッジ）
  - 「Louge をコピー」ボタン
  - data-testid 付与

#### Step 12: PlanterDetail Louge 状態拡張

- [x] `apps/web/app/p/[id]/planter-detail-client.tsx` 更新
  - status=louge 時の表示分岐
  - bloom_pending 時の開花中アニメーション表示
  - 開花ポーリングロジック（3秒→5秒→10秒、60秒タイムアウト）
  - 開花完了時の LougeArticle 表示
  - Seed 折りたたみ（デフォルト: 閉じた状態）
  - LogThread 読み取り専用（LogComposer 非表示）
  - 右サイドバー: louge 状態時は ContributorsSidebar に切替
- [x] `apps/web/components/log/LogComposer.tsx` 更新（既存ロジックで louge 時 null 返却を確認済み）
  - status=louge 時に非表示（既存ロジックの確認・修正）

#### Step 13: Louge コピー機能

- [x] `apps/web/components/louge/LougeCopyButton.tsx` 新規作成
  - Markdown テキストをクリップボードにコピー
  - コピー成功時にトースト通知
  - Lucide Copy アイコン使用
  - data-testid 付与

---

### Phase E: Documentation

#### Step 14: Documentation Summary

- [x] `aidlc-docs/construction/u4-louge/code/code-summary.md`
  - 作成/更新ファイル一覧
  - API エンドポイント一覧
  - テストカバレッジサマリ

---

## Test Strategy (CLAUDE.md)

| Target | Approach | Tool |
|---|---|---|
| LougeGenerator | TDD | pytest (Vertex AI mock) |
| InsightScoreCalculator | TDD | pytest (Vertex AI mock) |
| ScorePipeline (拡張) | TDD | pytest (Vertex AI mock) |
| PlanterRepository (拡張) | TDD | pytest |
| InsightScoreRepository | TDD | pytest |
| ContributorsRouter | TDD | pytest + httpx AsyncClient |
| Log 投稿制限 | TDD | pytest + httpx AsyncClient |
| Vertex AI 実動作 | 手動テスト | 実際の API 呼び出し |
| Frontend Components | Figma reference -> implement | Playwright (Build & Test) |

## Figma Reference Plan

| Step | nodeId | Screen |
|---|---|---|
| Step 10 | 213:10 | Louge Detail (開花状態) |

## Summary

- **14 steps** (5 phases)
- Phase A: Schemas (Step 1)
- Phase B: Service Layer TDD (Step 2-4)
- Phase C: Repository & Router Layer TDD (Step 5-9)
- Phase D: Frontend (Step 10-13)
- Phase E: Documentation (Step 14)
- **Backend 完了 & Vertex AI 動作確認 (Step 9) の後に Frontend (Step 10) に着手**
