# U2 Seed — Domain Entities

## 概要

U2 で操作する主要エンティティとその関連。DB スキーマは U1 で作成済み（`supabase/migrations/00001_create_tables.sql`）、SQLAlchemy モデルも定義済み（`apps/api/app/models/`）。ここではU2で利用するエンティティの操作仕様を定義する。

---

## Planter

U2 では Planter を **Seed 状態（status='seed'）** で新規作成し、フィードに表示する。

### カラム利用仕様（U2 スコープ）

| カラム | U2 での用途 |
|---|---|
| id | UUID。自動採番 |
| user_id | 投稿者。FK → users.id。必須 |
| title | Seed タイトル。必須。1〜200文字 |
| body | Seed 本文。必須。1〜10000文字 |
| seed_type_id | 投稿タイプ。FK → seed_types.id。必須 |
| status | 初期値 `'seed'`。U2 では変更しない |
| louge_content | NULL（U4 で使用） |
| louge_generated_at | NULL（U4 で使用） |
| structure_fulfillment | 初期値 0.0（U3 で更新） |
| maturity_score | NULL（U3 で更新） |
| progress | 初期値 0.0（U3 で更新） |
| log_count | 初期値 0（U3 で更新） |
| contributor_count | 初期値 0（U3 で更新） |
| parent_planter_id | NULL（Fork 機能はフェーズ2） |
| created_at | 自動設定 |
| updated_at | 自動設定 |
| deleted_at | NULL。ソフトデリート用 |

### レスポンス形式

```python
class PlanterResponse:
    id: UUID
    title: str
    body: str
    status: str  # "seed"
    seed_type: SeedTypeResponse  # ネストしたオブジェクト
    user: UserPublicResponse  # 投稿者情報
    tags: list[TagResponse]  # 紐付けられたタグ
    log_count: int
    contributor_count: int
    progress: float
    created_at: datetime
```

### フィード用レスポンス形式（カード表示用）

```python
class PlanterCardResponse:
    id: UUID
    title: str
    status: str
    seed_type: SeedTypeResponse
    user: UserPublicResponse
    tags: list[TagResponse]
    log_count: int
    contributor_count: int
    progress: float
    created_at: datetime
    # body は含まない（フィードでは不要）
```

---

## SeedType

マスタデータ。U1 で初期投入済み（8タイプ）。U2 では読み取り専用。

### レスポンス形式

```python
class SeedTypeResponse:
    id: UUID
    slug: str  # "query", "pain", "failure", etc.
    name: str  # "疑問", "悩み", "失敗", etc.
    description: str
```

---

## Tag

マスタデータ。U1 の `00003_seed_tags.sql` で初期投入済み。U2 では読み取り + Planter への紐付け。

### 階層構造

```
Tag (category='occupation', parent_tag_id=NULL)  ← ルート: "経営・事業開発"
  └─ Tag (parent_tag_id=上記id)                  ← 中間: "経営企画・事業統括"
       └─ Tag (parent_tag_id=上記id, is_leaf=true) ← リーフ（選択可能）
```

- 6カテゴリ: industry, occupation, role, situation, skill, knowledge
- 親子関係は `parent_tag_id` で表現
- `is_leaf=true` のタグのみ Planter に紐付け可能（中間ノードはナビゲーション用）
- `is_active=true` のタグのみ表示

### レスポンス形式

```python
class TagResponse:
    id: UUID
    name: str
    category: str

class TagTreeNode:
    id: UUID
    name: str
    category: str
    is_leaf: bool
    children: list[TagTreeNode]
```

---

## PlanterTag

Planter と Tag の多対多中間テーブル。

### 操作仕様

- Planter 作成時にタグ ID の配列を受け取り、一括 INSERT
- タグ数の上限なし（Q1 回答: D）
- `is_leaf=true` かつ `is_active=true` のタグ ID のみ受け付ける（バリデーション）
- Planter 削除時は Planter のソフトデリートのみ（PlanterTag は残す）

---

## User（U2 で拡張）

U1 で定義済み。U2 では以下を追加:

### 追加カラム

| カラム | 型 | 用途 |
|---|---|---|
| onboarded_at | datetime \| None | オンボーディング完了日時。NULL = 未完了 |

新規マイグレーション: `supabase/migrations/00004_add_onboarded_at.sql`

```sql
ALTER TABLE users ADD COLUMN onboarded_at TIMESTAMPTZ;
```

### レスポンス形式（拡張）

```python
class UserResponse:
    id: UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    insight_score: float
    role: str
    onboarded_at: datetime | None  # 追加
    created_at: datetime
```

### 更新リクエスト形式（拡張）

```python
class UserUpdate:
    display_name: str | None = None
    bio: str | None = None
    tag_ids: list[UUID] | None = None        # 追加: ユーザータグ設定
    complete_onboarding: bool | None = None   # 追加: オンボーディング完了フラグ
```

---

## UserTag

User と Tag の多対多中間テーブル。U1 でスキーマ定義済み。U2 でオンボーディング時のタグ設定 API を追加。

### 操作仕様

- オンボーディング完了時（`PATCH /users/me` で `complete_onboarding: true`）にタグ ID の配列を受け取る
- 全置換方式: 既存の UserTag を DELETE → 新しいタグ ID で一括 INSERT
- `is_leaf=true` かつ `is_active=true` のタグ ID のみ受け付ける（PlanterTag と同じルール）
- タグ数の上限なし
- tag_ids が空配列 or 未指定の場合はタグ紐付けなし（任意項目）

---

## PlanterFollow（自動フォロー）

Seed 投稿時に投稿者が自動で Planter をフォローする。U2 ではこの自動フォローのみ実装。フォロー/アンフォロー UI は U6 で実装。

### 操作仕様

- Planter 作成トランザクション内で `planter_follows` に INSERT
- `user_id` + `planter_id` の一意制約あり
