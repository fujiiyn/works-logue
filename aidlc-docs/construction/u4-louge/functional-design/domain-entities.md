# U4 Louge - Domain Entities

---

## 既存エンティティの拡張

### Planter（拡張なし - 既存カラムを活用）

U4 で新規カラム追加は不要。以下の既存カラムを活用する:

| カラム | 型 | U4 での用途 |
|---|---|---|
| `status` | VARCHAR(10) | `"louge"` に遷移 |
| `louge_content` | TEXT (nullable) | Markdown 形式の Louge 記事を保存 |
| `louge_generated_at` | TIMESTAMPTZ (nullable) | 記事生成完了時刻 |
| `progress` | FLOAT | 開花時に 1.0 に設定 |

**bloom_pending の判定**（カラム追加なし、導出値）:
```
bloom_pending = (status == "louge") AND (louge_content IS NULL)
```

### User（拡張なし - 既存カラムを活用）

| カラム | 型 | U4 での用途 |
|---|---|---|
| `insight_score` | FLOAT | InsightScoreCalculator が加算 |

---

## 既存エンティティ（U4 で本格活用）

### InsightScoreEvent

U3 でモデル定義済み。U4 で初めてレコードが書き込まれる。

| カラム | 型 | 内容 |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID FK(users) | スコア加算対象ユーザー |
| `planter_id` | UUID FK(planters) | 開花した Planter |
| `log_id` | UUID FK(logs) nullable | 貢献した Log（Seed 投稿者ボーナスの場合は NULL） |
| `score_delta` | FLOAT | 加算スコア（0.0〜1.0） |
| `reason` | VARCHAR(50) | `"log_contribution"` or `"seed_author"` |
| `created_at` | TIMESTAMPTZ | 記録日時 |

### Notification

U3 で定義済み。U4 で `louge_bloomed` タイプを使用。

| カラム | 型 | 内容 |
|---|---|---|
| `type` | VARCHAR(30) | `"louge_bloomed"` |
| `user_id` | UUID FK(users) | 通知対象ユーザー |
| `planter_id` | UUID FK(planters) | 開花した Planter |
| `actor_id` | UUID FK(users) nullable | NULL（システムイベント） |

---

## 新規エンティティ

U4 で新規テーブル・モデルの追加は不要。

---

## DB マイグレーション

U4 で新規マイグレーションは不要。既存のスキーマで全ての要件を満たせる:

- `planters.louge_content`: 既存（U1 で作成済み）
- `planters.louge_generated_at`: 既存（U1 で作成済み）
- `insight_score_events`: 既存テーブル（U1 で作成済み）
- `notifications` の `louge_bloomed` タイプ: CHECK 制約で許可済み

---

## レスポンス構造

### PlanterDetailResponse（拡張）

既存の Planter 詳細レスポンスに以下を追加:

```python
class PlanterDetailResponse(BaseModel):
    # ... 既存フィールド ...
    louge_content: str | None       # Markdown 記事（null = 未生成）
    louge_generated_at: str | None  # ISO 8601 日時
    bloom_pending: bool             # 導出: status=="louge" and louge_content is None
```

### ContributorResponse（新規）

```python
class ContributorResponse(BaseModel):
    user_id: str
    display_name: str
    avatar_url: str | None
    insight_score_earned: float     # この Planter での獲得スコア合計
    log_count: int                  # この Planter での Log 投稿数
    is_seed_author: bool

class ContributorsListResponse(BaseModel):
    contributors: list[ContributorResponse]
```
