# U3 Log & Score - Frontend Components

## 概要

U3 で実装・拡張するフロントエンドコンポーネント:
1. **PlanterDetail（拡張）** — Seed/Sprout 状態の詳細表示、スコア情報
2. **LogThread（新規）** — Log 一覧表示 + 投稿フォーム
3. **ScoreCard（拡張）** — 構造パーツ詳細の追加
4. **PlanterCard（拡張）** — Sprout 状態のバッジ表示対応

---

## FC-07: PlanterDetail（Seed/Sprout 状態）

### 現状（U2）

- Planter の基本情報（タイトル、本文、タグ、メタ情報）を表示
- Log 一覧は空のプレースホルダー
- Log 投稿バーは disabled 状態

### U3 拡張

```
+--Main Content Area------------------------------------------+
| [Sprout Badge] [投稿タイプ] · [Avatar] [Username] · [時間]   |
|                                                              |
| [タイトル]                                                    |
| [本文]                                                        |
|                                                              |
| [Tag] [Tag] [Tag]                                            |
|                                                              |
| ---- Logs セクション ----                                     |
|                                                              |
| [LogThread コンポーネント]                                     |
|   [Log 1] Avatar Username 時間                               |
|     本文テキスト...                                           |
|     [返信する]                                                |
|       [Reply 1-1] Avatar Username 時間                       |
|         返信テキスト...                                       |
|   [Log 2 - AI] Logo "AI アシスタント" 時間                    |
|     ファシリテート文...                                       |
|   [Log 3] Avatar Username 時間                               |
|     本文テキスト...                                           |
|   ...                                                        |
|   [もっと読み込む]（カーソルページネーション）                   |
|                                                              |
+-- Sticky Input Bar（画面下部固定）--------------------------+
| [Avatar] [Log を投稿...                          ] [送信]    |
+--------------------------------------------------------------+
```

### データ取得

1. **Planter 詳細**: `GET /api/v1/planters/{id}` — SSR（Server Component）
2. **Log 一覧**: `GET /api/v1/planters/{id}/logs` — CSR（Client Component、無限スクロール）
3. **スコア設定**: `GET /api/v1/settings/score` — SSR（bloom_threshold を取得）

### 状態管理

- Planter のスコア情報は Log 投稿後のレスポンスで更新（`LogCreateResponse.planter`）
- Right Sidebar の ScoreCard も同時に更新（RightSidebarContext 経由）

---

## FC-09: LogThread（新規）

### コンポーネント構造

```typescript
// components/log/LogThread.tsx
interface LogThreadProps {
  planterId: string
  planterStatus: string  // "seed" | "sprout" | "louge"
  onLogCreated: (response: LogCreateResponse) => void
}
```

### Log 一覧表示

```typescript
// components/log/LogItem.tsx
interface LogItemProps {
  log: LogWithReplies
  onReply: (parentLogId: string) => void
}
```

- トップレベル Log を古い順に表示
- 各 Log の下に返信（replies）をインデント表示
- AI 投稿（is_ai_generated=true）は通常 Log と同スタイル
  - アバター: Works Logue ロゴアイコン
  - ユーザー名: "AI アシスタント"

### 返信 UI

- 各トップレベル Log に「返信する」リンク
- クリックで返信フォームが展開（Log の直下にインライン表示）
- 返信の返信（ネスト2段）は不可

### 投稿フォーム（Sticky Input Bar）

```
+-- 画面下部固定 -------------------------------------------------+
| [ログインユーザーAvatar] [テキスト入力エリア          ] [送信 ->] |
+------------------------------------------------------------------+
```

- **位置**: 画面下部に固定（position: sticky、ChatGPT 風）
- **テキストエリア**: 1行表示、入力に応じて自動拡張（最大5行）
- **送信ボタン**: テキストが空の場合は disabled
- **認証チェック**: 未ログイン時は「ログインして参加する」ボタンに置換
- **Planter 状態チェック**: `status='louge'` の場合は非表示

### 無限スクロール

- 初回: 50件取得
- 「もっと読み込む」ボタンで追加取得（IntersectionObserver ではなく明示ボタン）
  - Log は古い順なので、上方向にスクロールで追加読み込みするとUXが複雑になるため
  - 初回50件で十分な場合が多い

### Log 投稿フロー

```
1. ユーザーがテキストを入力
2. 送信ボタンクリック
3. POST /api/v1/planters/{id}/logs
4. レスポンス即時受信（score_pending=true）:
   a. 新しい Log をリストの末尾に追加
   b. log_count, contributor_count, status を即時反映
   c. ScoreCard に「スコア計算中...」インジケーター表示
5. 入力欄をクリア
6. スコア polling 開始:
   a. 3秒後に GET /api/v1/planters/{id}/score
   b. score_pending=true なら 5秒後にリトライ（最大3回）
   c. score_pending=false になったら ScoreCard を更新、インジケーター消去
   d. 3回リトライしても pending の場合はインジケーター消去（次回ページ読み込みで反映）
```

---

## ScoreCard（拡張）

### 現状（U2）

```
+-- Right Sidebar --+
| 開花スコア         |
| [===] 25%         |  <- structure_fulfillment
| Log数: 3          |
| 貢献者数: 2       |
| 多様性: --        |
| 開花まで: 75%     |
+-------------------+
```

### U3 拡張（構造パーツ詳細追加）

```
+-- Right Sidebar -------------------+
| 開花スコア                          |
| [===========] 45%                  |  <- progress (総合)
|                                    |
| -- 構造パーツ --                    |
| [v] 状況 (Context)                 |  <- チェックマーク付き
| [v] 問題 (Problem)                 |
| [ ] 解決策 (Solution)              |  <- 未充足
| [ ] パターン名 (Name)              |  <- 未充足
|                                    |
| -- 統計 --                         |
| Log数: 8                           |
| 貢献者数: 4                        |
| 開花まで: あと55%                  |
+------------------------------------+
```

### Props

```typescript
interface ScoreCardProps {
  progress: number           // 0.0〜1.0
  structureFulfillment: number
  structureParts: {
    context: boolean
    problem: boolean
    solution: boolean
    name: boolean
  } | null
  logCount: number
  contributorCount: number
  bloomThreshold: number
  isLouge: boolean
  scorePending: boolean      // バックグラウンド計算中フラグ
}
```

### 表示ロジック

- **Louge 状態**: 開花済みの特別表示（「開花済み」バッジ、全パーツチェック済み）
- **Sprout 状態**: 進捗バー + 構造パーツチェックリスト + 統計
- **Seed 状態（Log 0件）**: 「最初の Log を投稿して育てましょう」メッセージ
- **スコア計算中** (`scorePending=true`): progress バー横に小さなスピナー + 「スコア計算中...」テキスト。計算完了で消去しアニメーション付きでスコア更新

---

## PlanterCard（U3 拡張）

### 変更点

- Sprout 状態の Planter にも正しいバッジ色を適用
- `status='sprout'` のバッジ: `bg-primary-light`・`text-primary`（Seed と同じスタイル）
- progress バーの表示を Planter の実際の progress 値に連動（U2 では静的だった可能性）

---

## AI アシスタントの表示仕様

| 項目 | 値 |
|---|---|
| 表示名 | "AI アシスタント" |
| アバター | Works Logue ロゴアイコン (`/img/works-logue-logo-icon.png`) |
| スタイル | 通常 Log と同じ（背景色・フォント等の区別なし） |
| user が null | `is_ai_generated=true` の場合、アバターとユーザー名をハードコード |

---

## API 呼び出しまとめ

| コンポーネント | エンドポイント | メソッド | タイミング |
|---|---|---|---|
| PlanterDetail | `/api/v1/planters/{id}` | GET | SSR（ページ読み込み） |
| LogThread | `/api/v1/planters/{id}/logs` | GET | CSR（初回 + ページネーション） |
| LogThread | `/api/v1/planters/{id}/logs` | POST | ユーザー操作（Log 投稿） |
| ScoreCard | `/api/v1/settings/score` | GET | SSR（bloom_threshold 取得） |
| ScoreCard | `/api/v1/planters/{id}/score` | GET | CSR（Log 投稿後の polling、3秒後 + 5秒後 + 10秒後） |
