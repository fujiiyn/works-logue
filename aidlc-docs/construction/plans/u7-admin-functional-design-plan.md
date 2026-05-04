# U7 Admin — Functional Design Plan

## Plan Overview

U7 は管理者機能（admin 専用画面）を実装する。**Figma を単一の真実源とする**。スコープ:

- ユーザー BAN / 解除（`users.is_banned`, `banned_at`, `ban_reason`）
- Planter アーカイブ・復元・削除（`planters.status='archived'` / `deleted_at`）
- マスタデータ管理（`seed_types` の **説明（description）編集** + `is_active` トグル）
- AdminMiddleware（`users.role='admin'` チェック）
- /admin 専用レイアウト（AdminHeader + ダーク緑 AdminSidebar + RightSidebar 抑止）

**スコープ外**:
- Log 非表示の Admin UI（スキーマは存在するが U7 では UI を作らない）
- Tags マスタ管理 UI（マイグレーション運用のみ）
- SeedType の新規追加・slug／名称／並び順の編集・物理削除（マイグレーション運用のみ）
- 監査ログ専用テーブル `admin_audit_logs`

依存ユニット: U1 Foundation（DB、認証、SQLAlchemy モデル全量はマイグレーション 00001 時点で揃っている）

Figma 参照: page `admin`（nodeId `420:159`）。主要フレーム:

| nodeId | フレーム |
|---|---|
| 422:159 | Admin / Layout — desktop shell |
| 424:159 | Admin / Dashboard |
| 426:159 | Admin / Users — list (default) |
| 427:159 / 427:400 | Admin / Users — BAN dialog / BAN release dialog |
| 428:159 | Admin / Planters — list (default) |
| 432:159 / 432:435 / 432:713 | Admin / Planters — Archive / Restore / Delete (typed confirmation) dialog |
| 433:159 | Admin / SeedTypes — list |
| 464:2 | Admin / SeedTypes — Edit description dialog |
| 434:159 / 434:391 / 434:678 / 434:949 | Users・Planters の empty state / loading state |

---

## Steps

- [x] **Step 1**: ドメインエンティティ定義
  - [x] 1a: User の admin 関連フィールド整理（`role`, `is_banned`, `banned_at`, `ban_reason`）
  - [x] 1b: Planter のアーカイブ／削除フィールド整理（`status='archived'`, `deleted_at`）
  - [x] 1c: SeedType マスタの編集用エンティティ整理（`description` の更新、`is_active` トグルのみ。`slug` / `name` / `sort_order` は migration 管理）
  - [x] 1d: AdminAuditLog は導入しない（Q5=B 確定）— 既存 `banned_at` / `hidden_by` 等のフィールドのみで運用

- [x] **Step 2**: ビジネスロジックモデル定義
  - [x] 2a: AdminMiddleware（`role=admin` のみ通過、それ以外は Q10=B により `notFound()` で 404）
  - [x] 2b: ダッシュボード統計取得ロジック（総ユーザー数 / 総 Planter 数 / 本日の新規 Planter / 開花待ち Sprout の集計）
  - [x] 2c: ユーザー管理ロジック（一覧取得・検索・フィルタ、BAN／解除、自己 BAN 禁止、BAN 中ユーザーは投稿不可かつ既存投稿は表示維持）
  - [x] 2d: Planter 管理ロジック（一覧取得・状態フィルタ、アーカイブ／復元、ソフトデリート、削除はタイプ確認モーダル）
  - [x] 2e: SeedType マスタ編集（`description` 更新 + `is_active` トグルのみ。追加・並び替え・slug/name 変更は migration）

- [x] **Step 3**: ビジネスルール定義
  - [x] 3a: 認可ルール（`role=admin` 必須、Server Component で `notFound()`、加えてバックエンド AdminMiddleware で二重検証）
  - [x] 3b: BAN 副作用ルール（Q1=A: 既存投稿は表示維持、本人のみログイン後の投稿不可。セッション一括無効化は不要）
  - [x] 3c: アーカイブと削除の使い分けルール（`status='archived'` は復元可、`deleted_at` はソフト削除＝フィード不可視。削除は typed confirmation 必須）
  - [x] 3d: SeedType 編集制約（admin から物理削除・追加・slug/name/sort_order 変更は不可。`description` 編集と `is_active` トグルのみ）
  - [x] 3e: 自己 BAN 禁止 / 他 admin BAN 禁止ルール（Figma の自分の行は鍵アイコンで操作不可）
  - [x] 3f: 監査運用ルール（既存 `banned_at` / `hidden_by` / `hidden_at` のみで運用、Cloud Logging 構造化ログに admin 操作を出力）

- [x] **Step 4**: フロントエンドコンポーネント設計
  - [x] 4a: AdminLayout（AdminHeader + ダーク緑 AdminSidebar + RightSidebar 抑止。`apps/web/app/admin/layout.tsx` で完全独立）
  - [x] 4b: AdminDashboard `/admin`（統計カード 4 枚: 総ユーザー数 / 総 Planter 数 / 本日の新規 Planter / 開花待ち Sprout）
  - [x] 4c: UserManagementTable（一覧、検索、FilterChip すべて／正常／BAN中、BAN／BAN 解除ダイアログ、自分の行は鍵アイコン）
  - [x] 4d: PlanterManagementTable（一覧、状態フィルタ すべて／Seed／Sprout／Louge／アーカイブ／削除済み、Archive／Restore／Delete (typed) ダイアログ）
  - [x] 4e: SeedTypeAdminPage（一覧 + 説明編集モーダル + `is_active` トグル。FilterChip すべて／公開中／非公開）
  - [x] 4f: AdminGuard（Server Component で `role=admin` 以外は `notFound()`。Q10=B）

---

## Questions

> ⚠️ MVP 一人開発のため、迷ったらシンプル側に倒す前提で回答してください。

### Q1: BAN の副作用範囲

ユーザーを BAN したとき、既存の投稿（Planter / Log）の扱いをどうしますか？

- A: 表示は維持。投稿者だけログイン＋投稿不可（最小実装）
- B: 既存投稿は自動的に非公開化（`is_hidden=true` を一括付与）し、解除で戻る
- C: 既存投稿は admin が個別に判断（一覧から手動で hide）

[Answer]: A

### Q2: Planter のアーカイブと削除の役割分担

スキーマには `planters.status='archived'` と `planters.deleted_at` の両方が存在します。Admin UI ではどちらを主操作にしますか？

- A: 「アーカイブ」（status='archived'、フィード除外、URL 直叩きは閲覧可、復元可）と「削除」（deleted_at、完全に不可視）の 2 段階
- B: 「アーカイブ」だけ提供（復元可）、削除はメンテナンス用に DB 直叩きのみ
- C: 「削除」だけ提供（ソフトデリート、復元不可）、アーカイブは未使用

[Answer]: A

### Q3: Log 非表示機能の Admin 露出

スキーマには `logs.is_hidden`, `hidden_by` がすでにあります。Admin 画面に Log の非表示／復元 UI を含めますか？

- A: 含める（Planter 管理タブから配下 Log にドリルダウン → 個別 hide）
- B: 含めない（MVP は Planter 全体のアーカイブで対応、Log 単位は後回し）

[Answer]: B（Figma の admin ページに Log 管理画面が存在しないため整合）

### Q4: マスタデータ削除のルール

`seed_types` / `tags` を物理削除する操作を許可しますか？

- A: 物理削除あり（参照中の場合はエラー、参照ゼロのみ削除可）
- B: 物理削除なし（`is_active=false` で無効化のみ。新規投稿で選択不可だが既存データは保持）

[Answer]: B（補足: SeedType は **`description` のみ admin から編集可**。`slug` / `name` / `sort_order` は migration 管理。Tags は admin UI 自体を設けない）

### Q5: 監査ログ（admin の操作履歴）の保存

「誰が・いつ・誰／何に対して BAN／アーカイブ／マスタ変更したか」を残しますか？

- A: 専用テーブル `admin_audit_logs` を新規作成して記録
- B: 既存フィールド（`banned_at`, `hidden_by`, `hidden_at`）のみで運用、専用テーブルはフェーズ 2
- C: 構造化 JSON ログ（Cloud Logging）に出すだけで DB には保存しない

[Answer]: B

### Q6: Admin レイアウトの Right Sidebar

Figma の admin 画面には Right Sidebar がありません。実装方針は？

- A: AdminLayout は完全に独立（apps/web/app/admin/layout.tsx）。ヘッダーのみ共通、Sidebar とサイドバー右パネルは admin 専用に置き換え
- B: 既存の LayoutShell を流用しつつ、`useRightSidebar().setContent(null)` と Sidebar 切替で対応

[Answer]: A

### Q7: ダッシュボード統計の鮮度

統計カード（総ユーザー数 1,247 / 総 Planter 数 3,891 等）はどう取得しますか？

- A: ページロード時にリアルタイム集計クエリ（COUNT）— MVP では十分速い
- B: マテリアライズドビュー or キャッシュ（`admin_stats_snapshot` を定期更新）
- C: フェーズ 2 まで簡易実装（COUNT のみ）でよい → A と同じ

[Answer]: A

### Q8: 初期 admin ユーザーの作成方法

最初の admin はどう作りますか？

- A: 環境変数 `ADMIN_EMAILS` に列挙、初回ログイン時に `users.role='admin'` を自動セット
- B: DB マイグレーションで特定 email のユーザーを admin に昇格
- C: Supabase 管理画面から手動で `role='admin'` に UPDATE（運用ドキュメントに記載）

[Answer]: C

### Q9: タグ管理 UI の編集粒度

タグマスタは階層構造（category → 親タグ → 子タグ）で 6 カテゴリ × 多数。Admin 画面の操作粒度は？

- A: カテゴリ別の階層ツリーを表示し、ノード追加・編集・並び替え・有効化トグルが可能（フル機能）
- B: フラットなリスト編集（カテゴリ + 親タグはセレクタ、ツリービューなし）— シンプル実装
- C: MVP は閲覧のみ（マスタ追加は migration で対応、Admin UI は表示と is_active トグルのみ）
- D: Admin UI を設けない（タグマスタは migration / DB 直叩きで管理）

[Answer]: **D**（Admin UI 自体を作らない）

### Q10: Frontend ルート保護方針

`/admin` 配下にログイン済みの非 admin がアクセスした場合の挙動は？

- A: middleware（Next.js）でリダイレクト → `/`（403 ページに遷移）
- B: Server Component 側で `role` をチェックし `notFound()`（404 を返す＝admin 画面の存在を秘匿）
- C: Client 側で AdminGuard を使い、403 メッセージを表示

[Answer]: B

---

## Resolved Decisions

- [x] Q1 BAN 副作用範囲: A — 表示維持、本人ログイン＋投稿のみ不可
- [x] Q2 アーカイブ／削除の使い分け: A — アーカイブ（復元可）と削除（typed confirmation・ソフトデリート）の 2 段階
- [x] Q3 Log 非表示 Admin 機能の有無: B — 含めない（Figma に画面なし）
- [x] Q4 マスタ物理削除可否: B — `is_active` トグルのみ。SeedType 追加・slug/name/sort_order 編集は migration、Tags は admin UI そのものを設けない
- [x] Q5 監査ログ専用テーブルの導入: B — 専用テーブルなし、既存フィールド + Cloud Logging で運用
- [x] Q6 AdminLayout 独立 / 流用: A — 完全独立（`apps/web/app/admin/layout.tsx`）
- [x] Q7 統計鮮度: A — リアルタイム集計（COUNT）
- [x] Q8 初期 admin の作り方: C — Supabase 管理画面から手動 UPDATE（運用ドキュメントに記載）
- [x] Q9 タグ管理 UI 粒度: D — Admin UI を設けない（migration / DB 直叩きで管理）
- [x] Q10 `/admin` 非 admin アクセス時挙動: B — Server Component で `notFound()`（404 で存在を秘匿）
