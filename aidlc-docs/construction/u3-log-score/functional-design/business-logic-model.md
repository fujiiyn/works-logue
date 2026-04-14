# U3 Log & Score - Business Logic Model

## 概要

U3 のビジネスロジックは7つのフローで構成される:
1. **Log 投稿フロー** — Log を作成し、ScorePipeline をバックグラウンドで起動する
2. **Log 一覧取得フロー** — Planter に紐づく Log をスレッド構造で取得する
3. **ScorePipeline（バックグラウンド）** — 条件A → 条件B → AI ファシリテートのオーケストレーション
4. **Planter 詳細取得（拡張）** — スコア情報・構造パーツ詳細を含むレスポンスを返す
5. **AI ファシリテート** — 条件B 未達時に AI が問いかけを投稿する
6. **スコア polling** — フロントエンドがバックグラウンド計算の完了を確認する
7. **スコア設定取得フロー** — 開花閾値等の設定を取得する

---

## フロー1: Log 投稿

### シーケンス

```
Client (LogThread input bar)
  |
  |-- POST /api/v1/planters/{planter_id}/logs
  |     Body: { body, parent_log_id? }
  |     Header: Authorization: Bearer <JWT>
  |
  v
LogRouter.create_log()
  |
  |-- 1. get_current_user(request)     <- 認証チェック（BAN チェック含む）
  |
  |-- 2. バリデーション
  |     |-- planter_id が planters に存在 & deleted_at IS NULL & status != 'archived'
  |     |-- parent_log_id が指定されている場合:
  |     |     |-- 同一 planter_id の Log に存在 & deleted_at IS NULL
  |     |     |-- parent_log_id の Log 自体が parent_log_id=NULL であること（ネスト1段制限）
  |     |-- body: 1〜5000文字
  |
  |-- 3. トランザクション開始（同期）
  |     |-- Log INSERT (planter_id, user_id, body, parent_log_id, is_ai_generated=false)
  |     |-- Planter.log_count += 1
  |     |-- Planter.contributor_count を再計算（DISTINCT user_id from logs WHERE planter_id）
  |     |-- status='seed' かつ log_count >= 1 → status='sprout' に遷移
  |     |-- PlanterFollow INSERT（Log 投稿者の自動フォロー、既存なら無視）
  |     |-- 通知イベント作成（BR-08）
  |     |-- COMMIT
  |
  |-- 4. ScorePipeline をバックグラウンドで起動
  |     |-- FastAPI BackgroundTasks.add_task(score_pipeline.execute, planter_id, log.id)
  |     |-- （詳細はフロー3参照）
  |
  |-- 5. レスポンス即時返却
        |-- 201 Created
        |-- Body: LogCreateResponse (Log + Planter の現時点スコア + score_pending=true)
```

### エラーケース

| 条件 | HTTP Status | Error Code |
|---|---|---|
| 未認証 | 401 | not_authenticated |
| BAN ユーザー | 403 | account_banned |
| Planter が存在しない / 削除済み / アーカイブ | 404 | planter_not_found |
| Planter が louge 状態 | 400 | planter_already_bloomed |
| parent_log_id が無効 | 400 | invalid_parent_log |
| parent_log_id が既にネストされた返信 | 400 | nested_reply_not_allowed |
| body が空 or 5000文字超 | 422 | validation_error |

### Planter 状態チェック

- `status='louge'` の Planter には Log 投稿不可（開花済みは読み取り専用）
- `status='seed'` or `status='sprout'` の場合のみ Log 投稿を許可

---

## フロー2: Log 一覧取得

### シーケンス

```
Client (PlanterDetail page)
  |
  |-- GET /api/v1/planters/{planter_id}/logs?limit=50&cursor=<created_at>&cursor_id=<id>
  |     Header: Authorization: Bearer <JWT>  <- オプション
  |
  v
LogRouter.list_logs()
  |
  |-- 1. get_optional_user(request)    <- 認証は任意
  |
  |-- 2. LogRepository.list_by_planter(planter_id, cursor, cursor_id, limit)
  |     |-- WHERE planter_id = :planter_id
  |     |-- WHERE deleted_at IS NULL
  |     |-- WHERE parent_log_id IS NULL  <- トップレベル Log のみ
  |     |-- ORDER BY created_at ASC, id ASC  <- 古い順
  |     |-- カーソル条件: (created_at, id) > (cursor, cursor_id)
  |     |-- LIMIT limit + 1
  |
  |-- 3. 各トップレベル Log の返信を一括取得
  |     |-- WHERE parent_log_id IN (top_level_log_ids)
  |     |-- WHERE deleted_at IS NULL
  |     |-- ORDER BY created_at ASC
  |
  |-- 4. User 情報を一括取得（N+1 回避）
  |
  |-- 5. レスポンス返却
        |-- 200 OK
        |-- Body: CursorPaginatedResponse<LogWithRepliesResponse>
```

### ページネーション仕様

- U2 の PlanterFeed と同じ CursorPaginatedResponse 形式を再利用
- **ソート順**: 古い順（ASC）— チャット風表示
- **limit**: デフォルト 50、最大 100
- **返信**: トップレベル Log ごとに `replies: list[LogResponse]` をネスト

---

## フロー3: ScorePipeline（バックグラウンドオーケストレーション）

FastAPI の `BackgroundTasks` で非同期実行。Log 投稿のレスポンス返却後に開始される。
エラーが発生しても Log 投稿自体は成功済み（データロスなし）。エラーはログに記録する。

### シーケンス

```
ScorePipeline.execute(planter_id, trigger_log_id)  <- BackgroundTasks で実行
  |
  |-- 0. 新規 DB セッション取得（BackgroundTasks は独自セッション）
  |
  |-- 1. Planter + 全 Log を取得
  |     |-- Planter: 現在の status, structure_fulfillment, maturity_score
  |     |-- Logs: planter_id に紐づく全 Log（deleted_at IS NULL）
  |
  |-- 2. 条件A: ScoreEngine.evaluate_structure(seed, logs)
  |     |-- Vertex AI (Gemini Flash) に Seed + Log 全文を送信
  |     |-- 4つの構造パーツ (Context, Problem, Solution, Name) の充足状態を判定
  |     |-- 返却: StructureResult { parts: dict[str, bool], fulfillment: float }
  |     |-- fulfillment = 充足パーツ数 / 4
  |
  |-- 3. Planter 更新（条件A 結果）
  |     |-- structure_fulfillment = fulfillment
  |     |-- progress の前半50% を更新: progress = min(fulfillment * 0.5, 0.5)
  |
  |-- 4. 条件B 判定: 最低参加ラインチェック
  |     |-- ScoreSettings から閾値を取得（min_contributors, min_logs）
  |     |-- contributor_count >= min_contributors AND log_count >= min_logs
  |     |-- AND structure_fulfillment == 1.0（条件A 完全充足）
  |     |-- 未達: 条件B スキップ、Step 6 へ
  |
  |-- 5. 条件B: ScoreEngine.evaluate_maturity(seed, logs)
  |     |-- Vertex AI (Gemini Flash) に Seed + Log 全文を送信
  |     |-- 4観点スコアリング:
  |     |     comprehensiveness: 0.0〜1.0
  |     |     diversity: 0.0〜1.0
  |     |     counterarguments: 0.0〜1.0
  |     |     specificity: 0.0〜1.0
  |     |-- 返却: MaturityResult { scores: dict[str, float], total: float }
  |     |-- total = 4観点の平均
  |
  |-- 6. Planter 更新（条件B 結果）
  |     |-- maturity_score = total（条件B 実行時のみ更新）
  |     |-- progress の後半50% を更新:
  |     |     progress = 0.5 + min(maturity_total * 0.5, 0.5)
  |
  |-- 7. LougeScoreSnapshot INSERT
  |     |-- planter_id, trigger_log_id
  |     |-- structure_fulfillment, passed_structure
  |     |-- maturity_scores (JSONB), maturity_total, passed_maturity
  |
  |-- 8. 開花判定
  |     |-- passed_structure AND passed_maturity (maturity_total >= bloom_threshold)
  |     |-- bloom_threshold: ScoreSettings から取得（デフォルト 0.7）
  |     |-- 開花条件を満たした場合:
  |     |     Planter.status = 'louge' への遷移は U4 で実装
  |     |     U3 では「開花準備完了」フラグのみ（passed_maturity=true をスナップショットに記録）
  |     |     ※ 実際の Louge 生成（AI 記事生成）は U4 スコープ
  |
  |-- 9. AI ファシリテート判定（条件B 未達時）
  |     |-- 条件B 実行済み かつ maturity_total < bloom_threshold の場合
  |     |-- AIFacilitator.generate_facilitation(seed, logs, maturity_scores)
  |     |-- （詳細はフロー5参照）
  |
  |-- 10. COMMIT
  |
  |-- 11. DB セッションをクローズ
```

### 条件A と条件B の関係

```
Log 投稿
  |
  v
条件A（毎回）── structure_fulfillment 更新
  |
  |-- 条件A 未完全充足 → progress 前半のみ更新、終了
  |
  |-- 条件A 完全充足 (1.0) かつ 最低参加ライン到達
        |
        v
      条件B 実行 ── maturity_score 更新
        |
        |-- maturity_total >= bloom_threshold → 開花準備完了（U4 で Louge 生成）
        |
        |-- maturity_total < bloom_threshold → AI ファシリテート投稿
```

---

## フロー4: Planter 詳細取得（U3 拡張）

### U2 からの拡張点

U2 の PlanterResponse に以下を追加:

```
PlanterRouter.get_planter() の拡張
  |
  |-- 既存: Planter + User + SeedType + Tags
  |
  |-- U3 追加:
  |     |-- structure_parts: 条件A の構造パーツ詳細
  |     |     最新の LougeScoreSnapshot から取得
  |     |     { context: bool, problem: bool, solution: bool, name: bool }
  |     |-- structure_fulfillment: float (0.0〜1.0)
  |     |-- maturity_score: float | null
  |     |-- progress: float (0.0〜1.0)
  |     |-- bloom_threshold: float (ScoreSettings から)
```

### レスポンス形式の拡張

```python
class PlanterResponse:
    # ... 既存フィールド ...
    structure_fulfillment: float
    maturity_score: float | None
    progress: float
    # U3 追加
    structure_parts: StructurePartsResponse | None  # 最新スナップショットの構造パーツ
    bloom_threshold: float  # 開花閾値（設定値）
```

---

## フロー5: AI ファシリテート

### トリガー条件

条件B が実行されたが `maturity_total < bloom_threshold` の場合に発動。

### シーケンス

```
AIFacilitator.generate_facilitation(seed, logs, maturity_scores)
  |
  |-- 1. 最もスコアが低い観点を特定
  |     |-- min(comprehensiveness, diversity, counterarguments, specificity)
  |
  |-- 2. Vertex AI (Gemini Flash) でファシリテート文を生成
  |     |-- プロンプト:
  |     |     - Seed の内容
  |     |     - 現在の議論の要約（Log 群）
  |     |     - 不足している観点の指示
  |     |     - 「ファシリテーターとして、参加者に問いかける形で」
  |     |-- 出力: ファシリテート文（テキスト、500文字以内）
  |
  |-- 3. Log INSERT
  |     |-- user_id = NULL（AI 投稿）
  |     |-- is_ai_generated = true
  |     |-- parent_log_id = NULL（トップレベル Log として投稿）
  |     |-- body = 生成されたファシリテート文
  |
  |-- 4. Planter.log_count += 1
  |     |-- contributor_count は変更なし（AI は contributor に含めない）
```

### ファシリテート頻度制限

- 同一 Planter に対して連続でファシリテートしない
- 前回のファシリテート Log から **3件以上のユーザー Log** が投稿されるまで次のファシリテートを抑制
- これにより AI が連投して議論を支配することを防ぐ

---

## フロー6: スコア polling

### シーケンス

```
Client (ScoreCard polling)
  |
  |-- GET /api/v1/planters/{planter_id}/score
  |     Header: Authorization: Bearer <JWT>  <- オプション
  |
  v
PlanterRouter.get_planter_score()
  |
  |-- 1. Planter のスコア関連フィールドを取得
  |
  |-- 2. 最新の LougeScoreSnapshot を取得
  |     |-- structure_parts を含む
  |
  |-- 3. score_pending 判定
  |     |-- 最新 Log の created_at > 最新 Snapshot の created_at → pending=true
  |     |-- Snapshot が存在しない かつ log_count > 0 → pending=true
  |     |-- それ以外 → pending=false
  |
  |-- 4. レスポンス返却
        |-- 200 OK
        |-- Body: PlanterScoreWithPendingResponse
```

---

## フロー7: スコア設定取得

### シーケンス

```
Client (PlanterDetail / Admin)
  |
  |-- GET /api/v1/settings/score
  |     Header: Authorization: Bearer <JWT>  <- オプション
  |
  v
SettingsRouter.get_score_settings()  <- 認証不要（公開情報）
  |
  |-- ScoreSettings を返却
  |-- Body: ScoreSettingsResponse
```

### ScoreSettings（設定テーブル）

| キー | 型 | デフォルト | 説明 |
|---|---|---|---|
| min_contributors | int | 3 | 条件B 開始の最低参加者数 |
| min_logs | int | 5 | 条件B 開始の最低 Log 数 |
| bloom_threshold | float | 0.7 | 条件B の開花閾値（0.0〜1.0） |
| bud_threshold | float | 0.8 | Sprout 3（蕾）の progress 閾値 |

- `app_settings` テーブル（key-value 形式）に保存
- 管理者ページ（U7）から CRUD 可能
- U3 では読み取り専用 API + デフォルト値のフォールバック

---

## Repository 層の責務

### LogRepository

| メソッド | 責務 |
|---|---|
| `create(log: Log) -> Log` | INSERT + flush + refresh |
| `get_by_id(id: UUID) -> Log \| None` | 単一取得（deleted_at IS NULL） |
| `list_by_planter(planter_id, cursor, cursor_id, limit) -> list[Log]` | トップレベル Log のカーソルページネーション（ASC） |
| `list_replies(parent_log_ids: list[UUID]) -> list[Log]` | 返信 Log の一括取得 |
| `count_by_planter(planter_id) -> int` | Log 件数 |
| `count_contributors(planter_id) -> int` | DISTINCT user_id 件数 |
| `count_user_logs_since(planter_id, since_log_id) -> int` | 指定 Log 以降のユーザー Log 件数（ファシリテート頻度制限用） |
| `get_all_by_planter(planter_id) -> list[Log]` | 全 Log 取得（ScorePipeline 用） |

### ScoreRepository

| メソッド | 責務 |
|---|---|
| `create_snapshot(snapshot: LougeScoreSnapshot) -> LougeScoreSnapshot` | INSERT |
| `get_latest_snapshot(planter_id) -> LougeScoreSnapshot \| None` | 最新スナップショット取得 |

### PlanterRepository（U3 拡張）

| メソッド | 責務 |
|---|---|
| `update_scores(planter_id, **fields) -> None` | structure_fulfillment, maturity_score, progress, status 等を更新 |
| `increment_log_count(planter_id) -> None` | log_count += 1 |
| `update_contributor_count(planter_id, count) -> None` | contributor_count を更新 |

### SettingsRepository

| メソッド | 責務 |
|---|---|
| `get_score_settings() -> ScoreSettings` | score 関連設定を取得（未設定時はデフォルト値） |
