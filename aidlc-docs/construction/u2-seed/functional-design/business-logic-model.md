# U2 Seed — Business Logic Model

## 概要

U2 のビジネスロジックは3つのフローで構成される:
1. **Seed 投稿フロー** — Planter を作成し、タグを紐付け、自動フォローする
2. **フィード取得フロー** — 新着タブの Planter 一覧をカーソルベースで取得する
3. **マスタデータ取得フロー** — SeedType 一覧・Tag ツリーを取得する

---

## フロー1: Seed 投稿

### シーケンス

```
Client (SeedForm)
  |
  |-- POST /api/v1/planters
  |     Body: { title, body, seed_type_id, tag_ids[] }
  |     Header: Authorization: Bearer <JWT>
  |
  v
PlanterRouter.create_planter()
  |
  |-- 1. get_current_user(request)     ← 認証チェック（BAN チェック含む）
  |
  |-- 2. バリデーション
  |     |-- seed_type_id が seed_types に存在 & is_active=true
  |     |-- tag_ids が全て tags に存在 & is_leaf=true & is_active=true
  |     |-- title: 1〜200文字
  |     |-- body: 1〜10000文字
  |
  |-- 3. トランザクション開始
  |     |-- Planter INSERT (status='seed', progress=0, log_count=0, contributor_count=0)
  |     |-- PlanterTag 一括 INSERT
  |     |-- PlanterFollow INSERT (投稿者の自動フォロー)
  |     |-- COMMIT
  |
  |-- 4. レスポンス返却
        |-- 201 Created
        |-- Body: PlanterResponse (Planter + SeedType + User + Tags)
```

### エラーケース

| 条件 | HTTP Status | Error Code |
|---|---|---|
| 未認証 | 401 | not_authenticated |
| BAN ユーザー | 403 | account_banned |
| seed_type_id が無効 | 400 | invalid_seed_type |
| tag_ids に無効な ID | 400 | invalid_tags |
| title が空 or 200文字超 | 422 | validation_error |
| body が空 or 10000文字超 | 422 | validation_error |

---

## フロー2: フィード取得（新着タブ）

### シーケンス

```
Client (PlanterFeed)
  |
  |-- GET /api/v1/planters?limit=20&cursor=<created_at>&cursor_id=<id>
  |     Header: Authorization: Bearer <JWT>  ← オプション（非認証でも取得可）
  |
  v
PlanterRouter.list_planters()
  |
  |-- 1. get_optional_user(request)    ← 認証は任意
  |
  |-- 2. PlanterRepository.list_recent(cursor, cursor_id, limit)
  |     |-- WHERE deleted_at IS NULL
  |     |-- WHERE status != 'archived'
  |     |-- ORDER BY created_at DESC, id DESC
  |     |-- カーソル条件: (created_at, id) < (cursor, cursor_id)
  |     |-- LIMIT limit + 1  ← 次ページ有無の判定用
  |
  |-- 3. 関連データの一括取得（N+1 回避）
  |     |-- User 情報: user_ids → users
  |     |-- SeedType 情報: seed_type_ids → seed_types
  |     |-- Tag 情報: planter_ids → planter_tags → tags
  |
  |-- 4. レスポンス返却
        |-- 200 OK
        |-- Body: CursorPaginatedResponse<PlanterCardResponse>
```

### カーソルベースページネーション仕様

```python
class CursorPaginatedResponse[T]:
    items: list[T]
    next_cursor: str | None  # Base64エンコードした "created_at|id"
    has_next: bool
```

- **カーソル値**: `created_at` + `id` の複合キー（同一 created_at の Planter が複数存在するケースに対応）
- **エンコード**: `base64(f"{created_at.isoformat()}|{id}")` → クライアントは不透明な文字列として扱う
- **デコード**: サーバー側で `cursor` パラメータを分解して `(created_at, id)` ペアに復元
- **limit**: デフォルト 20、最大 50
- **has_next**: `limit + 1` 件取得し、超過分があれば `true`

---

## フロー3: Planter 詳細取得

### シーケンス

```
Client (PlanterDetail page)
  |
  |-- GET /api/v1/planters/{planter_id}
  |     Header: Authorization: Bearer <JWT>  ← オプション
  |
  v
PlanterRouter.get_planter()
  |
  |-- 1. PlanterRepository.get_by_id(planter_id)
  |     |-- WHERE id = planter_id AND deleted_at IS NULL
  |
  |-- 2. 関連データ取得
  |     |-- User (投稿者)
  |     |-- SeedType
  |     |-- Tags
  |
  |-- 3. レスポンス返却
        |-- 200 OK → PlanterResponse (body 含む)
        |-- 404 Not Found → planter_not_found
```

---

## フロー4: SeedType 一覧取得

```
Client (SeedForm)
  |
  |-- GET /api/v1/seed-types
  |
  v
SeedTypeRouter.list_seed_types()  ← 認証不要
  |
  |-- WHERE is_active = true
  |-- ORDER BY sort_order ASC
  |-- レスポンス: list[SeedTypeResponse]
```

---

## フロー5: Tag ツリー取得

```
Client (TagSelector)
  |
  |-- GET /api/v1/tags?category=occupation
  |
  v
TagRouter.list_tags()  ← 認証不要
  |
  |-- 1. WHERE is_active = true
  |-- 2. category パラメータが指定されていれば WHERE category = :category
  |-- 3. 全タグをフラットに取得し、アプリケーション側でツリー構築
  |     |-- parent_tag_id = NULL → ルートノード
  |     |-- parent_tag_id != NULL → 親の children に追加
  |-- 4. レスポンス: list[TagTreeNode] (ルートノードの配列)
```

### ツリー構築ロジック（サーバー側）

```python
def build_tree(flat_tags: list[Tag]) -> list[TagTreeNode]:
    nodes = {t.id: TagTreeNode(id=t.id, name=t.name, category=t.category,
                                is_leaf=t.is_leaf, children=[]) for t in flat_tags}
    roots = []
    for t in flat_tags:
        if t.parent_tag_id is None:
            roots.append(nodes[t.id])
        elif t.parent_tag_id in nodes:
            nodes[t.parent_tag_id].children.append(nodes[t.id])
    return roots
```

- カテゴリ未指定時は全カテゴリのツリーを返す
- `sort_order` 順にソート

---

## フロー6: オンボーディング完了

### シーケンス

```
Client (OnboardingPage)
  |
  |-- PATCH /api/v1/users/me
  |     Body: { display_name, bio?, tag_ids?, complete_onboarding: true }
  |     Header: Authorization: Bearer <JWT>
  |
  v
UserRouter.update_me()
  |
  |-- 1. get_current_user(request)     ← 認証チェック
  |
  |-- 2. バリデーション
  |     |-- display_name: 必須（complete_onboarding=true の場合）、1〜100文字
  |     |-- tag_ids: 各 ID が tags に存在 & is_leaf=true & is_active=true
  |
  |-- 3. トランザクション
  |     |-- display_name / bio 更新
  |     |-- UserTag 全置換（DELETE existing → INSERT new）
  |     |-- onboarded_at = now()（complete_onboarding=true の場合）
  |     |-- COMMIT
  |
  |-- 4. レスポンス返却
        |-- 200 OK
        |-- Body: UserResponse (onboarded_at 含む)
```

### リダイレクトチェーン

```
ユーザー操作（例: + Seed ボタン）
  |
  |-- 未ログイン → /login?redirect=/seed/new
  |                    ↓
  |              ログイン成功
  |                    ↓
  |           onboarded_at NULL? ──YES──→ /onboarding?redirect=/seed/new
  |                    |                         ↓
  |                   NO                   表示名設定（必須）
  |                    |                   bio・タグ（任意）
  |                    |                         ↓
  |                    |                   完了 → PATCH /users/me
  |                    ↓                         ↓
  |              /seed/new ←─────────── redirect パラメータの URL へ遷移
```

- `redirect` パラメータは login → onboarding → 完了後まで持ち回す
- redirect 未指定時のデフォルト遷移先: `/`
- 閲覧ページ（フィード、Planter 詳細）へのアクセスはオンボーディング未完了でもブロックしない

### エラーケース

| 条件 | HTTP Status | Error Code |
|---|---|---|
| 未認証 | 401 | not_authenticated |
| display_name が空（complete_onboarding=true 時） | 422 | validation_error |
| tag_ids に無効な ID | 400 | invalid_tags |

---

## Repository 層の責務

### PlanterRepository

| メソッド | 責務 |
|---|---|
| `create(planter: Planter) -> Planter` | INSERT + flush + refresh |
| `get_by_id(id: UUID) -> Planter \| None` | 単一取得（deleted_at IS NULL） |
| `list_recent(cursor, cursor_id, limit) -> list[Planter]` | 新着フィード取得 |

### TagRepository

| メソッド | 責務 |
|---|---|
| `list_by_category(category: str \| None) -> list[Tag]` | カテゴリ別取得（is_active=true） |
| `get_by_ids(ids: list[UUID]) -> list[Tag]` | ID リストで一括取得（バリデーション用） |
| `attach_to_planter(planter_id, tag_ids) -> None` | PlanterTag 一括 INSERT |

### FollowRepository（U2 スコープ: 自動フォローのみ）

| メソッド | 責務 |
|---|---|
| `follow_planter(user_id, planter_id) -> None` | PlanterFollow INSERT |
