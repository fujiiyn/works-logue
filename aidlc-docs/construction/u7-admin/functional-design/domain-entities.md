# U7 Admin — Domain Entities

U7 では新規テーブルは作らない。U1 マイグレーション 00001 時点で揃っているフィールドのみを使用する（Q5=B / Q4=B 確定）。

## 1. User（既存・admin 関連フィールドの整理）

`users` テーブル（`supabase/migrations/00001_create_tables.sql` で定義済、確認済）。`role` / `is_banned` / `banned_at` / `ban_reason` / `deleted_at` は全て 00001 時点で実在する列であり、U7 では新規 migration を切らない。

| フィールド | 型 | U7 での意味 |
|---|---|---|
| id | UUID PK | — |
| auth_id | UUID UNIQUE | Supabase Auth ID |
| display_name | varchar(100) | 一覧で表示する名前 |
| avatar_url | text | 一覧サムネイル |
| **role** | varchar(10) default `'user'` | `'user'` / `'admin'`。`'admin'` のみ `/admin` 通過 |
| **is_banned** | bool default false | `true` の間は本人のログイン後に投稿禁止（既存投稿は表示維持: BR-A02） |
| **banned_at** | timestamptz nullable | BAN 実行日時。Q5=B により監査の唯一の痕跡 |
| **ban_reason** | text nullable | BAN 理由（admin が任意入力、Figma `427:159` のテキストエリア） |
| created_at | timestamptz | 一覧の登録日表示 |
| deleted_at | timestamptz nullable | 論理削除済みは admin 一覧の対象外 |

### U7 で扱うステータス

| ステータス | 判定式 | Figma バッジ |
|---|---|---|
| 正常 | `is_banned = false AND deleted_at IS NULL` | "正常" (緑) |
| BAN中 | `is_banned = true AND deleted_at IS NULL` | "BAN中" (赤) |
| 削除済み | `deleted_at IS NOT NULL` | 一覧から除外 |
| Admin | `role = 'admin'` | "Admin" バッジ（自分の行に "（自分）" 表示） |

### 不変条件

- `role = 'admin'` のユーザーは admin 画面で BAN 不可（BR-A07）
- 自分自身は admin 画面で BAN 不可（BR-A06）
- `is_banned` を変更したら必ず `banned_at` / `ban_reason` も同時に更新する（BR-A03）

---

## 2. Planter（既存・archived/deleted フィールドの整理）

`planters` テーブル（00001 で定義済）。

| フィールド | 型 | U7 での意味 |
|---|---|---|
| id | UUID PK | — |
| user_id | UUID FK | 投稿者（一覧で表示） |
| title | varchar(200) | 一覧表示 |
| **status** | varchar(10) | `seed` / `sprout` / `louge` / `archived`。`archived` は admin がアーカイブ済 |
| seed_type_id | UUID FK | フィルタには使わない（参考表示） |
| log_count | int | 一覧の "Logs" 列 |
| contributor_count | int | 一覧の "Contributors" 列 |
| created_at | timestamptz | 一覧の作成日 |
| updated_at | timestamptz | 一覧の更新日 |
| **deleted_at** | timestamptz nullable | ソフトデリート。null でないものはフィードから完全に不可視 |

### U7 で扱うステータス（admin 用フィルタ）

| 表示名 | 判定式 |
|---|---|
| すべて | `status IN ('seed','sprout','louge') AND deleted_at IS NULL`（**フィードに出ているもの**＝archived も削除済みも含まない） |
| Seed | `status = 'seed' AND deleted_at IS NULL` |
| Sprout | `status = 'sprout' AND deleted_at IS NULL` |
| Louge | `status = 'louge' AND deleted_at IS NULL` |
| アーカイブ | `status = 'archived' AND deleted_at IS NULL` |
| 削除済み | `deleted_at IS NOT NULL` |

**「すべて」の定義について**: admin が日常的に確認したいのは「現在ユーザーに見えている Planter」なので、デフォルトで archived を除外する。archived / 削除済みはそれぞれ専用フィルタで明示的に切り替えて確認する。

### archived と deleted_at の役割分担（Q2=A）

| 操作 | 状態変化 | 意味 | 復元 |
|---|---|---|---|
| アーカイブ | `status = 'archived'` | フィード除外、URL 直叩きは閲覧可 | 可（status を元に戻す） |
| 復元 | `status = 'archived' → 元のstatus` | アーカイブから戻す | — |
| 削除 | `deleted_at = now()` | フィード・URL から完全に不可視 | 不可（typed confirmation 必須） |

### 不変条件

- 削除済み（`deleted_at IS NOT NULL`）は復元 UI を表示しない（BR-A11）
- アーカイブ復元時の status については **BR-A10** が単一の真実源（MVP では `seed` 固定 + 後続 Log で自動再昇格）

---

## 3. SeedType（既存・description / is_active のみ admin 編集可）

`seed_types` テーブル（00001 で定義済、00002 で 8 種シード投入済み）。

| フィールド | 型 | U7 での扱い |
|---|---|---|
| id | UUID PK | — |
| slug | varchar(20) UNIQUE | **読み取り専用**（migration 管理） |
| name | varchar(50) | **読み取り専用**（migration 管理） |
| **description** | text | **admin 編集可**（一覧表示・編集モーダル） |
| sort_order | int | **読み取り専用**（migration 管理） |
| **is_active** | bool default true | **admin 編集可**（一覧トグル） |
| created_at | timestamptz | — |

### U7 で扱うフィルタ

| 表示名 | 判定式 |
|---|---|
| すべて | （全件） |
| 公開中 | `is_active = true` |
| 非公開 | `is_active = false` |

### 不変条件（Q4=B）

- admin から `slug` / `name` / `sort_order` の変更不可、新規追加・物理削除も不可
- `description` の更新と `is_active` トグルのみ
- `is_active = false` の SeedType は SeedForm の選択肢から除外（U2 で実装済の前提を利用）。既存 Planter は影響を受けない

---

## 4. Tags（admin UI スコープ外）

Q9=D 確定。`tags` / `tag_categories` テーブルへの admin 操作 UI は U7 では作らない。マイグレーションでのみ管理する。

---

## 5. AdminAuditLog（**導入しない** = Q5=B）

専用テーブルは作らない。次のフィールドのみで運用する：

| 操作 | 残る痕跡 |
|---|---|
| BAN | `users.banned_at`, `users.ban_reason`（誰が BAN したかは Cloud Logging の構造化ログで補完） |
| BAN 解除 | `users.is_banned = false`, `banned_at = NULL`, `ban_reason = NULL`（Cloud Logging に「誰が解除したか」を出力） |
| Planter アーカイブ / 復元 | `planters.status` / `updated_at`（Cloud Logging に admin 操作を出力） |
| Planter 削除 | `planters.deleted_at`（Cloud Logging に「誰が削除したか」を出力） |
| SeedType 編集 | `seed_types.description` / `is_active`（Cloud Logging に before/after を出力） |

**Cloud Logging 構造化ログ仕様（BR-A14）**:
```json
{ "event": "admin.user.ban", "actor_user_id": "...", "target_user_id": "...", "ban_reason": "...", "ts": "..." }
{ "event": "admin.user.unban", "actor_user_id": "...", "target_user_id": "...", "ts": "..." }
{ "event": "admin.planter.archive", "actor_user_id": "...", "planter_id": "...", "ts": "..." }
{ "event": "admin.planter.restore", "actor_user_id": "...", "planter_id": "...", "ts": "..." }
{ "event": "admin.planter.delete", "actor_user_id": "...", "planter_id": "...", "ts": "..." }
{ "event": "admin.seed_type.update", "actor_user_id": "...", "seed_type_id": "...", "before": {...}, "after": {...}, "ts": "..." }
```

## リレーション（U7 で使う範囲のみ）

```
User(role=admin) ──操作──> User(BAN/解除)
                ──操作──> Planter(archive/restore/delete)
                ──操作──> SeedType(description/is_active)
```

新規 FK は追加しない。
