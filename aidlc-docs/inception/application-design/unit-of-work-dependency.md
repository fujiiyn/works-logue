# Unit of Work Dependency — Works Logue MVP

## 依存関係マトリクス

行が依存元、列が依存先。`x` は直接依存を示す。

| 依存元 / 依存先 | U1 Foundation | U2 Seed | U3 Log&Score | U4 Louge | U5 Feed&Search | U6 User&Follow |
|---|---|---|---|---|---|---|
| **U1 Foundation** | - | | | | | |
| **U2 Seed** | x | - | | | | |
| **U3 Log & Score** | x | x | - | | | |
| **U4 Louge** | x | | x | - | | |
| **U5 Feed & Search** | x | x | | | - | |
| **U6 User & Follow** | x | x | | | | - |

---

## 依存関係の詳細

### U1 Foundation → (なし)
基盤ユニット。外部依存なし。

### U2 Seed → U1
- DB スキーマ（planters, tags, planter_tags テーブル）
- 認証（AuthMiddleware, AuthProvider）
- レイアウト（LayoutShell, Header, Sidebar）

### U3 Log & Score → U1, U2
- U1: VertexAIClient（AI スコアリング）、DB（logs, louge_score_snapshots テーブル）
- U2: PlanterRepository（Planter 状態更新）、PlanterCard（ProgressBar 連動）

### U4 Louge → U1, U3
- U1: VertexAIClient（AI 記事生成）、NotificationRepository
- U3: ScorePipeline（開花トリガー連携）、ScoreEngine（条件判定結果の受け渡し）

### U5 Feed & Search → U1, U2
- U1: DB（planter_views テーブル）
- U2: PlanterRepository（フィードクエリ拡張）、PlanterFeed（タブ追加）

### U6 User & Follow → U1, U2
- U1: DB（users, follows テーブル）、SupabaseStorageClient（アバター）
- U2: PlanterCard（フォロー中フィード表示に再利用）

---

## 実装順序（クリティカルパス）

```
U1 Foundation
  |
  +---> U2 Seed
  |       |
  |       +---> U3 Log & Score
  |       |       |
  |       |       +---> U4 Louge
  |       |
  |       +---> U5 Feed & Search
  |       |
  |       +---> U6 User & Follow
```

**クリティカルパス**: U1 → U2 → U3 → U4

U5 と U6 は U3/U4 に依存しないため、U3 完了後に U4 と並行で開発可能。ただし一人開発のため順次実行を推奨。

---

## 共有リソース

| リソース | 提供元 | 利用先 |
|---|---|---|
| DB スキーマ全量 | U1 | 全ユニット |
| AuthMiddleware / AuthProvider | U1 | 全ユニット |
| VertexAIClient | U1 | U3, U4 |
| PlanterRepository | U2 | U3, U5 |
| PlanterCard / PlanterFeed | U2 | U5, U6 |
| ScorePipeline | U3 | U4 |
| NotificationRepository | U1 | U4, U6 |
| LayoutShell | U1 | 全ユニット |
