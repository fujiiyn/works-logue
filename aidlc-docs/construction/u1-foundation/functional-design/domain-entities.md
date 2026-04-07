# U1 Foundation — Domain Entities（DB スキーマ全量）

## 概要

全ユニットが使用する DB テーブル定義。U1 でマイグレーション全量を作成する。

---

## テーブル定義

### seed_types（マスタ）

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| slug | VARCHAR(20) | UNIQUE, NOT NULL | コード値（query/pain/failure/hypothesis/comparison/observation/knowledge/practice） |
| name | VARCHAR(50) | NOT NULL | 表示名（例: "疑問"、"悩み"） |
| description | TEXT | NOT NULL | ジャンルの説明文（投稿フォームで表示） |
| sort_order | INT | NOT NULL, DEFAULT 0 | 表示順 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 無効化フラグ（管理画面から制御） |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**初期データ**:

| slug | name | description |
|---|---|---|
| query | 疑問 | 現場で感じた「なぜ？」「どうすれば？」を投げかける |
| pain | 悩み | 解決策が見つからない業務課題や困りごと |
| failure | 失敗 | 実際に経験した失敗事例とその教訓 |
| hypothesis | 仮説 | 「こうすればうまくいくのでは？」という仮説の検証を求める |
| comparison | 比較 | ツール・手法・アプローチの比較検討 |
| observation | 違和感 | 「これおかしくない？」という現場の気づき |
| knowledge | シェア | 知見やノウハウの共有 |
| practice | 実践報告 | 実際に試した結果の報告とフィードバック募集 |

---

### users

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | Supabase Auth の user ID と一致させる |
| auth_id | UUID | UNIQUE, NOT NULL | Supabase Auth の user ID（auth.users.id） |
| display_name | VARCHAR(100) | NOT NULL | 表示名 |
| bio | TEXT | NULL | 自己紹介文 |
| avatar_url | TEXT | NULL | Supabase Storage のアバター画像 URL |
| insight_score | FLOAT | NOT NULL, DEFAULT 0.0 | 累積インサイトスコア（表示用キャッシュ。正は insight_score_events） |
| role | VARCHAR(10) | NOT NULL, DEFAULT 'user' | ユーザーロール（user/admin） |
| is_banned | BOOLEAN | NOT NULL, DEFAULT FALSE | BAN 状態 |
| banned_at | TIMESTAMPTZ | NULL | BAN 日時 |
| ban_reason | TEXT | NULL | BAN 理由 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| deleted_at | TIMESTAMPTZ | NULL | ソフトデリート |

**インデックス**:
- `idx_users_auth_id` ON (auth_id) — 認証時の検索
- `idx_users_deleted_at` ON (deleted_at) WHERE deleted_at IS NULL — アクティブユーザーフィルタ

---

### planters

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| user_id | UUID | FK → users.id, NOT NULL | 投稿者 |
| title | VARCHAR(200) | NOT NULL | タイトル |
| body | TEXT | NOT NULL | Seed 本文 |
| seed_type_id | UUID | FK → seed_types.id, NOT NULL | 投稿タイプ |
| status | VARCHAR(10) | NOT NULL, DEFAULT 'seed' | Planter 状態（seed/sprout/louge） |
| louge_content | TEXT | NULL | Louge 記事（Markdown）。開花後に格納 |
| louge_generated_at | TIMESTAMPTZ | NULL | Louge 生成日時 |
| structure_fulfillment | FLOAT | NOT NULL, DEFAULT 0.0 | 条件A 構造パーツ充足率（0.0〜1.0） |
| maturity_score | FLOAT | NULL | 条件B 成熟度スコア（0.0〜100.0）。条件A 充足後に値が入る |
| progress | FLOAT | NOT NULL, DEFAULT 0.0 | UI表示用の総合進捗（0.0〜1.0）。条件A=0〜0.5、条件B=0.5〜1.0 にスケール |
| log_count | INT | NOT NULL, DEFAULT 0 | Log 件数（非正規化・パフォーマンス用） |
| contributor_count | INT | NOT NULL, DEFAULT 0 | ユニーク投稿者数（非正規化） |
| parent_planter_id | UUID | FK → planters.id, NULL | Fork 元（フェーズ2） |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| deleted_at | TIMESTAMPTZ | NULL | ソフトデリート |

**インデックス**:
- `idx_planters_seed_type_id` ON (seed_type_id)
- `idx_planters_user_id` ON (user_id)
- `idx_planters_status` ON (status) WHERE deleted_at IS NULL
- `idx_planters_created_at` ON (created_at DESC) WHERE deleted_at IS NULL — 新着フィード
- `idx_planters_deleted_at` ON (deleted_at) WHERE deleted_at IS NULL

**CHECK 制約**:
- `chk_planters_status` CHECK (status IN ('seed','sprout','louge','archived'))

---

### logs

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| planter_id | UUID | FK → planters.id, NOT NULL | 所属 Planter |
| user_id | UUID | FK → users.id, NULL | 投稿者（AI 生成の場合 NULL） |
| body | TEXT | NOT NULL | Log 本文 |
| parent_log_id | UUID | FK → logs.id, NULL | 返信先（ネスト1段） |
| is_ai_generated | BOOLEAN | NOT NULL, DEFAULT FALSE | AI ファシリテート Log フラグ |
| is_hidden | BOOLEAN | NOT NULL, DEFAULT FALSE | 管理者による非表示フラグ |
| hidden_at | TIMESTAMPTZ | NULL | 非表示日時 |
| hidden_by | UUID | FK → users.id, NULL | 非表示にした管理者 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 編集日時 |
| deleted_at | TIMESTAMPTZ | NULL | ソフトデリート |

**インデックス**:
- `idx_logs_planter_id` ON (planter_id, created_at) WHERE deleted_at IS NULL — Planter の Log 一覧
- `idx_logs_user_id` ON (user_id) WHERE deleted_at IS NULL
- `idx_logs_parent_log_id` ON (parent_log_id) WHERE parent_log_id IS NOT NULL

---

### tags

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| name | VARCHAR(100) | NOT NULL | タグ名（例: "SaaS・ソフトウェア"） |
| category | VARCHAR(20) | NOT NULL | カテゴリ（industry/occupation/role/situation/skill/knowledge） |
| parent_tag_id | UUID | FK → tags.id, NULL | 親タグ（階層構造） |
| sort_order | INT | NOT NULL, DEFAULT 0 | 表示順 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 無効化フラグ（管理画面から制御） |

**インデックス**:
- `idx_tags_category` ON (category, sort_order)
- `idx_tags_parent` ON (parent_tag_id)
- `idx_tags_name_search` ON (name) — 部分一致検索用（pg_trgm 拡張で GIN インデックスも検討）

**UNIQUE 制約**:
- `uq_tags_name_category` UNIQUE (name, category)

**CHECK 制約**:
- `chk_tags_category` CHECK (category IN ('industry','occupation','role','situation','skill','knowledge'))

---

### planter_tags（中間テーブル）

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| planter_id | UUID | FK → planters.id, NOT NULL | |
| tag_id | UUID | FK → tags.id, NOT NULL | |

**PK**: (planter_id, tag_id)

---

### user_tags（中間テーブル）

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| user_id | UUID | FK → users.id, NOT NULL | |
| tag_id | UUID | FK → tags.id, NOT NULL | |

**PK**: (user_id, tag_id)

---

### planter_follows

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| user_id | UUID | FK → users.id, NOT NULL | フォローする側 |
| planter_id | UUID | FK → planters.id, NOT NULL | フォロー対象 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**PK**: (user_id, planter_id)

---

### user_follows

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| follower_id | UUID | FK → users.id, NOT NULL | フォローする側 |
| followee_id | UUID | FK → users.id, NOT NULL | フォロー対象 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**PK**: (follower_id, followee_id)

**CHECK 制約**:
- `chk_user_follows_no_self` CHECK (follower_id != followee_id)

---

### notifications

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| user_id | UUID | FK → users.id, NOT NULL | 通知対象ユーザー |
| type | VARCHAR(30) | NOT NULL | イベント型（new_log/status_changed/louge_bloomed/new_seed） |
| planter_id | UUID | FK → planters.id, NULL | 関連 Planter |
| actor_id | UUID | FK → users.id, NULL | 行為者 |
| is_read | BOOLEAN | NOT NULL, DEFAULT FALSE | 既読フラグ |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**インデックス**:
- `idx_notifications_user_unread` ON (user_id, created_at DESC) WHERE is_read = FALSE

**CHECK 制約**:
- `chk_notifications_type` CHECK (type IN ('new_log','status_changed','louge_bloomed','new_seed'))

---

### planter_views

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| planter_id | UUID | FK → planters.id, NOT NULL | |
| user_id | UUID | FK → users.id, NULL | 非ログインユーザーは NULL |
| viewed_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**カウント方針**: ログインユーザーはユニーク閲覧数（同一ユーザーの重複カウントなし）。非ログインユーザーは毎回カウント。

**インデックス**:
- `idx_planter_views_planter` ON (planter_id, viewed_at) — 閲覧数集計用
- `idx_planter_views_user` ON (user_id, planter_id) WHERE user_id IS NOT NULL — 重複閲覧チェック用

**UNIQUE 制約**:
- `uq_planter_views_user` UNIQUE (user_id, planter_id) WHERE user_id IS NOT NULL — ログインユーザーの重複防止

---

### louge_score_snapshots

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| planter_id | UUID | FK → planters.id, NOT NULL | |
| trigger_log_id | UUID | FK → logs.id, NULL | スコア計算のトリガーとなった Log |
| structure_fulfillment | FLOAT | NOT NULL | 条件A 充足率 |
| maturity_scores | JSONB | NULL | 条件B 4観点スコア（comprehensiveness/diversity/counterarguments/specificity） |
| maturity_total | FLOAT | NULL | 条件B 合計スコア |
| passed_structure | BOOLEAN | NOT NULL | 条件A 充足判定 |
| passed_maturity | BOOLEAN | NULL | 条件B 基準突破判定（条件A 未充足時は NULL） |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**インデックス**:
- `idx_score_snapshots_planter` ON (planter_id, created_at DESC)

---

### insight_score_events

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| user_id | UUID | FK → users.id, NOT NULL | スコア付与対象ユーザー |
| planter_id | UUID | FK → planters.id, NOT NULL | 開花した Planter |
| log_id | UUID | FK → logs.id, NULL | 貢献した Log（NULL = Seed 投稿者ボーナス） |
| score_delta | FLOAT | NOT NULL | 加算スコア |
| reason | VARCHAR(50) | NOT NULL | 加算理由（seed_author/log_cited/log_contributed） |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**インデックス**:
- `idx_insight_events_user` ON (user_id, created_at DESC)
- `idx_insight_events_planter` ON (planter_id)

---

### ai_configs（管理者設定）

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| key | VARCHAR(50) | UNIQUE, NOT NULL | 設定キー |
| value | TEXT | NOT NULL | 設定値 |
| description | TEXT | NULL | 管理画面での説明 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_by | UUID | FK → users.id, NULL | 最終更新した管理者 |

**初期データ**:

| key | value | description |
|---|---|---|
| scoring_model | gemini-2.0-flash | スコアリング用AIモデル（軽量・高頻度） |
| louge_model | gemini-2.0-pro | Louge記事生成用AIモデル（高品質） |
| facilitator_model | gemini-2.0-flash | AIファシリテート用モデル |
| scoring_structure_prompt | (プロンプトテンプレート) | 条件A 構造パーツ判定プロンプト |
| scoring_maturity_prompt | (プロンプトテンプレート) | 条件B 成熟度スコアリングプロンプト |
| louge_generation_prompt | (プロンプトテンプレート) | Louge記事生成プロンプト |
| facilitator_prompt | (プロンプトテンプレート) | AIファシリテートLog生成プロンプト |
| structure_threshold | 0.8 | 条件A 充足率の閾値（これ以上でSprout2へ） |
| maturity_threshold | 100 | 条件B 完全充足スコア（これ以上でLouge開花） |
| bud_threshold | 80 | 条件B スコアの蕾しきい値（これ以上でSprout3へ） |
| min_participants | 5 | 条件B 発動の最低参加者数 |
| min_logs | 10 | 条件B 発動の最低Log数 |

---

## テーブル間リレーション

```
seed_types (マスタ) ──── planters.seed_type_id (N:1)

users ─────────────┬─── planters (1:N)
  |                |       |
  |                |       ├── logs (1:N)
  |                |       ├── planter_tags (N:M → tags)
  |                |       ├── planter_follows (N:M → users)
  |                |       ├── planter_views (1:N)
  |                |       ├── louge_score_snapshots (1:N)
  |                |       └── insight_score_events (1:N)
  |                |
  ├── user_tags (N:M → tags)
  ├── user_follows (N:M → users)
  ├── notifications (1:N)
  └── insight_score_events (1:N)

tags ──── parent_tag_id (自己参照: 階層構造)
logs ──── parent_log_id (自己参照: 返信ネスト)
planters ── parent_planter_id (自己参照: Fork、フェーズ2)
```

---

## タグ初期データ

`docs/tags.md` の全タグを `supabase/migrations/` の seed マイグレーションとして投入。

カテゴリマッピング:
| docs/tags.md セクション | tags.category 値 |
|---|---|
| 業界 | industry |
| 職種 | occupation |
| 役割 | role |
| 状況 | situation |
| スキル/メソッド | skill |
| ナレッジ | knowledge |

階層は `parent_tag_id` で表現。例: "IT・インターネット" → "SaaS・ソフトウェア"
