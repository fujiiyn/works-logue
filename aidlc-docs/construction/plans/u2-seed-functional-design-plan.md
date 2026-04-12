# U2 Seed — Functional Design Plan

## 計画概要

U2 Seed は Seed 投稿と基本フィード（新着タブ）を実装するユニット。ユーザーが最初に体験するコアフロー。

**スコープ**:
- Backend: PlanterRouter（CRUD + 新着フィード）、PlanterRepository、TagRepository
- Frontend: SeedForm、TagSelector、PlanterCard、PlanterFeed（新着タブのみ）、ProgressBar

**依存（U1 Foundation から提供済み）**:
- DB スキーマ全量（planters, tags, planter_tags, seed_types）
- 認証（get_current_user, get_optional_user）
- レイアウト（LayoutShell, Header, Sidebar, RightSidebar）
- API クライアント（lib/api-client.ts）

---

## 実行ステップ

### Phase 1: ドメインエンティティ定義

- [x] 1.1: Planter エンティティの詳細仕様（状態遷移ルール・バリデーション・レスポンス形式）
- [x] 1.2: SeedType エンティティの利用仕様（マスタ取得・投稿時の紐付け）
- [x] 1.3: Tag エンティティの階層構造仕様（カテゴリ別取得・Planter への紐付けルール）
- [x] 1.4: PlanterTag 関連テーブルの操作仕様

### Phase 2: ビジネスロジック

- [x] 2.1: Seed 投稿フロー定義（バリデーション → Planter 作成 → タグ紐付け → 自動フォロー → レスポンス）
- [x] 2.2: Planter 取得フロー定義（単一取得・フィード取得・ソフトデリート除外）
- [x] 2.3: 新着フィード取得ロジック（ページネーション・ソート・フィルタ条件）
- [x] 2.4: SeedType 一覧取得ロジック（アクティブなもののみ、sort_order 順）
- [x] 2.5: タグ一覧取得ロジック（カテゴリ別階層構造・アクティブのみ・is_leaf フィルタ）

### Phase 3: ビジネスルール

- [x] 3.1: Seed 投稿のバリデーションルール（タイトル長・本文長・タグ上限・必須項目）
- [x] 3.2: Seed 投稿の権限ルール（認証必須・BAN ユーザー禁止）
- [x] 3.3: フィード閲覧の権限ルール（非認証でも閲覧可・ただし一部データ制限）
- [x] 3.4: Planter の初期状態ルール（status='seed', progress=0, log_count=0）

### Phase 4: フロントエンドコンポーネント

- [x] 4.1: SeedForm コンポーネント定義（Props・State・バリデーション・API 連携）
- [x] 4.2: TagSelector コンポーネント定義（階層展開 UI・選択状態管理・カテゴリ表示）
- [x] 4.3: PlanterCard コンポーネント定義（Props・表示要素・リンク先）
- [x] 4.4: PlanterFeed コンポーネント定義（新着タブ・ページネーション・空状態）
- [x] 4.5: ProgressBar コンポーネント定義（条件A/B 表示ロジック・スタイル）

### Phase 5: API エンドポイント定義

- [x] 5.1: POST /api/v1/planters（Seed 投稿）のリクエスト/レスポンス仕様
- [x] 5.2: GET /api/v1/planters（フィード取得）のクエリパラメータ・レスポンス仕様
- [x] 5.3: GET /api/v1/planters/{id}（Planter 詳細取得）のレスポンス仕様
- [x] 5.4: GET /api/v1/seed-types（SeedType 一覧）のレスポンス仕様
- [x] 5.5: GET /api/v1/tags（タグ一覧）のクエリパラメータ・レスポンス仕様

---

## 質問

### Q1: タグ選択の上限

Seed 投稿時に選択できるタグの上限数はいくつにしますか？

- A) カテゴリごとに最大3個（業界3 + 職種3 + スキル3 = 最大9個）
- B) カテゴリ問わず合計5個まで
- C) カテゴリ問わず合計10個まで
- D) 上限なし

[Answer]:D

### Q2: フィードのページネーション方式

新着フィードのページネーションはどちらにしますか？

- A) オフセットベース（?page=2&per_page=20）- シンプル、MVPに適切
- B) カーソルベース（?cursor=xxx&limit=20）- 大規模データに適切だが実装が複雑

[Answer]:B

### Q3: Seed 投稿後のリダイレクト先

Seed 投稿成功後、ユーザーをどこへ遷移させますか？

- A) 投稿した Planter の詳細ページ（`/p/{id}`）
- B) ホームフィードに戻る（`/`）
- C) 投稿完了メッセージ表示後にホームへ

[Answer]:A

### Q4: Planter 詳細ページの実装範囲

U2 での Planter 詳細ページ（`/p/{id}`）の実装範囲はどこまでにしますか？U3 で Log 機能を実装するため、段階的に拡充される前提です。

- A) Seed 情報のみ表示（タイトル・本文・タグ・投稿者情報）。Log 一覧は U3 で追加
- B) Seed 情報 + Log 一覧の枠（空の状態 UI）まで。Log 投稿フォームは U3 で追加
- C) U2 では Planter 詳細ページを作らない。フィードカードのみ

[Answer]:A

### Q5: タグ選択 UI のレイアウト

TagSelector の UI パターンはどちらにしますか？

- A) カテゴリ（業界/職種/スキル等）をタブで切り替え、その中で階層展開
- B) 全カテゴリを縦に並べ、各カテゴリを折りたたみパネルで階層展開
- C) 検索ボックス + サジェスト形式（タイプして候補表示、カテゴリはバッジで区別）

[Answer]:A
