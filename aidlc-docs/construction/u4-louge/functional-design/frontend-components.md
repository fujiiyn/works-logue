# U4 Louge - Frontend Components

## 概要

U4 で実装・拡張するフロントエンドコンポーネント:
1. **PlanterDetail（Louge 状態拡張）** - 記事表示 + Seed 折りたたみ + 開花ポーリング
2. **LougeArticle（新規）** - Markdown 記事のレンダリング
3. **ContributorsSidebar（新規）** - 右サイドバーの貢献者一覧
4. **PlanterCard（拡張）** - Louge バッジ表示の確認

---

## FC-07: PlanterDetail（Louge 状態の拡張）

### 現状（U3）

- `status == "seed"` or `"sprout"` のみ対応
- Seed 本文 + LogThread + ScoreCard（右サイドバー）を表示
- 画面下部に Log 投稿バー（Sticky Input Bar）

### U4 拡張: Louge 状態の表示

**Figma 参照**: nodeId `213:10`（Louge Detail）

```
+--Main Content Area------------------------------------------+
| [Louge Badge] [投稿タイプ] · [Avatar] [Username] · [時間]    |
|                                                              |
| [タイトル]                                                    |
|                                                              |
| ---- 元の Seed ----                                          |
| [▶ 元の Seed を表示]  ← 折りたたみ（デフォルト: 閉じた状態） |
|   展開時:                                                     |
|   [本文テキスト...]                                           |
|   [Tag] [Tag] [Tag]                                          |
|                                                              |
| ---- Louge 記事 ----                                         |
| [LougeArticle コンポーネント]                                 |
|   # パターン名                                               |
|   ## 状況（Context）                                          |
|   ...                                                        |
|   ## 問題（Problem）                                          |
|   ...                                                        |
|   ## 解決策（Solution）                                       |
|   ...                                                        |
|   ## 反論・例外（Counterarguments）                            |
|   ...                                                        |
|   ---                                                        |
|   ## 出典                                                     |
|   [1] @田中 - 「引用スニペット...」                            |
|   [2] @佐藤 - 「引用スニペット...」                            |
|                                                              |
| ---- Logs セクション ----                                     |
| [LogThread コンポーネント]（既存、読み取り専用）               |
|                                                              |
+--------------------------------------------------------------+
  ※ Log 投稿バー（Sticky Input Bar）は非表示
```

### 状態分岐ロジック

```typescript
// PlanterDetail 内の表示切替
if (planter.status === "louge") {
  if (planter.bloom_pending) {
    // 開花処理中: BloomPendingView を表示
  } else {
    // 開花完了: LougeView を表示
  }
} else {
  // seed / sprout: 既存の SeedSproutView を表示
}
```

### bloom_pending 時の表示

```
+--Main Content Area------------------------------------------+
| [Louge Badge] [投稿タイプ] · [Avatar] [Username] · [時間]    |
|                                                              |
| [タイトル]                                                    |
|                                                              |
|         +--開花アニメーション--+                               |
|         |   [蓮の花アイコン]    |                              |
|         |   ✿ 開花中...        |                              |
|         |   記事を生成して      |                              |
|         |   います              |                              |
|         +---------------------+                               |
|                                                              |
+--------------------------------------------------------------+
```

- 蓮の花アイコン（ロゴモチーフ）を使ったローディングアニメーション
- ポーリングで `bloom_pending=false` を検知したら自動で記事表示に切替
- 60秒タイムアウト後: 「記事生成に時間がかかっています。しばらく後にもう一度アクセスしてください」

---

## LougeArticle（新規コンポーネント）

### 責務

Markdown 形式の Louge 記事をレンダリングする。

### Props

```typescript
interface LougeArticleProps {
  content: string;        // Markdown テキスト
  generatedAt: string;    // ISO 8601 日時
  onCopy: () => void;     // コピーボタンのコールバック
}
```

### 機能

- Markdown → HTML レンダリング（react-markdown 等を使用）
- コードブロック・テーブル・リスト等の基本的な Markdown 要素に対応
- 「Louge をコピー」ボタン: Markdown テキストをクリップボードにコピー
- コピー成功時にトースト通知（「クリップボードにコピーしました」）
- 生成日時の表示（「2026年4月15日に開花」）

### スタイリング

- 記事本文: `text-primary-dark` (`#1F3833`)
- 見出し: `text-primary-dark`、下線付き
- 引用ブロック: 左ボーダー `border-primary` (`#29736B`)
- 出典セクション: `text-sm text-muted`、番号部分は `font-semibold`
- コピーボタン: アウトラインスタイル、Lucide `Copy` アイコン

---

## ContributorsSidebar（新規コンポーネント）

### 責務

開花した Planter の右サイドバーに貢献者一覧を表示。

### Figma 参照

nodeId `213:10` の右パネル部分。

### 構造

```
+--Right Sidebar----------------------------------------------+
| 貢献者                                                       |
|                                                              |
| [Avatar] [田中太郎]              +0.85                       |
|          IT・SaaS / 事業開発                                  |
|          3 logs                                              |
|                                                              |
| [Avatar] [佐藤花子]     🌱 Seed  +1.0                        |
|          メーカー / 人事                                      |
|          Seed 投稿者                                         |
|                                                              |
| [Avatar] [鈴木一郎]              +0.4                        |
|          金融 / 営業                                         |
|          2 logs                                              |
|                                                              |
+-- Louge をコピー [Copy icon] ---+                            |
+--------------------------------------------------------------+
```

### Props

```typescript
interface ContributorsSidebarProps {
  contributors: Contributor[];
  onCopyLouge: () => void;
}

interface Contributor {
  userId: string;
  displayName: string;
  avatarUrl: string | null;
  insightScoreEarned: number;
  logCount: number;
  isSeedAuthor: boolean;
}
```

### データ取得

- `GET /api/v1/planters/{id}/contributors` から取得
- 貢献スコア降順でソート
- Seed 投稿者にはバッジ（🌱 アイコンではなく Lucide の `Sprout` アイコン）を付与

---

## PlanterCard（U4 拡張）

### 変更点

- `status == "louge"` の場合:
  - バッジ: `Louge`（`bg-primary` / `text-white`）
  - Progress Bar: 100% 表示（`bg-primary` フル幅）
  - Log 投稿バー: 非表示

既存の PlanterCard は `louge` バッジの表示ロジックを既に持っている（U2 で実装済み）。
Progress Bar が 100% で表示されることを確認するのみ。

---

## 右サイドバーの状態別表示

| Planter 状態 | 右サイドバーの内容 |
|---|---|
| `seed` / `sprout` | ScoreCard（構造パーツ + 進捗バー + 統計） |
| `louge`（bloom_pending） | ScoreCard（progress=100%）+ 「開花中...」 |
| `louge`（完了） | ContributorsSidebar（貢献者一覧 + コピーボタン） |

---

## データフロー

### SSR（Server Component）
- Planter 詳細取得: `GET /api/v1/planters/{id}`
- 初期レンダリングで `status` に応じた表示を決定

### CSR（Client Component）
- **bloom_pending 時のポーリング**: `GET /api/v1/planters/{id}` を定期チェック
  - 間隔: 3秒 → 5秒 → 10秒
  - `bloom_pending=false` になったら記事表示に切替
  - 60秒タイムアウト
- **貢献者一覧取得**: `GET /api/v1/planters/{id}/contributors`（Louge 状態時のみ）
- **Log 一覧**: 既存の LogThread（読み取り専用、投稿バー非表示）
