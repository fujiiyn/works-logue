# U2 Seed — Business Rules

## BR-U2-01: Seed 投稿の権限

- 認証済みユーザーのみ Seed を投稿できる（`get_current_user` で検証）
- BAN ユーザー（`is_banned=true`）は投稿不可（403）
- ソフトデリート済みユーザー（`deleted_at IS NOT NULL`）は認証段階で拒否（403）

## BR-U2-02: Seed 投稿のバリデーション

| フィールド | ルール |
|---|---|
| title | 必須。1〜200文字。前後の空白はトリム |
| body | 必須。1〜10000文字。前後の空白はトリム |
| seed_type_id | 必須。UUID。`seed_types` に存在し `is_active=true` であること |
| tag_ids | 任意（空配列可）。各 ID が `tags` に存在し `is_leaf=true` かつ `is_active=true` であること。重複 ID は除外 |

## BR-U2-03: Planter 初期状態

Seed 投稿で作成される Planter は以下の初期状態を持つ:

| カラム | 初期値 |
|---|---|
| status | `'seed'` |
| progress | `0.0` |
| log_count | `0` |
| contributor_count | `0` |
| structure_fulfillment | `0.0` |
| maturity_score | `NULL` |
| louge_content | `NULL` |
| parent_planter_id | `NULL` |

## BR-U2-04: 投稿者の自動フォロー

- Seed 投稿時、投稿者は自動的にその Planter をフォローする
- `planter_follows` テーブルに `(user_id, planter_id)` を INSERT
- Planter 作成と同一トランザクション内で実行

## BR-U2-05: フィード閲覧の権限

- 非認証ユーザーでもフィード・Planter 詳細の閲覧が可能
- ソフトデリート済み Planter（`deleted_at IS NOT NULL`）はフィードに表示しない
- アーカイブ済み Planter（`status='archived'`）はフィードに表示しない

## BR-U2-06: フィードのソート・ページネーション

- 新着タブ: `created_at DESC, id DESC` でソート
- カーソルベースページネーション（`cursor` + `cursor_id`）
- デフォルト件数: 20件、最大: 50件
- カーソル値はサーバーが生成する不透明な文字列（Base64）

## BR-U2-07: タグの表示ルール

- `is_active=false` のタグは API レスポンスに含めない
- タグはカテゴリごとに階層ツリー形式で返す
- `is_leaf=true` のタグのみ Planter への紐付けが可能
- 親タグ（`is_leaf=false`）はナビゲーション・グルーピング目的のみ

## BR-U2-08: SeedType の表示ルール

- `is_active=false` の SeedType は API レスポンスに含めない
- `sort_order ASC` で並び替え
- SeedType は読み取り専用（管理は U7 Admin で実装）

## BR-U2-09: ソフトデリートポリシー

- Planter の削除は `deleted_at` に現在時刻を設定（物理削除しない）
- 全クエリで `WHERE deleted_at IS NULL` を自動適用
- 関連する PlanterTag・PlanterFollow はそのまま残す（参照整合性のため）

## BR-U2-10: Planter 詳細の表示ルール（U2 スコープ）

- Seed 情報のみ表示（タイトル・本文・タグ・投稿者・投稿タイプ・日時）
- Log 一覧・Log 投稿フォームは U3 で追加
- progress / log_count / contributor_count は表示する（U2 時点では全て 0）

## BR-U2-11: オンボーディングリダイレクト

- ログイン済みかつ `onboarded_at IS NULL` のユーザーが、閲覧以外のページ（`/seed/new` 等）にアクセスした場合 → `/onboarding?redirect=元URL` へ遷移
- フィード（`/`）や Planter 詳細（`/p/{id}`）などの閲覧ページはオンボーディング未完了でもアクセス可能
- `/login` と `/onboarding` 自体へのアクセスはリダイレクトしない（無限ループ防止）
- auth-context.tsx の useEffect で user ロード後に判定

## BR-U2-12: オンボーディング必須項目

- `display_name` は必須（1〜100文字、前後トリム）
- `complete_onboarding: true` を送信するには `display_name` が空でないこと
- `bio` は任意（未入力可）
- `tag_ids` は任意（空配列可）
- オンボーディング画面の「設定を完了する」ボタンは `display_name` 未入力時に disabled

## BR-U2-13: UserTag バリデーション

- PlanterTag と同じルール: `is_leaf=true` かつ `is_active=true` のタグ ID のみ受け付ける
- タグ数の上限なし
- 全置換方式: 既存の UserTag を全削除してから新しいタグを INSERT
- 重複 ID は除外

## BR-U2-14: リダイレクトチェーン

- `redirect` クエリパラメータを login → onboarding → 完了後まで持ち回す
- ログイン画面: `/login?redirect=/seed/new`
- オンボーディング画面: `/onboarding?redirect=/seed/new`
- オンボーディング完了後: `redirect` パラメータの URL へ遷移（未指定時は `/`）
- 外部 URL やプロトコル付き URL は無視してデフォルト（`/`）へ遷移（オープンリダイレクト防止）
