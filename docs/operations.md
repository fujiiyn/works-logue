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

---

## ドメイン運用（workslogue.com）

本サービスの本番ドメインは `workslogue.com`。Cloud Run の domain mappings 機能を
使って `*.run.app` URL から切り替えている。詳細な切替手順・DNS 仕様・ロール
バック手順は AI-DLC ドキュメントを参照する。

| 用途 | URL | バックエンド |
|---|---|---|
| Web | `https://workslogue.com` | Cloud Run `works-logue-web` |
| API | `https://api.workslogue.com` | Cloud Run `works-logue-api` |

**詳細ドキュメント**:

- 切替プラン: `aidlc-docs/operations/plans/domain-mapping-plan.md`
- DNS レコード仕様: `aidlc-docs/operations/domain-mapping/dns-records.md`
- gcloud / Search Console 操作: `aidlc-docs/operations/domain-mapping/cloud-run-mapping.md`
- 検証手順: `aidlc-docs/operations/domain-mapping/verification.md`
- ロールバック: `aidlc-docs/operations/domain-mapping/rollback.md`

### 1. SSL 証明書の状態確認 / 強制再発行

Google managed certificate は自動で更新されるため、通常は何もしなくて良い。
状態確認のみ:

```bash
gcloud run domain-mappings describe \
  --domain=workslogue.com --region=asia-northeast1 \
  --format='value(status.conditions)'

gcloud run domain-mappings describe \
  --domain=api.workslogue.com --region=asia-northeast1 \
  --format='value(status.conditions)'
```

万一再発行が必要な場合は mapping を削除→再作成する（DNS は維持で OK、伝播済みのため）:

```bash
gcloud run domain-mappings delete --domain=<domain> --region=asia-northeast1
gcloud run domain-mappings create --service=<service> --domain=<domain> --region=asia-northeast1
```

### 2. サブドメインの追加（例: `blog.workslogue.com`）

新しい Cloud Run サービスを公開する場合の手順:

```bash
# (1) サービスをデプロイした後
gcloud run domain-mappings create \
  --service=<new-service> \
  --domain=blog.workslogue.com \
  --region=asia-northeast1

# (2) 出力された CNAME を DNS に登録
# blog CNAME ghs.googlehosted.com.

# (3) 証明書発行を待つ
gcloud run domain-mappings describe --domain=blog.workslogue.com --region=asia-northeast1
```

### 3. CORS 許可元の変更

Web のドメインを増やしたい場合、`.github/workflows/cd.yml` の `CORS_ORIGINS`
にカンマ区切りで追加する:

```yaml
CORS_ORIGINS=https://workslogue.com,https://staging.workslogue.com
```

push 後に CD が走り API 側に反映される。確認は開発者ツールの Network タブで
`Access-Control-Allow-Origin` レスポンスヘッダを見る。

### 4. Supabase Auth の URL 設定

ドメイン切替時は Supabase Console → Authentication → URL Configuration の
**Site URL** と **Redirect URLs** も合わせて更新する。移行期間中は新旧両方を
Redirect URLs に登録しておき、安定確認後に旧 URL を削除する。

### 5. cutover（旧 URL → 新ドメイン）の安全手順

ダウンタイムを避けるため、以下の順番を厳守:

1. domain mapping 作成 + DNS 設定（ここまでは既存 `*.run.app` URL は影響なし）
2. SSL 証明書発行確認（`CertificateProvisioned: True`）
3. 新ドメインでブラウザ目視確認（旧 CORS 設定なので Web → API は失敗するが、Web の表示自体は OK）
4. Supabase Auth Site URL を新ドメインに更新（Redirect URLs に旧も残す）
5. `cd.yml` の `CORS_ORIGINS` と `NEXT_PUBLIC_API_URL` を新ドメインに更新 → CD 起動
6. 新ドメインで E2E ゴールデンパス確認
7. （1〜2 週間後）旧 URL を Redirect URLs / CORS から削除

逆順にやると CORS で全 API リクエストが落ちて全機能が止まる。注意。

### 6. ロールバック判断

`aidlc-docs/operations/domain-mapping/rollback.md` の判断基準を満たした場合、
即座に `cd.yml` を revert + push し、Supabase Auth Site URL を旧値に戻す。

---

## Supabase Realtime（logs / planters テーブル）

`logs` テーブルは Supabase Realtime の `postgres_changes` 経由でフロントエンド
へ配信される（Planter 詳細ページの LogThread が購読）。`planters` も同様に
スコア更新・status 遷移・Louge 開花を全画面同期するために配信される。
マイグレーションで以下をセットアップ済み:

- `logs` / `planters` を `supabase_realtime` パブリケーションに追加
- 両テーブルの RLS を有効化、`deleted_at IS NULL` の SELECT のみ anon に公開
- `anon`/`authenticated` に対し schema USAGE と table SELECT を GRANT、
  INSERT/UPDATE/DELETE は明示 REVOKE（書き込みは FastAPI=postgres role 経由のみ）
- `planters` は UPDATE 時にフル行を配信するため `REPLICA IDENTITY FULL`

### 動作確認

新しい environment / プロジェクトを立ち上げた際、Supabase ダッシュボードの
**Database → Replication** で `logs` と `planters` が `supabase_realtime`
パブリケーションに含まれていることを確認する。含まれていなければ migration
再適用。

### マイグレーション適用方針

CD でのマイグレーション自動適用機構は現状なし。本番 Supabase へは手元から
psql で直接適用している（`.env.local` の `DATABASE_URL` を使用）:

```bash
DB_URL=$(grep "^DATABASE_URL=" apps/api/.env.local | sed 's/^DATABASE_URL=//; s|+asyncpg||')
psql "$DB_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/<file>.sql
```

`supabase_migrations.schema_migrations` には記録されないため、`supabase db
push` を将来導入する場合は冪等性に依存する（既存マイグレーションは IF NOT
EXISTS / DROP IF EXISTS / UPDATE WHERE 等で再実行安全）。
