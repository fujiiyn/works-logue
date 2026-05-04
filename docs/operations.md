# 運用ドキュメント

このドキュメントは、Works Logue の admin 機能で **UI 化されていない運用判断**
を実行するための単一の真実源です。BR-A21 に基づき、admin の払い出し・降格・
緊急対応・タグ管理・email 検索といった操作はすべてここに集約します。

---

## admin の払い出し / 降格 / 緊急無効化（BR-A21）

admin UI からは **新規 admin の払い出し・降格** はできません。誤操作のリスク
を避けるため、Supabase のコンソール（or マイグレーションを介した SQL）で実行
します。

### 1. 初期 admin の作成

Supabase Auth で対象アカウントが既にサインアップ済みであること。

```sql
UPDATE users
SET role = 'admin'
WHERE auth_id = '<SUPABASE_AUTH_USER_UUID>';
```

確認:

```sql
SELECT id, display_name, role, is_banned, deleted_at
FROM users
WHERE auth_id = '<SUPABASE_AUTH_USER_UUID>';
```

### 2. admin の降格

```sql
UPDATE users
SET role = 'user'
WHERE id = '<USER_UUID>';
```

降格すると次回の `/admin` アクセス時に AdminLayout の guard が `notFound()`
を返すため、自動的に admin 画面から締め出されます。

### 3. 緊急時の admin 無効化（rogue admin 対応）

admin 画面から admin ユーザーを BAN することは BR-A07 で禁止されています。
直 SQL で role を user に降格してから BAN します。

```sql
UPDATE users
SET role = 'user',
    is_banned = true,
    banned_at = now(),
    ban_reason = '<理由 - 監査ログとして残す>'
WHERE id = '<USER_UUID>';
```

復旧時は対応する SQL で逆操作してください（`role = 'admin'`、`is_banned =
false`、`banned_at = NULL`、`ban_reason = NULL`）。

---

## タグの追加・並び替え・名称変更（BR-A18）

admin UI にはタグ管理画面はありません。`docs/tags.md` を編集し、
`supabase/migrations/` に新しい migration を発行してください。

```bash
# 例: 新しい職種タグを追加する
# supabase/migrations/<timestamp>_add_tag_xxx.sql に書く
INSERT INTO tags (name, category, is_leaf, sort_order, parent_id)
VALUES ('XXX', 'occupation', true, 99, '<parent_uuid>');
```

スコアリング・検索インデックスへの影響を確認した上で本番に適用してください。

---

## ユーザーの email 検索

admin UI のユーザー検索は `display_name` の部分一致のみです（BR-A04）。
email でユーザーを特定する必要がある場合、Supabase 管理コンソールの
**Authentication → Users** タブで email を検索し、`auth.users.id` を取得して
ください。その UUID は `users.auth_id` と紐付きます。

```sql
-- email から内部 user_id を引く
SELECT u.id, u.display_name, u.role, u.is_banned
FROM users u
JOIN auth.users a ON a.id = u.auth_id
WHERE a.email = '<EMAIL>';
```

---

## 構造化ログ（BR-A14）

admin 操作はすべて Cloud Logging に構造化 JSON として出力されます。trace に
は middleware が付与する `request_id` (UUID) が含まれます。

| event | 出力箇所 | キー |
|---|---|---|
| `admin.access` | `require_admin` 通過時 | `actor_user_id`, `path`, `method` |
| `admin.user.ban` | BAN 操作 | `actor_user_id`, `target_user_id`, `ban_reason` |
| `admin.user.unban` | BAN 解除 | `actor_user_id`, `target_user_id` |
| `admin.planter.archive` | アーカイブ | `actor_user_id`, `planter_id` |
| `admin.planter.restore` | 復元 | `actor_user_id`, `planter_id` |
| `admin.planter.delete` | 削除 | `actor_user_id`, `planter_id`, `title` |
| `admin.seed_type.update` | 説明更新 / 公開トグル | `actor_user_id`, `seed_type_id`, `before_*`, `after_*` |

Cloud Logging クエリ例:

```
jsonPayload.event="admin.user.ban"
jsonPayload.actor_user_id="<UUID>"
```
