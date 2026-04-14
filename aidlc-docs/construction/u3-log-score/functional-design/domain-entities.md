# U3 Log & Score - Domain Entities

## 概要

U3 で操作する主要エンティティとその関連。DB スキーマ・SQLAlchemy モデルは U1 で作成済み。ここでは U3 で利用するエンティティの操作仕様を定義する。

---

## Log

Seed に対して蓄積される知恵・コメント。スレッド形式（ネスト1段返信）。

### カラム利用仕様（U3 スコープ）

| カラム | U3 での用途 |
|---|---|
| id | UUID。自動採番 |
| planter_id | 対象 Planter。FK -> planters.id。必須 |
| user_id | 投稿者。FK -> users.id。nullable（AI 投稿時は NULL） |
| body | Log 本文。必須。1〜5000文字 |
| parent_log_id | 返信先 Log。FK -> logs.id。nullable。ネスト1段のみ許可 |
| is_ai_generated | AI ファシリテート Log: true、ユーザー投稿: false |
| is_hidden | false（U3 では非表示機能を使わない） |
| hidden_at | NULL |
| hidden_by | NULL |
| created_at | 自動設定 |
| updated_at | 自動設定 |
| deleted_at | NULL。ソフトデリート用 |

### レスポンス形式

```python
class LogResponse:
    id: UUID
    planter_id: UUID
    user: UserPublicResponse | None  # AI 投稿時は None
    body: str
    parent_log_id: UUID | None
    is_ai_generated: bool
    created_at: datetime

class LogWithRepliesResponse:
    id: UUID
    planter_id: UUID
    user: UserPublicResponse | None
    body: str
    is_ai_generated: bool
    created_at: datetime
    replies: list[LogResponse]  # ネストされた返信（古い順）
```

### リクエスト形式

```python
class LogCreate:
    body: str  # 1〜5000文字
    parent_log_id: UUID | None = None
```

### Log 投稿後のレスポンス

```python
class LogCreateResponse:
    log: LogResponse
    planter: PlanterScoreResponse  # 現時点のスコア情報（AI計算前）
    score_pending: bool            # true = バックグラウンドでスコア計算中
```

```python
class PlanterScoreResponse:
    id: UUID
    status: str                    # seed -> sprout 遷移は同期で反映済み
    log_count: int                 # 同期で更新済み
    contributor_count: int         # 同期で更新済み
    progress: float                # AI計算前の前回値
    structure_fulfillment: float   # AI計算前の前回値
    maturity_score: float | None   # AI計算前の前回値
    structure_parts: StructurePartsResponse | None  # AI計算前の前回値
```

### スコア polling 用エンドポイント

Log 投稿後、フロントエンドがスコア更新を確認するために使用:

```
GET /api/v1/planters/{planter_id}/score
```

```python
class PlanterScoreWithPendingResponse:
    score: PlanterScoreResponse
    score_pending: bool  # まだバックグラウンド計算中か
    last_scored_at: datetime | None  # 最新スナップショットの created_at
```

**score_pending の判定ロジック**:
- 最新の Log の created_at > 最新の LougeScoreSnapshot の created_at → pending=true
- それ以外 → pending=false

---

## LougeScoreSnapshot

Log 投稿のたびに記録されるスコアスナップショット。閾値チューニング・分析に使用。

### カラム利用仕様（U3 スコープ）

| カラム | U3 での用途 |
|---|---|
| id | UUID。自動採番 |
| planter_id | 対象 Planter。FK -> planters.id。必須 |
| trigger_log_id | スコア計算のトリガーとなった Log。FK -> logs.id |
| structure_fulfillment | 条件A 充足率（0.0〜1.0） |
| maturity_scores | 条件B の4観点スコア (JSONB)。条件B 未実行時は NULL |
| maturity_total | 条件B の総合スコア（4観点平均）。未実行時は NULL |
| passed_structure | 条件A 完全充足フラグ（fulfillment == 1.0） |
| passed_maturity | 条件B 閾値突破フラグ。未実行時は NULL |
| created_at | 自動設定 |

### maturity_scores JSONB 形式

```json
{
  "comprehensiveness": 0.75,
  "diversity": 0.60,
  "counterarguments": 0.45,
  "specificity": 0.80
}
```

### structure_parts（条件A 詳細）

LougeScoreSnapshot に保存するための拡張。`maturity_scores` と同様に JSONB カラムを追加するか、既存カラムを活用する。

**方針**: `structure_fulfillment` は float で全体の充足率のみ持つが、パーツ単位の詳細は Vertex AI のレスポンスに含まれる。これを LougeScoreSnapshot の新規 JSONB カラム `structure_parts` に保存する。

```json
{
  "context": true,
  "problem": true,
  "solution": false,
  "name": false
}
```

**マイグレーション**: `louge_score_snapshots` に `structure_parts JSONB` カラムを追加。

---

## Planter（U3 拡張）

U2 では `status='seed'` で作成するのみだった。U3 で更新する対象カラム:

| カラム | U3 での更新内容 |
|---|---|
| status | `seed` -> `sprout` への遷移（Log 1件以上で） |
| structure_fulfillment | 条件A の充足率（0.0〜1.0）を毎回更新 |
| maturity_score | 条件B の総合スコア（0.0〜1.0）を更新（条件B 実行時のみ） |
| progress | 開花までの総合進捗（0.0〜1.0）を毎回更新 |
| log_count | Log 投稿のたびにインクリメント |
| contributor_count | Log 投稿のたびに再計算（DISTINCT user_id） |

### PlanterResponse の拡張（U3）

```python
class PlanterResponse:
    # 既存（U2）
    id: UUID
    title: str
    body: str
    status: str  # "seed" | "sprout" | "louge"
    seed_type: SeedTypeResponse
    user: UserPublicResponse
    tags: list[TagResponse]
    log_count: int
    contributor_count: int
    progress: float
    created_at: datetime
    # U3 追加
    structure_fulfillment: float
    maturity_score: float | None
    structure_parts: StructurePartsResponse | None
    bloom_threshold: float
```

```python
class StructurePartsResponse:
    context: bool
    problem: bool
    solution: bool
    name: bool
```

---

## AppSetting（新規）

スコア設定等のアプリケーション設定を key-value で保存するテーブル。

### テーブル定義

```sql
CREATE TABLE app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 初期データ

```sql
INSERT INTO app_settings (key, value) VALUES
  ('score.min_contributors', '3'),
  ('score.min_logs', '5'),
  ('score.bloom_threshold', '0.7'),
  ('score.bud_threshold', '0.8');
```

### レスポンス形式

```python
class ScoreSettingsResponse:
    min_contributors: int
    min_logs: int
    bloom_threshold: float
    bud_threshold: float
```

---

## Notification（U3 での利用）

U1 で定義済みの通知テーブル。U3 では以下のイベントでレコードを積む（送信は U6 以降）:

| イベント | type | 対象 |
|---|---|---|
| Planter に新しい Log が投稿された | new_log | Planter のフォロワー全員 |
| Planter の status が変化した | status_changed | Planter のフォロワー全員 |

---

## エンティティ関連図

```
User ──< Log >── Planter ──< LougeScoreSnapshot
  |                 |
  |                 |── PlanterTag >── Tag
  |                 |── PlanterFollow >── User
  |
  └── UserTag >── Tag

AppSetting (独立)

Notification ── User (recipient)
             ── Planter (related)
```
