# U7 Admin — Business Rules

ID 規則: `BR-A##` で U7 Admin 固有のルール。Q## 確定事項を直接の根拠とする。

## 認可

### BR-A01: Admin 認可（二重防壁・存在秘匿）
- 全ての `/admin` URL（フロント）と `/api/v1/admin/*` エンドポイント（API）は `role = 'admin'` のみ通過
- 非 admin（未ログイン含む）には **404 Not Found** を返す（403 ではない、Q10=B により admin 画面の存在を秘匿）
- フロント: `apps/web/app/admin/layout.tsx` の Server Component で `notFound()` を呼ぶ
- API: AdminMiddleware（FastAPI Depends）で 404 を返す
- BAN 中 admin（理論上ありえないが）/ 削除済 admin も 404

### BR-A02: BAN ユーザーの行動制限（Q1=A）
- `users.is_banned = true` のユーザーは:
  - 新規 Planter 投稿不可（403）
  - 新規 Log 投稿不可（403）
  - プロフィール編集不可（403）
  - フォロー操作不可（403）
- 一方、**既存の投稿（Planter / Log）は表示維持**。フィード・詳細・プロフィールから普通に見える
- 自動ログアウトはしない。再ログインしてもセッションは作れるが、投稿だけが拒否される

### BR-A02b: BAN 中ユーザー向け案内バナー
- AuthContext の `user.is_banned = true` を検知した場合、`LayoutShell` 直下に固定バナー（`BannedBanner`）を表示する
- 文言: 「あなたのアカウントは現在制限されています。投稿・編集・フォロー操作はできません。詳細は運営までお問い合わせください。」
- 表示位置: ヘッダー直下、フィード上部に常時表示（dismiss 不可）
- BAN 解除されると自動的に消える（`refreshUser` ポーリング不要、次回 `useAuth` 再取得時に反映）
- 配色: 赤系 outline（`border-red-300 bg-red-50 text-red-900`）
- ボタン類は出さない（運営連絡先は `mailto:` または運用ドキュメントで案内）
- **AdminLayout には描画しない**: `app/admin/layout.tsx` は `app/layout.tsx` を継承しないため、BannedBanner も自動的に出ない（BR-A19）。BAN 中の admin は BR-A01 により `/admin` にそもそも到達できないので問題ない

**前提**: AuthContext の `AppUser` に `is_banned` フィールドを追加する必要がある（現状の `apps/web/contexts/auth-context.tsx` には `role` のみ含まれており、`is_banned` がない）。これも U7 のフロント差分とする。

### BR-A03: BAN 操作の原子性
- BAN 実行時、`is_banned`、`banned_at`、`ban_reason` は **同一 UPDATE 文** で更新する（不整合を防ぐ）
- BAN 解除時、3 列とも (`true → false`, `now → NULL`, `reason → NULL`) を同時に戻す

## ユーザー管理

### BR-A04: ユーザー検索の条件
- 検索クエリ `q` は **display_name の部分一致** のみ（大文字小文字無視、ILIKE）
- メールアドレスでの検索は MVP 非対応（`users` テーブルに email 列がなく Supabase Auth 側にのみ存在するため、新規 migration を切らない方針と整合させる）。必要時は Supabase 管理画面の Authentication タブで対応する
- ステータスフィルタ: すべて / 正常 / BAN中 の 3 値
- ソート: `created_at DESC` 固定（MVP）

### BR-A05: BAN 理由の入力
- 任意。500 文字まで（Figma `427:159` のテキストエリアに合わせる）
- 空文字 → `NULL` として保存
- BAN 理由は admin 一覧で hover or 詳細展開で確認可能

### BR-A06: 自己 BAN 禁止
- admin が自分自身を BAN する操作は不可（API: 400、UI: 「自分」行に鍵アイコンを表示し操作ボタン非表示）
- Figma `426:159` の自分の行（"Admin (あなた)"）に対応

### BR-A07: 他 admin BAN 禁止
- `target.role = 'admin'` のユーザーへの BAN は不可（400）
- admin 同士の権限管理は本 MVP のスコープ外（DB 直叩きで対処）

### BR-A08: BAN の冪等性
- 既に BAN 中のユーザーへの BAN リクエスト → 200 で現在状態を返す（`banned_at` は更新しない）
- 同じく解除も冪等

## Planter 管理

### BR-A09: アーカイブ vs 削除の二段階（Q2=A）
- **アーカイブ**: `status = 'archived'`。フィードからは消えるが、URL 直叩き（`/p/{id}`）は閲覧可能。**復元可**
- **削除**: `deleted_at = now()` のソフトデリート。フィードからも URL からも完全に不可視。**復元不可**
- admin 画面では両方を別操作として提供する

### BR-A09b: Planter 一覧フィルタ「すべて」の定義
- 「すべて」は **`status IN ('seed','sprout','louge') AND deleted_at IS NULL`**（フィードに出ている Planter のみ）
- アーカイブ / 削除済みは **デフォルトで除外**。それぞれ専用フィルタで切り替えて確認する
- 理由: admin の通常運用は「公開中の不適切投稿の発見・対処」が主であり、archived を毎回ノイズとして表示する必要はない

### BR-A10: アーカイブ復元時の status
- MVP では復元時に `status = 'seed'` に固定する
- 厳密には「アーカイブ前の status に戻す」のが理想だが、その実装は U7 のスコープ外（理由: アーカイブ時点での status を保存する追加列が必要なため）
- 結果として、Sprout や Louge をアーカイブ → 復元すると Seed に戻る。運用ドキュメントに明記する
- **自然な再昇格について**: 復元後に最初の Log が投稿されると、`apps/api/app/routers/logs.py:111-118` の既存ロジック（`status == 'seed'` なら `sprout` に遷移）により Sprout に自動昇格する。Louge については AI 開花の閾値を再度満たすまで戻らない（U4 のスコア再計算）。これらは既存の U3/U4 の振る舞いをそのまま利用する

### BR-A11: 削除済み Planter の操作制限
- `deleted_at IS NOT NULL` の Planter は **復元 UI を表示しない**
- 削除済みフィルタでの一覧表示と、ログ確認のみ可能（DB 直接操作で復活させる場合も MVP では運用判断）

### BR-A12: 削除の typed confirmation（Figma `432:713`）
- 削除実行時、admin にダイアログでタイトルの完全一致入力を求める
- 比較は **trim あり・大文字小文字区別あり**（`input.trim() === planter.title.trim()`）。日本語タイトル前提のため大小文字無視は不要
- フロント検証: 上記が true のときのみ削除ボタンを enable
- API 検証: 同条件を再チェック。一致しなければ 400 "タイトルが一致しません"
- フロント・API の二重検証

### BR-A13: フィード側の整合
- 既存の `GET /planters` 系（U2/U5）は `status IN ('seed','sprout','louge') AND deleted_at IS NULL` でフィルタ済とする
- archived / deleted_at の Planter は U7 の作業によって自動的にフィードから消える（既存ロジックを変更しない）

## SeedType 管理

### BR-A15: SeedType 編集スコープ（Q4=B）
- admin から編集可能なのは **`description`** と **`is_active`** のみ
- `slug` / `name` / `sort_order` は migration 管理
- 物理削除・新規追加は admin UI から不可（必要なら migration を発行）

### BR-A16: description の長さ
- 1〜1000 文字（前後空白トリム後）
- 空文字 → 400 "説明は必須です"

### BR-A17: is_active トグルの即時反映
- `is_active = false` にすると、SeedForm（U2）の選択肢から消える
- 既存 Planter の `seed_type_id` は変えない（参照は維持される）
- 一覧で is_active が即時切り替わる（楽観更新 + API レスポンスで上書き）

## Tags 管理

### BR-A18: Tags の admin UI スコープ外（Q9=D）
- `tags` / `tag_categories` テーブルへの admin 操作 UI は U7 では作らない
- 追加・編集・削除はすべて migration で実施

## 監査・ログ

### BR-A14: Cloud Logging 構造化ログ（Q5=B）
- 専用テーブル `admin_audit_logs` は作らない
- 代わりに、すべての admin 操作 API で **構造化 JSON ログを Cloud Logging に出力**
- 標準フィールド: `event`, `actor_user_id`, `target_*`, `ts`, （必要に応じ）`before` / `after`, `request_id`
- 出力箇所:
  - AdminMiddleware: 1 リクエストにつき 1 回 `event: "admin.access"` を出力
  - 各操作ハンドラ: 操作成功時に 1 回 `event: "admin.<resource>.<action>"` を出力
  - 同一リクエスト内で `request_id`（FastAPI middleware で生成、UUID v7 等）を共有し、access ログと操作ログが trace で紐付くようにする
- ログレベル: `INFO`

## レイアウト

### BR-A19: AdminLayout は完全独立（Q6=A）
- `apps/web/app/admin/layout.tsx` を新規作成し、ルート `app/layout.tsx` の RightSidebar / Sidebar / Header を **継承しない**
- AdminHeader（top bar、admin 表示・ログアウト・サイトに戻る） + AdminSidebar（ダーク緑）の 2 つで構成
- RightSidebar は描画しない（`useRightSidebar` も呼ばない）
- ロゴと「公開サイトに戻る」リンクで通常の `LayoutShell` に戻れる

### BR-A20: AdminSidebar の項目
- ダッシュボード（`/admin`）
- ユーザー管理（`/admin/users`）
- Planter 管理（`/admin/planters`）
- SeedType 管理（`/admin/seed-types`）
- 「公開サイトに戻る」リンク（`/`）
- Tags 管理は項目を出さない（BR-A18）

## 初期 admin の払い出し

### BR-A21: admin 昇格・降格の運用（Q8=C）
- **昇格（初期 admin の作成）**: Supabase 管理画面から `UPDATE users SET role = 'admin' WHERE auth_id = '...'` を手動実行
- **降格・誤昇格の取り消し**: Admin UI には降格機能を提供しない（admin 同士の権限管理は MVP スコープ外）。同じく `UPDATE users SET role = 'user' WHERE id = '...'` で DB 直叩きで対処する
- **緊急時の admin 無効化**: BR-A07 により Admin UI からは BAN できないため、`UPDATE users SET role = 'user', is_banned = true, banned_at = now(), ban_reason = '...'` のように同一 SQL で一括対処する
- 運用ドキュメント（`docs/operations.md` など）にこれらの SQL コマンドと操作手順を残す
- 環境変数による自動昇格は MVP では実装しない
