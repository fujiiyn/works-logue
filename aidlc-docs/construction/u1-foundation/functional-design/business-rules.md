# U1 Foundation — Business Rules

## 概要

U1 スコープのビジネスルール。認証・ユーザー管理・ソフトデリート・データ整合性に関するルール。

---

## BR-01: 認証フロー

### JWT 検証（AuthMiddleware）

1. リクエストの `Authorization: Bearer <token>` ヘッダーから JWT を取得
2. Supabase の JWKS エンドポイントから公開鍵を取得（キャッシュ付き）
3. JWT を RS256 で検証（署名・有効期限・issuer）
4. JWT payload から `sub`（Supabase Auth user ID）を抽出
5. `users` テーブルで `auth_id = sub` のレコードを検索
6. レコードが存在しない場合 → BR-02（自動作成）を実行
7. `deleted_at IS NOT NULL` の場合 → 403 Forbidden
8. 検証済みユーザーをリクエストコンテキストに注入

### 非認証アクセス

- `GET` 系エンドポイント（フィード・Planter 詳細・プロフィール閲覧）は認証不要
- `POST/PATCH/DELETE` 系は認証必須
- 非認証リクエストには `current_user = None` を注入（閲覧カウント等に利用）

### AuthMiddleware の2モード

| モード | 用途 | 認証なし時の挙動 |
|---|---|---|
| `require_auth` | 書き込み系エンドポイント | 401 Unauthorized を返す |
| `optional_auth` | 読み取り系エンドポイント | `current_user = None` でリクエスト続行 |

---

## BR-02: ユーザー自動作成（初回ログイン）

1. JWT 検証成功後、`users` テーブルに `auth_id` が存在しない場合
2. Supabase Auth からユーザーメタデータを取得（email, name 等）
3. 新規 `users` レコードを作成:
   - `auth_id`: JWT の `sub`
   - `display_name`: Auth メタデータの name、なければ email のローカルパート
   - その他: デフォルト値
4. 作成したユーザーをリクエストコンテキストに注入

---

## BR-03: Planter 状態遷移とスコア計算

### Progress Bar 計算ロジック

```
# planters.progress（0.0〜1.0）の計算

if structure_fulfillment < structure_threshold:
    # 条件A 進行中（0〜50%）
    progress = structure_fulfillment / structure_threshold * 0.5

else:
    # 条件A 充足済み、条件B 進行中（50〜100%）
    maturity = maturity_score or 0.0
    progress = 0.5 + (maturity / maturity_threshold) * 0.5

# progress は 0.0〜1.0 にクランプ
```

### Sprout サブステートの判定

| 条件 | サブステート |
|---|---|
| progress < 0.5 | Sprout 1（条件A 進行中） |
| 0.5 ≤ progress < 0.8 | Sprout 2（条件A 充足、条件B 進行中） |
| 0.9 ≤ progress < 1.0 | Sprout 3（蕾：条件B がもう少し） |

※ しきい値（0.5 / 0.8）は `ai_configs` の `bud_threshold` で調整可能

### Planter ステータス遷移

```
seed ─→ sprout: Log が1件以上になった時点
sprout ─→ louge: progress = 1.0（条件A AND 条件B 完全充足）
```

---

## BR-04a: ソフトデリートポリシー

### 対象テーブル

`users`, `planters`, `logs`（`deleted_at` カラムを持つテーブル）

### ルール

1. 削除操作は `deleted_at = now()` を設定する（物理削除しない）
2. 全ての READ クエリは `WHERE deleted_at IS NULL` を付与する
3. SQLAlchemy モデルにデフォルトフィルタを設定（query 時に自動適用）
4. 削除済みレコードの復元は管理操作として将来対応

### カスケード

- Planter を削除しても Log は削除しない（orphan Log は Planter 復元時に必要）
- User を削除しても Planter/Log は削除しない（匿名化して残す）

---

## BR-04b: 管理者機能

### ユーザーロール

| ロール | 権限 |
|---|---|
| `user` | 通常ユーザー。Seed/Log 投稿・閲覧・フォロー |
| `admin` | 全ユーザー権限 + 管理者機能（BAN・アーカイブ・マスタ管理） |

### BAN ルール

1. admin が対象ユーザーの `is_banned = TRUE` を設定
2. BAN されたユーザーは全ての書き込み操作が 403 Forbidden
3. BAN されたユーザーは閲覧は可能（ログイン状態は維持）
4. AuthMiddleware で `is_banned` チェックを追加（書き込み系のみ）
5. BAN 解除は admin が `is_banned = FALSE` に戻す
6. **BAN されたユーザーの既存コンテンツはそのまま表示し続ける**（投稿者名も通常表示、BAN事実は非表示）

### Log 単位の非表示（管理者モデレーション）

1. admin が個別の Log を非表示にできる（`logs.is_hidden = TRUE`）
2. 非表示 Log は一般ユーザーには表示されない
3. admin には「非表示済み」マーク付きで表示される
4. 非表示はソフトデリートとは独立（復元可能な軽い措置）
5. 非表示にされた Log は `log_count` / `contributor_count` の再集計対象外

### Planter アーカイブ・削除

- **アーカイブ**: `planters.status` に `archived` を追加（フィードに表示されないが、直リンクで閲覧可能）
- **削除**: ソフトデリート（BR-03 準拠）

### マスタデータ管理

- `seed_types`: ジャンルの追加・編集・無効化（`is_active`）
- `tags`: タグの追加・編集・親タグ変更・表示順変更
- 管理画面は最低限の CRUD UI（admin ロール限定）

### AI 設定管理

- `ai_configs` テーブルで AI モデル名・プロンプト・閾値を管理
- 管理画面から各設定を編集可能（admin ロール限定）
- モデル切り替え: スコアリング用（軽量）、Louge 生成用（高品質）、ファシリテート用を個別指定
- プロンプト編集: 条件A/B の判定プロンプト、Louge 生成プロンプト、ファシリテートプロンプトを管理画面から変更可能
- 閾値変更: 条件A 充足率閾値、条件B スコア閾値、最低参加者数、最低 Log 数を管理画面から調整可能
- 変更履歴: `updated_at` / `updated_by` で最終更新者を記録

---

## BR-07: タグ選択ルール（タクソノミー型）

### 基本方針

DB に保存されるのは**リーフタグ（`is_leaf = TRUE`）のみ**。親タグは UI 上のグルーピング・検索用。

### UI 上の挙動

1. タグピッカーで親タグをクリック → 配下の全リーフタグが選択される（`planter_tags` / `user_tags` にリーフのみ INSERT）
2. タグピッカーでリーフタグをクリック → そのリーフタグのみ選択される
3. 親タグのチェックを外す → 配下の全リーフタグが解除される

### 検索時の挙動

1. 親タグで検索 → `parent_tag_id` を再帰的に辿り、配下リーフを持つ Planter/User を返す
2. リーフタグで検索 → そのタグを持つ Planter/User を返す

### DB 制約

- `planter_tags.tag_id` / `user_tags.tag_id` は `is_leaf = TRUE` のタグのみ参照可能（アプリケーション層で検証）
- `tags.is_leaf` は子タグが存在するかどうかで自動判定（管理画面でタグ追加時に親の `is_leaf` を FALSE に更新）

---

## BR-05: タイムスタンプ自動更新

- `created_at`: レコード作成時に `now()` を自動設定（DB デフォルト）
- `updated_at`: レコード更新時に `now()` を自動設定（DB トリガー or SQLAlchemy イベント）
- タイムゾーン: 全て TIMESTAMPTZ（UTC で保存、表示時にクライアントで変換）

---

## BR-06: 環境分離

| 環境 | Supabase プロジェクト | 用途 |
|---|---|---|
| development | works-logue-dev | ローカル開発・テスト |
| production | works-logue-prod | 本番環境 |

- 環境変数で接続先を切り替え（`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`）
- マイグレーションは両環境に同一のものを適用
- GCP プロジェクトも同様に dev/prod 分離（`GCP_PROJECT_ID`）
