# U5 Feed & Search — Frontend Components

## FC-06: PlanterFeed 拡張

### 変更内容
- 「人気」「開花済み」タブの coming soon 表示を削除し、実機能に置き換え
- タブ切り替え時にフィード再取得（タブ名を API パラメータとして送信）
- API エンドポイント: `GET /api/v1/planters?tab=recent|trending|bloomed`

### タブごとの挙動
| タブ | API パラメータ | 並び順 |
|---|---|---|
| 新着 | `tab=recent` | created_at DESC |
| 人気 | `tab=trending` | trending_score DESC |
| 開花済み | `tab=bloomed` | louge_generated_at DESC |

### UI 変更
- タブの `disabled` 属性と coming soon ラベルを削除
- 各タブ独立の状態管理（planters, cursor, hasMore）
- タブ切り替え時にリスト・カーソルをリセットして再取得

## FC-13: SearchExplore（新規ページ）

### 場所
`apps/web/app/explore/page.tsx`

### 構成
```
SearchExplore
├── SearchBar（キーワード入力、debounce 300ms）
├── FilterBar
│   ├── TagFilter（TagAccordionSelector 再利用、複数選択）
│   └── StatusFilter（seed / sprout / louge チップ選択）
└── SearchResults（PlanterCard リスト、無限スクロール）
```

### API
`GET /api/v1/search?keyword=...&tag_ids=...&status=...&cursor=...&limit=20`

### 動作
- 初期表示: フィルタなし、新着順で全 Planter 表示
- キーワード入力: 300ms debounce 後に自動検索
- タグ/状態フィルタ: 変更時に即座に再検索
- 検索結果 0 件時: 空状態メッセージ表示

## ナビゲーション

### Sidebar
既存の Sidebar に `/explore` リンクを追加（Compass アイコン、Lucide `Search`）
