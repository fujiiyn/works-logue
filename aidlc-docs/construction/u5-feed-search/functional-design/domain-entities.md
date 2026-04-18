# U5 Feed & Search — Domain Entities

## 新規エンティティ

なし。既存テーブル (`planters`, `planter_views`, `planter_tags`, `tags`) を利用。

## 既存エンティティの拡張

### PlanterRepository 追加メソッド

| メソッド | 概要 |
|---|---|
| `list_trending_candidates(window_days, limit)` | 直近 N 日間にアクティブな Planter を取得 |
| `list_bloomed(limit, cursor)` | `status='louge'` を `louge_generated_at DESC` で取得 |
| `search(keyword?, tag_ids[]?, status?, limit, cursor)` | 複合検索クエリ |
| `get_view_counts(planter_ids, since)` | planter_views から集計 |

### LogRepository 追加メソッド

| メソッド | 概要 |
|---|---|
| `get_log_velocities(planter_ids, window_hours)` | 直近 N 時間の Log 投稿数を Planter ごとに集計 |

### 新規サービス: FeedRanker

| メソッド | 概要 |
|---|---|
| `rank_trending(planters, view_counts, log_velocities, window_hours)` | 複合スコア計算・並び替え |

## DB マイグレーション

### 追加インデックス（検索パフォーマンス用）

```sql
-- planters.title + body の ILIKE 検索用（pg_trgm）
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_planters_title_trgm ON planters USING gin (title gin_trgm_ops) WHERE deleted_at IS NULL;

-- louge_generated_at での並び替え用
CREATE INDEX idx_planters_louge_generated_at ON planters (louge_generated_at DESC) WHERE status = 'louge' AND deleted_at IS NULL;
```

### planter_views テーブル
既に `00001_create_tables.sql` で作成済み。`00007_planter_views_ip.sql` で以下を追加:
- `ip_address VARCHAR(45)` カラム追加
- IPアドレスベースの重複排除用インデックス追加
