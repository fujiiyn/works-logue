# U5 Feed & Search — Business Rules

## BR-01: フィードタブ切り替え

### 新着タブ (recent)
- `planters.created_at DESC` で並び替え
- `status != 'archived'`, `deleted_at IS NULL` でフィルタ
- 既存実装をそのまま利用

### 注目タブ (trending)
- FeedRanker による複合スコアでランキング
- 対象: 直近 7 日間に作成、または直近 7 日間に Log が投稿された Planter
- スコア計算式:

```
trending_score = w_views * norm(view_count)
               + w_velocity * norm(log_velocity)
               + w_structure * structure_fulfillment

w_views     = 0.3
w_velocity  = 0.5
w_structure = 0.2
```

- **norm()**: 候補集合内での min-max 正規化 (0.0 〜 1.0)
- **log_velocity**: `window_hours` (デフォルト 72h) 内の Log 投稿数 / window_hours
- **view_count**: `planter_views` テーブルから集計（直近 7 日間）
- **structure_fulfillment**: Planter に保存済みの値 (0.0 〜 1.0)
- スコアが同点の場合は `created_at DESC` で並び替え

### 開花済みタブ (bloomed)
- `status = 'louge'` のみ表示
- `louge_generated_at DESC` で並び替え
- カーソルページネーション（louge_generated_at + id）

## BR-02: 検索ロジック

### キーワード検索
- PostgreSQL `to_tsvector / to_tsquery` による全文検索
- 検索対象: `planters.title` + `planters.body`
- 言語設定: `simple`（日本語は形態素解析なしで部分一致を `ILIKE` でフォールバック）
- 実装方針: まず `ILIKE '%keyword%'` で実装し、データ量増加時に full-text search へ移行

### タグフィルタ
- `tag_ids[]` で指定された全タグを持つ Planter を AND 条件でフィルタ
- SQL: `planter_tags` を JOIN し `HAVING COUNT(DISTINCT tag_id) = len(tag_ids)` で絞り込み

### 状態フィルタ
- `status` パラメータで `seed | sprout | louge` を指定
- 未指定時は全状態（archived 除外）

### 複合条件
- キーワード、タグ、状態の全条件を AND で結合
- 並び順: 新着順（`created_at DESC`）
- カーソルページネーション

## BR-03: 閲覧数記録 (planter_views)

- Planter 詳細ページ (`/p/{id}`) 表示時に記録
- **ログイン有無に関係なく記録する**
- ログインユーザー: `(user_id, planter_id)` で UPSERT（1ユーザー1Planter1レコード、`viewed_at` を更新）
- 未ログインユーザー: IPアドレスで重複排除。同一IP × 同一Planter で **10分以内** の再アクセスは無視
- 自分の Planter も閲覧数にカウント
- PlanterCard に閲覧数を表示（Eye アイコン + 数字、0件時は非表示）

## BR-04: Explore ページ

- URL: `/explore`
- 検索バー（キーワード入力）+ タグフィルタ + 状態フィルタの UI
- 検索結果は PlanterCard リストで表示
- 初期表示: フィルタなしで新着順に全 Planter を表示
- タグフィルタ: カテゴリ別にタグを展開選択（既存 TagAccordionSelector を再利用）
