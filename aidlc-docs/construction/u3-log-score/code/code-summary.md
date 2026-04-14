# U3 Log & Score -- Code Generation Summary

## 作成/更新ファイル一覧

### Backend (apps/api)

| ファイル | 操作 | 概要 |
|---|---|---|
| `app/models/log.py` | 新規 | Log モデル (soft delete, AI generated, reply chain) |
| `app/models/score.py` | 新規 | LougeScoreSnapshot, InsightScoreEvent モデル |
| `app/models/app_setting.py` | 新規 | AppSetting モデル (key-value 設定) |
| `app/models/__init__.py` | 更新 | 新モデルのインポート追加 |
| `app/schemas/log.py` | 新規 | LogCreate, LogResponse, LogWithRepliesResponse, LogCreateResponse |
| `app/schemas/score.py` | 新規 | PlanterScoreResponse, PlanterScoreWithPendingResponse, ScoreSettingsResponse, StructurePartsResponse |
| `app/schemas/planter.py` | 更新 | structure_fulfillment, maturity_score, structure_parts, bloom_threshold 追加 |
| `app/repositories/log_repository.py` | 新規 | CRUD, ページネーション, カウント, ユーザーLog数計算 |
| `app/repositories/score_repository.py` | 新規 | スナップショット作成/最新取得 |
| `app/repositories/settings_repository.py` | 新規 | スコア設定取得 (デフォルト値フォールバック) |
| `app/repositories/planter_repository.py` | 更新 | update_scores, increment_log_count, update_contributor_count 追加 |
| `app/infra/vertex_client.py` | 新規 | Vertex AI (google-genai SDK) クライアント |
| `app/services/score_engine.py` | 新規 | 条件A (構造評価) + 条件B (成熟度評価) |
| `app/services/ai_facilitator.py` | 新規 | AI ファシリテーション生成 + 実行判定 |
| `app/pipelines/score_pipeline.py` | 新規 | スコア計算パイプライン (条件A→条件B→ファシリテート→保存) |
| `app/routers/logs.py` | 新規 | POST/GET /planters/{id}/logs |
| `app/routers/scores.py` | 新規 | GET /planters/{id}/score, GET /settings/score |
| `app/main.py` | 更新 | logs, scores ルーター登録 |

### Frontend (apps/web)

| ファイル | 操作 | 概要 |
|---|---|---|
| `components/log/LogItem.tsx` | 新規 | Log 1件表示 (ユーザー/AI, 返信ボタン) |
| `components/log/LogThread.tsx` | 新規 | Log一覧 (カーソルページネーション, 返信ネスト) |
| `components/log/LogComposer.tsx` | 新規 | 投稿フォーム (sticky, 自動拡張, 返信モード, 未ログイン対応) |
| `components/planter/ScoreCard.tsx` | 新規 | 開花スコアカード (構造パーツチェックリスト, pending インジケーター) |
| `app/p/[id]/page.tsx` | 更新 | settings API 取得, 拡張フィールド対応 |
| `app/p/[id]/planter-detail-client.tsx` | 更新 | LogThread/LogComposer/ScoreCard 統合, スコア polling |

### Database

| ファイル | 概要 |
|---|---|
| `supabase/migrations/00005_u3_log_score.sql` | logs, louge_score_snapshots, insight_score_events, app_settings テーブル + planter カラム追加 |

## API エンドポイント一覧

| Method | Path | 認証 | 概要 |
|---|---|---|---|
| POST | `/api/v1/planters/{id}/logs` | 必須 | Log 投稿 (自動フォロー, seed->sprout 遷移, バックグラウンドスコア計算) |
| GET | `/api/v1/planters/{id}/logs` | 不要 | Log 一覧取得 (カーソルページネーション, 返信ネスト) |
| GET | `/api/v1/planters/{id}/score` | 不要 | スコア取得 (score_pending 判定付き) |
| GET | `/api/v1/settings/score` | 不要 | スコア設定取得 (デフォルト値フォールバック) |

## Vertex AI 設定手順

1. Google Cloud プロジェクトで Vertex AI API を有効化
2. サービスアカウントキーを取得
3. 環境変数を設定:
   - `GOOGLE_CLOUD_PROJECT`: GCP プロジェクト ID
   - `GOOGLE_CLOUD_LOCATION`: リージョン (default: `us-central1`)
   - `GOOGLE_APPLICATION_CREDENTIALS`: サービスアカウントキーのパス
4. `google-genai` パッケージがインストール済みであること (`pyproject.toml` に追加済み)

## テストカバレッジサマリ

| テストファイル | テスト数 | 対象 |
|---|---|---|
| `test_log_repository.py` | 8 | LogRepository CRUD, ページネーション, カウント |
| `test_score_repository.py` | 4 | ScoreRepository スナップショット作成/取得 |
| `test_settings_repository.py` | 2 | SettingsRepository デフォルト/DB値取得 |
| `test_planter_repository.py` | 7 | PlanterRepository (既存 + 拡張) |
| `test_score_engine.py` | 6 | ScoreEngine 条件A/B 評価 |
| `test_ai_facilitator.py` | 5 | AIFacilitator 生成/判定 |
| `test_score_pipeline.py` | 5 | ScorePipeline 統合テスト |
| `test_logs.py` | 17 | LogRouter エンドポイント (認証, バリデーション, ページネーション) |
| `test_scores.py` | 7 | ScoreRouter エンドポイント (pending判定, 設定デフォルト) |
| **合計** | **61** | U3 新規テスト (全体 124 テスト通過) |
