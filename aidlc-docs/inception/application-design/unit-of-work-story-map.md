# Unit of Work Story Map — Works Logue MVP

User Stories ステージはスキップしたため、機能要件（FR）をユニットにマッピングする。

---

## マッピング概要

| 機能要件 | 内容 | ユニット |
|---|---|---|
| FR-01 | 認証・ユーザー管理 | U1 Foundation |
| FR-02 | ユーザープロフィール | U6 User & Follow |
| FR-03 | Seed 投稿 | U2 Seed |
| FR-04 | Log 投稿 | U3 Log & Score |
| FR-05 | Louge スコアリング（条件A/B） | U3 Log & Score |
| FR-05b | UI レイアウト構造 | U1 Foundation（レイアウト）+ U2 Seed（カード・フィード） |
| FR-06 | Louge 開花（AI記事生成） | U4 Louge |
| FR-07 | インサイトスコア | U4 Louge |
| FR-08 | フォロー機能 | U6 User & Follow |
| FR-09 | フィード・検索・タグ | U2 Seed（新着タブ）+ U5 Feed & Search（注目/開花済み/検索） |

---

## ユニット別の機能要件マッピング

### U1: Foundation

| 機能要件 | 対象範囲 |
|---|---|
| FR-01 | メール+パスワード認証、Google OAuth（Supabase Auth） |
| FR-05b | 3カラムレイアウト（Header, Sidebar, RightSidebar）、About カード |
| NFR-01 | プロジェクト初期化（Next.js, FastAPI, Supabase 接続） |
| NFR-02 | Dockerfile, 環境変数設定 |
| DB全量 | 全テーブルのマイグレーション + SQLAlchemy モデル |
| (共通) | NotificationRepository（通知イベント記録の器） |

### U2: Seed

| 機能要件 | 対象範囲 |
|---|---|
| FR-03 | Seed 投稿フォーム（タイプ選択・タイトル・本文・タグ）、投稿 API |
| FR-05b | PlanterCard（バッジ・タグ・メタ・ProgressBar）、PlanterFeed（新着タブ） |
| FR-09（部分） | 新着タブのフィード表示、タグ選択 UI |

### U3: Log & Score

| 機能要件 | 対象範囲 |
|---|---|
| FR-04 | Log 投稿（スレッド形式・ネスト1段返信）、投稿 API |
| FR-05 | ScoreEngine（条件A 構造判定 + 条件B 成熟度スコア）、ScorePipeline、AIFacilitator |
| FR-05b（部分） | PlanterDetail ページ（Seed/Sprout 状態の表示）、ProgressBar 連動 |

### U4: Louge

| 機能要件 | 対象範囲 |
|---|---|
| FR-06 | LougeGenerator（Vertex AI 記事生成）、開花フロー、Louge コピー機能 |
| FR-07 | InsightScoreCalculator（貢献度スコア算出） |
| FR-05b（部分） | PlanterDetail ページ（Louge 状態: 記事表示 + Seed 折りたたみ + 貢献者一覧） |

### U5: Feed & Search

| 機能要件 | 対象範囲 |
|---|---|
| FR-09（残り） | 注目タブ（FeedRanker）、開花済みタブ、探索画面（タグフィルタ + キーワード検索 + 状態フィルタ） |
| FR-05b（部分） | planter_views による閲覧数集計 |

### U6: User & Follow

| 機能要件 | 対象範囲 |
|---|---|
| FR-02 | プロフィール表示・編集（表示名・自己紹介・アバター・タグ・インサイトスコア・投稿履歴） |
| FR-08 | Planter フォロー、ユーザーフォロー、フォロー中フィード、自動フォロー（通知イベント記録は U1 の NotificationRepository を利用） |

---

## カバレッジ検証

全機能要件（FR-01 ~ FR-09, FR-05b）が少なくとも1つのユニットに割り当てられていることを確認済み。

| チェック項目 | 結果 |
|---|---|
| FR-01 ~ FR-09 全てにユニットが割り当てられているか | OK |
| 1つのFRが複数ユニットにまたがる場合、境界が明確か | OK（FR-05b, FR-09 は対象範囲を明記） |
| 全コンポーネント（FC/BC）がユニットに含まれているか | OK |
| DB スキーマが U1 で全量カバーされているか | OK |
