# U1 Foundation — Functional Design Plan

## 計画概要

U1 Foundation は全ユニット共通の基盤。DB スキーマ全量・認証・レイアウト Shell・外部サービスクライアントを定義する。

---

## 実行ステップ

### Phase 1: ドメインエンティティ（DB スキーマ全量）

- [x] 1.1: `users` テーブル定義（カラム・型・制約・インデックス）
- [x] 1.2: `planters` テーブル定義（状態遷移・louge_content・parent_planter_id）
- [x] 1.3: `logs` テーブル定義（parent_log_id・is_ai_generated）
- [x] 1.4: `tags` テーブル + 中間テーブル定義（planter_tags・user_tags）
- [x] 1.5: `follows` テーブル定義（planter_follows・user_follows を分離）
- [x] 1.6: `notifications` テーブル定義（イベント型・FK）
- [x] 1.7: `planter_views` テーブル定義（閲覧記録）
- [x] 1.8: `louge_score_snapshots` テーブル定義（スコア履歴）
- [x] 1.9: `insight_score_events` テーブル定義（貢献度イベント）
- [x] 1.10: テーブル間リレーション図の作成

### Phase 2: ビジネスルール（U1 スコープ）

- [x] 2.1: 認証フロー定義（JWT 検証・セッション管理・非認証アクセスの扱い）
- [x] 2.2: ユーザー初回ログイン時の自動レコード作成ルール
- [x] 2.3: ソフトデリートポリシー（deleted_at の扱い・クエリフィルタ）

### Phase 3: フロントエンドコンポーネント（U1 スコープ）

- [x] 3.1: LayoutShell 構造定義（3カラム・レスポンシブ方針）
- [x] 3.2: Header コンポーネント定義（認証状態に応じた表示切替）
- [x] 3.3: Sidebar コンポーネント定義（ナビ項目・アクティブ状態）
- [x] 3.4: RightSidebar コンポーネント定義（About カード）
- [x] 3.5: AuthProvider 定義（Supabase Auth セッション管理）

### Phase 4: インフラストラクチャコンポーネント（U1 スコープ）

- [x] 4.1: Database 接続設定（SQLAlchemy AsyncSession・接続プール）
- [x] 4.2: SupabaseAuthClient 定義（JWT 公開鍵取得・検証）
- [x] 4.3: SupabaseStorageClient 定義（アバター画像操作）
- [x] 4.4: VertexAIClient 定義（API 抽象化・リトライ）
- [x] 4.5: AuthMiddleware 定義（FastAPI Dependency）

### Phase 5: 検証

- [x] 5.1: 全テーブルの FK 整合性チェック
- [x] 5.2: U2〜U6 の依存要件との適合確認

---

## 質問

### Q1: タグデータの初期投入方針

`docs/tags.md` に定義された業界・職種・スキルタグ（数百件）をどのタイミングで DB に投入しますか？

- A) マイグレーションの seed データとして初期投入（推奨：タグは固定マスタに近い）
- B) 管理画面から手動投入（フェーズ2以降）
- C) アプリ起動時に自動同期

[Answer]:A

### Q2: レスポンシブ対応の範囲

3カラムレイアウトのレスポンシブ対応はどこまで必要ですか？

- A) デスクトップのみ（MVP では PC ブラウザを想定）
- B) タブレット+デスクトップ（768px 以上、サイドバー折りたたみ）
- C) フルレスポンシブ（モバイル含む、ハンバーガーメニュー等）

[Answer]:C

### Q3: Supabase プロジェクトの環境分離

開発環境と本番環境で Supabase プロジェクトを分けますか？

- A) 1プロジェクトで開発（MVP 初期は分離不要）
- B) 開発用・本番用の2プロジェクトを最初から作成

[Answer]:B

### Q4: Louge 記事の保存形式

`planters.louge_content` カラムのデータ形式は？

- A) Markdown テキスト（シンプル、フロントで描画）
- B) 構造化 JSON（セクション・引用元 Log ID 等をメタデータとして保持）
- C) HTML（AI が生成した最終形をそのまま保存）

[Answer]:A
