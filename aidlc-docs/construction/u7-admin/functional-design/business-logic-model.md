# U7 Admin — Business Logic Model

API は `/api/v1/admin/...` 配下に集約する。すべての admin エンドポイントは **AdminMiddleware** で `role=admin` を強制する（Q10=B により非 admin には `404 Not Found` を返し、admin 画面の存在自体を秘匿する）。

## 0. AdminMiddleware（BC-23 新規）

```
入力: Request (認証済 User)
出力: 通過 or 404 Not Found

1. AuthMiddleware が認証済 User を解決済みである前提（U1 BC-01）
2. user.role != 'admin' OR user.is_banned == true OR user.deleted_at != null
   → 404 Not Found を返す（403 ではない。admin 画面の存在を秘匿: BR-A01）
3. 通過時、後続のハンドラに admin User を引き渡す
4. 同時に Cloud Logging に admin リクエストの構造化ログを出力（BR-A14）
   { "event": "admin.access", "actor_user_id": "...", "path": "...", "method": "...",
     "request_id": "..." }
   ※ request_id は FastAPI middleware で生成し ContextVar 経由で各ハンドラから参照可能にする。
     後続の操作ログ（admin.user.ban 等）と同一 request_id で trace 紐付けする（BR-A14）
```

`/api/v1/admin/*` ルーターに `Depends(require_admin)` として適用する。

---

## 1. ダッシュボード統計

### 1a. 統計カード取得 (`GET /api/v1/admin/stats`)

```
Output: AdminStatsResponse {
  total_users: int,
  total_planters: int,
  new_planters_today: int,
  pending_louge_count: int
}

1. AdminMiddleware を通過した admin User を取得
2. 4本の COUNT クエリを並列実行（Q7=A: リアルタイム集計、MVP では十分速い想定）:
   a. total_users:        SELECT COUNT(*) FROM users WHERE deleted_at IS NULL
   b. total_planters:     SELECT COUNT(*) FROM planters WHERE deleted_at IS NULL
   c. new_planters_today: SELECT COUNT(*) FROM planters
                          WHERE created_at >= date_trunc('day', now() AT TIME ZONE 'Asia/Tokyo')
                            AND deleted_at IS NULL
   d. pending_louge_count: SELECT COUNT(*) FROM planters
                          WHERE status = 'sprout'
                            AND deleted_at IS NULL
                            -- 「開花待ち」= sprout 状態のもの全件
                            -- ⚠ NOTE: U4 の Louge 開花閾値（条件 A AND 条件 B）に到達済みの件数では
                            -- ない。MVP ではダッシュボードの目安数値として「Sprout 全件」を返す。
                            -- 「閾値到達かつ未開花」の厳密カウントは将来拡張（U4 の maturity_score
                            -- 等を JOIN）。ハンドラ docstring にも同旨を記載する。
3. レスポンス組み立てて返却
```

**注**: 「本日」は JST（Asia/Tokyo）で判定する（運用国に合わせる）。`COUNT(*)` は MVP の規模では問題なし、データ量増加時はマテリアライズドビューに切替（Q7=A）。

---

## 2. ユーザー管理

### 2a. ユーザー一覧 (`GET /api/v1/admin/users`)

```
Input: query params
  - q: string (optional) — display_name の部分一致（大文字小文字無視）
  - status: 'all' | 'normal' | 'banned' (default 'all')
  - page: int (default 1)
  - per_page: int (default 50, max 100)
Output: AdminUserListResponse {
  items: AdminUserItem[],
  total: int,
  page: int,
  per_page: int
}

AdminUserItem {
  id, display_name, avatar_url, role,
  is_banned, banned_at, ban_reason,
  planter_count: int,     -- 集計
  log_count: int,         -- 集計
  created_at,
  is_self: bool           -- リクエストユーザーと同一なら true
}

1. AdminMiddleware を通過した admin User を取得
2. ベースクエリ: users WHERE deleted_at IS NULL
3. status フィルタ:
   - normal: AND is_banned = false
   - banned: AND is_banned = true
4. q フィルタ:
   - display_name ILIKE :q_pattern  -- :q_pattern = f"%{q.lower()}%"
5. ORDER BY created_at DESC
6. ページング (LIMIT/OFFSET)
7. planter_count / log_count を 2 本の集計クエリで付与:
   - SELECT user_id, COUNT(*) FROM planters
     WHERE user_id IN :ids AND deleted_at IS NULL GROUP BY user_id
   - SELECT user_id, COUNT(*) FROM logs
     WHERE user_id IN :ids AND deleted_at IS NULL GROUP BY user_id
   それぞれ dict 化し、items にマージする（N+1 回避）
8. items に is_self を付与（i.id == admin_user.id）
9. レスポンス返却
```

**email を扱わない理由**: `users` テーブルに `email` 列は存在せず、Supabase Auth 側にのみ保持されている（`apps/api/app/dependencies.py` で JWT claim から都度取得）。U7 では新規 migration を切らない方針（Q4=B 系）に従い、email 検索・表示は MVP スコープ外とする。必要な運用は Supabase 管理画面の Authentication タブで対応する。

### 2b. ユーザー BAN (`POST /api/v1/admin/users/{user_id}/ban`)

```
Input:
  - user_id: UUID (path)
  - body: { reason: string (max 500, optional) }
Output: AdminUserItem (更新後)

1. AdminMiddleware 通過
2. 対象 User を取得（deleted_at IS NULL）
   存在しない → 404
3. 自己 BAN 禁止: target.id == admin.id → 400 "自分を BAN できません"（BR-A06）
4. admin 同士 BAN 禁止: target.role == 'admin' → 400 "admin ユーザーは BAN できません"（BR-A07）
5. 既に BAN 中なら冪等扱い: is_banned == true → 200 で現在値を返す
6. UPDATE users SET
     is_banned = true,
     banned_at = now(),
     ban_reason = :reason
   WHERE id = :user_id
7. Cloud Logging:
   { "event": "admin.user.ban", "actor_user_id": admin.id,
     "target_user_id": user_id, "ban_reason": reason, "ts": now }
8. 更新後の AdminUserItem を返却
```

**副作用（既存実装側で担保すべき）**: `is_banned = true` のユーザーは自身でログインしたとき、Planter / Log の **新規投稿エンドポイントで 403** を返す（U2/U3 側で `current_user.is_banned` チェックを追加）。既存投稿は表示維持（Q1=A、BR-A02）。

### 2c. ユーザー BAN 解除 (`POST /api/v1/admin/users/{user_id}/unban`)

```
Input: user_id (UUID)
Output: AdminUserItem (更新後)

1. AdminMiddleware 通過
2. 対象 User 取得（deleted_at IS NULL） → 404 if not found
3. 既に解除済み（is_banned == false）なら冪等扱い: 200
4. UPDATE users SET
     is_banned = false,
     banned_at = NULL,
     ban_reason = NULL
   WHERE id = :user_id
5. Cloud Logging:
   { "event": "admin.user.unban", "actor_user_id": admin.id,
     "target_user_id": user_id, "ts": now }
6. 更新後の AdminUserItem を返却
```

---

## 3. Planter 管理

### 3a. Planter 一覧 (`GET /api/v1/admin/planters`)

```
Input: query params
  - q: string (optional) — title 部分一致
  - status: 'all' | 'seed' | 'sprout' | 'louge' | 'archived' | 'deleted' (default 'all')
  - page, per_page
Output: AdminPlanterListResponse {
  items: AdminPlanterItem[], total, page, per_page
}

AdminPlanterItem {
  id, title, status, seed_type_name,
  author: { id, display_name, avatar_url },
  log_count, contributor_count,
  created_at, updated_at, deleted_at
}

1. AdminMiddleware 通過
2. ベースクエリ:
   - status='all' → planters WHERE status IN ('seed','sprout','louge') AND deleted_at IS NULL
                    （= フィードに出ているもの。archived は含めない）
   - status='deleted' → planters WHERE deleted_at IS NOT NULL
   - その他 ('seed'/'sprout'/'louge'/'archived') → planters WHERE status = :status AND deleted_at IS NULL
3. q フィルタ: title ILIKE :q_pattern  -- :q_pattern = f"%{q.strip()}%"
4. ORDER BY:
   - status='deleted' → ORDER BY deleted_at DESC
   - その他 → ORDER BY updated_at DESC
5. JOIN users (author) / seed_types (name) / 集計列
6. ページング、レスポンス返却
```

### 3b. Planter アーカイブ (`POST /api/v1/admin/planters/{planter_id}/archive`)

```
Input: planter_id
Output: AdminPlanterItem (更新後)

1. AdminMiddleware 通過
2. Planter 取得（deleted_at IS NULL） → 404 if not found
3. 既に archived → 冪等で 200
4. UPDATE planters SET status = 'archived', updated_at = now()
5. Cloud Logging:
   { "event": "admin.planter.archive", "actor_user_id": admin.id,
     "planter_id": planter_id, "ts": now }
6. レスポンス返却
```

**副作用**: フィード（U2/U5）は `status IN ('seed','sprout','louge')` でフィルタ済の前提。`archived` は自動的に除外される。URL 直叩き（`/p/{id}`）は閲覧可（Q2=A）。

### 3c. Planter 復元 (`POST /api/v1/admin/planters/{planter_id}/restore`)

```
Input: planter_id
Output: AdminPlanterItem (更新後)

1. AdminMiddleware 通過
2. Planter 取得（deleted_at IS NULL） → 404 if not found
3. status != 'archived' → 400 "アーカイブされていません"
4. UPDATE planters SET status = 'seed', updated_at = now()
   ※ 復元時の status 戦略は BR-A10 を参照（MVP では 'seed' 固定 + 後続 Log で自動 sprout 昇格）
5. Cloud Logging:
   { "event": "admin.planter.restore", "actor_user_id": admin.id,
     "planter_id": planter_id, "ts": now }
6. レスポンス返却
```

### 3d. Planter 削除 (`DELETE /api/v1/admin/planters/{planter_id}`)

```
Input:
  - planter_id (path)
  - body: { confirm_title: string (required) }   -- typed confirmation
Output: 204 No Content

1. AdminMiddleware 通過
2. Planter 取得（deleted_at IS NULL） → 404 if not found
3. typed confirmation 検証:
   - confirm_title.strip() != planter.title.strip()
     → 400 "タイトルが一致しません"（BR-A12）
4. UPDATE planters SET deleted_at = now()  -- ソフトデリート
5. Cloud Logging:
   { "event": "admin.planter.delete", "actor_user_id": admin.id,
     "planter_id": planter_id, "title": planter.title, "ts": now }
6. 204 No Content
```

---

## 4. SeedType 管理

### 4a. SeedType 一覧 (`GET /api/v1/admin/seed-types`)

```
Input: query params
  - status: 'all' | 'active' | 'inactive' (default 'all')
Output: AdminSeedTypeItem[] {
  id, slug, name, description, sort_order, is_active, created_at
}

1. AdminMiddleware 通過
2. ベースクエリ: seed_types
3. status='active' → WHERE is_active = true
   status='inactive' → WHERE is_active = false
4. ORDER BY sort_order ASC
5. 全件返却（高々 8〜20 件想定）
```

### 4b. SeedType description 更新 (`PATCH /api/v1/admin/seed-types/{seed_type_id}`)

```
Input:
  - seed_type_id (path)
  - body: { description: string }   -- 1..1000 文字
Output: AdminSeedTypeItem (更新後)

1. AdminMiddleware 通過
2. SeedType 取得 → 404 if not found
3. バリデーション: description は 1〜1000 文字（前後空白トリム）
4. before = { description: ..., is_active: ... } を退避
5. UPDATE seed_types SET description = :description
6. Cloud Logging:
   { "event": "admin.seed_type.update", "actor_user_id": admin.id,
     "seed_type_id": id, "before": before, "after": after, "ts": now }
7. レスポンス返却
```

### 4c. SeedType is_active トグル (`POST /api/v1/admin/seed-types/{seed_type_id}/toggle-active`)

```
Input: seed_type_id (path)
Output: AdminSeedTypeItem (更新後)

1. AdminMiddleware 通過
2. SeedType 取得 → 404 if not found
3. before / after を構築（is_active を反転）
4. UPDATE seed_types SET is_active = NOT is_active
5. Cloud Logging:
   { "event": "admin.seed_type.update", "actor_user_id": admin.id,
     "seed_type_id": id, "before": before, "after": after, "ts": now }
6. レスポンス返却
```

**注**: `slug` / `name` / `sort_order` を変更する API は **意図的に提供しない**（Q4=B）。

---

## 5. AdminRouter（BC-24 新規）

FastAPI ルーター: `apps/api/routers/admin.py`

```
@router.get("/stats", response_model=AdminStatsResponse, dependencies=[Depends(require_admin)])
@router.get("/users", response_model=AdminUserListResponse, dependencies=[Depends(require_admin)])
@router.post("/users/{user_id}/ban", response_model=AdminUserItem, dependencies=[Depends(require_admin)])
@router.post("/users/{user_id}/unban", response_model=AdminUserItem, dependencies=[Depends(require_admin)])
@router.get("/planters", response_model=AdminPlanterListResponse, dependencies=[Depends(require_admin)])
@router.post("/planters/{planter_id}/archive", response_model=AdminPlanterItem, dependencies=[Depends(require_admin)])
@router.post("/planters/{planter_id}/restore", response_model=AdminPlanterItem, dependencies=[Depends(require_admin)])
@router.delete("/planters/{planter_id}", status_code=204, dependencies=[Depends(require_admin)])
@router.get("/seed-types", response_model=list[AdminSeedTypeItem], dependencies=[Depends(require_admin)])
@router.patch("/seed-types/{seed_type_id}", response_model=AdminSeedTypeItem, dependencies=[Depends(require_admin)])
@router.post("/seed-types/{seed_type_id}/toggle-active", response_model=AdminSeedTypeItem, dependencies=[Depends(require_admin)])
```

`require_admin` は AdminMiddleware の薄い Depends 関数として実装する（FastAPI の `Depends` 統合）。

## 6. AdminRepository（BC-25 新規）

`apps/api/repositories/admin_repository.py` に集約。集計クエリと CRUD は単純なので、既存の `UserRepository` / `PlanterRepository` の上に **薄いラッパー** として実装し、admin 専用の集計（planter_count / log_count）と検索は本リポジトリに置く。

| メソッド | 概要 |
|---|---|
| `get_dashboard_stats() -> AdminStats` | §1a の 4 つの COUNT |
| `list_users(q, status, page, per_page) -> (items, total)` | §2a |
| `ban_user(user, reason)` | §2b 中の UPDATE |
| `unban_user(user)` | §2c 中の UPDATE |
| `list_planters(q, status, page, per_page) -> (items, total)` | §3a |
| `archive_planter(planter)` | §3b の UPDATE |
| `restore_planter(planter)` | §3c の UPDATE |
| `soft_delete_planter(planter)` | §3d の UPDATE |
| `list_seed_types(status) -> items` | §4a |
| `update_seed_type_description(seed_type, description)` | §4b |
| `toggle_seed_type_active(seed_type)` | §4c |

## 7. 既存 BAN ガードの再確認（U7 で **追加実装は不要**）

`apps/api/app/dependencies.py:67-91` の `get_current_user` に **既に汎用ガードが実装済み**:

```python
# dependencies.py から抜粋
if user.is_banned:
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        raise HTTPException(status_code=403, detail="Account is banned")
```

これにより、`Depends(get_current_user)` を使っているすべての非 GET エンドポイント
（POST `/planters`, POST `/logs`, PATCH `/users/me`, POST `/users/me/avatar`,
POST/DELETE `/users/{id}/follow`, POST/DELETE `/planters/{id}/follow` 等）が
BR-A02 の要件（既存投稿は表示維持・新規投稿のみ不可）を自動的に満たす。

| BR-A02 が要求する挙動 | 担保箇所 |
|---|---|
| 新規 Planter 投稿不可 | `get_current_user` の汎用ガード（POST = 403） |
| 新規 Log 投稿不可 | 同上 |
| プロフィール編集不可 | 同上（PATCH/POST = 403） |
| フォロー操作不可 | 同上（POST/DELETE = 403） |
| 既存投稿の表示は維持 | GET/HEAD/OPTIONS は通過するため自動的に満たされる |

**U7 で行うこと**:
- 上記汎用ガードに **依存していることを Functional Design として明文化**（本セクション）
- `pytest` で Banned ユーザーの非 GET = 403、GET = 200 を網羅するテストを **U7 のテストスコープに含める**（既存実装の振る舞いを契約として固定する）
- 個別ハンドラに `if current_user.is_banned` を **追加しない**（二重ガードで TDD が混乱するため）

## 8. 既存ユニットへの API 拡張（U7 で同時に入れる）

| 対象 API | 変更内容 | 理由 |
|---|---|---|
| `GET /api/v1/users/me`（U1/U6） | レスポンスに `is_banned: bool`、`deleted_at: str \| null` を追加 | フロント `AuthContext.AppUser` で BannedBanner 判定 / Server `getCurrentUser` の AdminGuard 判定に必要 |

`UserMeResponse` Pydantic スキーマを拡張し、TDD で「`is_banned` フィールドが含まれる」テストを追加する。バックエンドモデルには既に存在する列なので新規 migration 不要。
