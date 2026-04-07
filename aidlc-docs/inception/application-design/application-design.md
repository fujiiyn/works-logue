# Application Design — Works Logue MVP

統合設計書。各設計ドキュメントの概要と設計判断の根拠をまとめる。

---

## 設計判断サマリ

| 判断項目 | 決定 | 根拠 |
|---|---|---|
| API 設計方針 | RESTful リソースベース | `/api/planters`, `/api/planters/{id}/logs` 等。リソース構造が明確でドメインモデルと一致 |
| Frontend-Backend 通信 | 混合方式 | ページロード: Server Components → FastAPI、ユーザー操作: Client → FastAPI 直接 |
| DB 接続 | SQLAlchemy メイン + Auth/Storage のみ supabase-py | ORM のメリット（型安全・マイグレーション連携）を享受しつつ、Auth/Storage は公式 SDK を使用 |
| 認証検証 | FastAPI 側で JWT 検証 | FastAPI がゲートキーパー。Next.js はトークン中継のみ |
| バックグラウンドジョブ | MVP: BackgroundTasks → スケール時: Cloud Tasks/Pub/Sub | 初期はシンプルに。サービス層のインターフェースを変えずに移行可能な設計 |
| 注目ランキング | 複合スコア（閲覧数 + Log 投稿速度 + 構造充足率） | 単一指標では偏りが出るため複合化 |
| 検索 | タグ + キーワード全文検索 + Planter 状態フィルタ | Supabase PostgreSQL の full-text search を活用。3条件 AND 結合 |
| URL 設計 | `/p/{id}` | 状態に依存しない短い URL。Planter 概念を隠蔽しつつ一意 |
| Figma デザイン | 全画面を Figma で事前作成 | 実装前にデザインを確定。Figma MCP で参照しながら実装 |

---

## アーキテクチャ概要

### レイヤード構成

```
+--Frontend (Next.js App Router)----------------------------------+
| Layout Shell | Pages | Components                               |
| Server Components (SSR) + Client Components (インタラクション)    |
+--+--------------------------------------------------------------+
   | HTTP (JSON)
   v
+--Backend (FastAPI)----------------------------------------------+
| Router Layer     | エンドポイント定義、リクエスト検証、レスポンス整形  |
| Service Layer    | ビジネスロジック、オーケストレーション              |
| Repository Layer | データアクセス抽象化                               |
| Infrastructure   | 外部サービス統合（Vertex AI, Supabase）            |
+--+--------------------------------------------------------------+
   | SQLAlchemy / supabase-py
   v
+--Data Layer-----------------------------------------------------+
| Supabase PostgreSQL | Auth | Storage                             |
+-------------------------------------------------------------+
```

### コンポーネント数

| レイヤー | コンポーネント数 |
|---|---|
| Frontend Components | 14（FC-01 ~ FC-14） |
| Backend Routers | 6（BC-01 ~ BC-06） |
| Backend Repositories | 6（BC-07 ~ BC-10, BC-20 FollowRepo, BC-21 NotifRepo） |
| Backend Services | 5（BC-11 ~ BC-15） |
| Backend Orchestration | 1（BC-22 ScorePipeline） |
| Backend Infrastructure | 4（BC-16 ~ BC-19） |
| Database | 2（Models + Migrations） |

---

## コアフロー

### 1. Seed 投稿

1. ユーザーが SeedForm で入力・送信（Client → FastAPI 直接）
2. `POST /api/planters` → PlanterRouter → PlanterRepository.create()
3. タグ紐付け、投稿者の自動フォロー
4. Planter(status=seed) を返却

### 2. Log 投稿 + スコア再計算

1. ユーザーが LogThread で Log 投稿（Client → FastAPI 直接）
2. `POST /api/planters/{id}/logs` → LogRouter → LogRepository.create()
3. 即座にレスポンス返却
4. BackgroundTasks でスコアパイプライン実行:
   - ScoreEngine が条件A（構造充足率）を軽量チェック
   - 条件A 充足 + 最低参加ライン超過時のみ条件B（成熟度4観点）を本格スコアリング
   - 条件B 突破 → LougeGenerator.bloom()（開花）
   - 条件B 不足 → AIFacilitator.facilitate()（AI ファシリテート）

### 3. Louge 開花

1. LougeGenerator が Vertex AI で記事生成
2. Planter の状態を `louge` に更新、記事内容を保存
3. InsightScoreCalculator が各 Log 投稿者の貢献度を算出・反映
4. 通知イベントを DB に記録

### 4. フィード表示

1. Server Component が `GET /api/planters?tab=xxx` で取得
2. 新着: 時系列順、注目: FeedRanker の複合スコア順、開花済み: Louge のみ
3. PlanterCard でカード描画

---

## 詳細設計ドキュメント

| ドキュメント | 内容 |
|---|---|
| [components.md](./components.md) | 全コンポーネントの定義・責務・配置パス |
| [component-methods.md](./component-methods.md) | メソッドシグネチャ・I/O 型定義 |
| [services.md](./services.md) | サービス定義・オーケストレーションパターン・通信方式 |
| [component-dependency.md](./component-dependency.md) | 依存関係マトリクス・データフロー・URL 設計 |

---

## 設計上の注意事項

1. **ポリシー外部化**: ScoreEngine の閾値・パーツ定義は設定ファイル/環境変数で管理。コード変更なしでチューニング可能にする
2. **スコアスナップショット**: Log 投稿のたびにスコアを `louge_score_snapshots` に記録。分析・改善の根拠データ
3. **ソフトデリート**: planters / logs / users は物理削除しない。`deleted_at` カラムで管理
4. **通知イベント先行記録**: 通知送信はフェーズ2だが、イベント（開花・状態変化等）は MVP から DB に記録
5. **Figma 参照実装**: 全画面のデザインを Figma で事前作成し、Figma MCP で参照しながら実装する
