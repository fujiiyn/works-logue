# U2 Seed — Frontend Components

## 概要

U2 で実装するフロントエンドコンポーネント:
- **SeedForm** — Seed 投稿フォーム（`/seed/new`）
- **TagSelector** — タグ選択 UI（右サイドバー内、SeedForm と連携）
- **PlanterCard** — フィードカード（1枚）
- **PlanterFeed** — 新着フィード（タブ + カードリスト）
- **ProgressBar** — 開花進捗バー
- **PlanterDetail** — Planter 詳細ページ（`/p/[id]`、Seed 情報のみ）

Figma 参照: `fileKey: RKsHkKG2GfOlaVxRzY81TG`

---

## FC-08: SeedForm

**配置**: `apps/web/app/seed/new/page.tsx` + `apps/web/components/seed/SeedForm.tsx`
**Figma**: nodeId `78:6`（Seed投稿画面）
**種別**: Client Component

### レイアウト

メインエリアに配置。右サイドバーに TagSelector。

```
[ページタイトル: "新しいSeedを蒔く"]
[説明文]
[投稿タイプ選択: 8タイプのグリッド（2列x4行）]
[タイトル入力: text input]
[本文入力: textarea]
[キャンセル / Seedを蒔く ボタン]
```

### Props & State

```typescript
// SeedForm の内部 State
interface SeedFormState {
  seedTypeId: string | null      // 選択した投稿タイプ ID
  title: string                   // タイトル（max 200文字）
  body: string                    // 本文（max 10000文字）
  selectedTagIds: string[]        // 選択したタグ ID 配列
  isSubmitting: boolean           // 送信中フラグ
  errors: Record<string, string>  // フィールドごとのエラー
}
```

### 投稿タイプ選択 UI

- 8タイプを2列グリッドで表示（Figma 準拠）
- 各カードに `name` + `description` を表示
- 選択中: `bg-brand-light` + `border-brand-primary`
- 未選択: `bg-surface-card` + `border-border-default`
- 1つのみ選択可（ラジオボタン的挙動）

### バリデーション（クライアント側）

| フィールド | ルール | エラーメッセージ |
|---|---|---|
| seedTypeId | 必須 | 「投稿タイプを選択してください」 |
| title | 必須、1〜200文字 | 「タイトルを入力してください」/「200文字以内で入力してください」 |
| body | 必須、1〜10000文字 | 「本文を入力してください」/「10000文字以内で入力してください」 |

タグは任意のため、クライアント側バリデーションなし。

### API 連携

- **SeedType 取得**: ページロード時に `GET /api/v1/seed-types` を呼び出し
- **投稿**: `POST /api/v1/planters` に `{ title, body, seed_type_id, tag_ids }` を送信
- **成功時**: `router.push(/p/${planter.id})` で詳細ページへ遷移（Q3 回答: A）
- **エラー時**: サーバーエラーをフォーム上部にトーストまたはインラインで表示

### ユーザーインタラクション

1. SeedType 一覧をロード → グリッド表示
2. ユーザーがタイプを選択
3. タイトル・本文を入力
4. 右サイドバーで TagSelector からタグ選択
5. 「Seedを蒔く」クリック → バリデーション → API 送信
6. 成功 → `/p/{id}` へ遷移

---

## FC-10: TagSelector

**配置**: `apps/web/components/common/TagSelector.tsx`
**Figma**: nodeId `78:6` 内の右サイドバー "Tag Selection Card"
**種別**: Client Component

### レイアウト（Figma 準拠）

```
[タグ]（見出し）
[選択中]（ラベル）
[チップ: 人事・採用 x] [チップ: デジタルマーケティング x]  ← 選択済みタグ
[業界 | 職種 | 役割 | 状況 | スキル | ナレッジ]           ← カテゴリタブ
[ツリービュー]                                              ← 階層展開
  ▸ □ 経営・事業開発
  ▾ ■ コーポレート（管理部門）        ← indeterminate
    ▾ ☑ 人事・採用                     ← checked（子全選択）
        ☑ 採用（新卒/中途）            ← leaf checked
        ☑ 人材開発・研修              ← leaf checked
        ...
```

### Props

```typescript
interface TagSelectorProps {
  selectedTagIds: string[]
  onTagsChange: (tagIds: string[]) => void
}
```

### Internal State

```typescript
interface TagSelectorState {
  activeCategory: TagCategory  // 現在のタブ
  expandedNodeIds: Set<string> // 展開中のノード
  tagTree: TagTreeNode[]       // API から取得したツリー
  isLoading: boolean
}

type TagCategory = 'industry' | 'occupation' | 'role' | 'situation' | 'skill' | 'knowledge'
```

### ツリー操作

- **Chevron クリック**: ノードの展開/折りたたみをトグル
- **チェックボックス（リーフ）**: `selectedTagIds` にトグル追加/削除
- **チェックボックス（親）**: 全子リーフを一括トグル
  - 全子が選択済み → 全子を解除
  - 一部 or 未選択 → 全子を選択
- **親のチェック状態表示**:
  - 全子選択: checked (✓)
  - 一部選択: indeterminate (−)
  - 未選択: unchecked (□)
- **チップの x ボタン**: 該当タグを `selectedTagIds` から削除

### カテゴリタブ

- 6タブ: 業界 / 職種 / 役割 / 状況 / スキル / ナレッジ
- アクティブタブ: `bg-brand-primary` + `text-inverse`
- 非アクティブタブ: `text-secondary`
- タブ切り替え時にツリーを差し替え

### API 連携

- **初回ロード**: `GET /api/v1/tags` で全タグを取得し、カテゴリ別にキャッシュ
- または **タブ切り替え時**: `GET /api/v1/tags?category=occupation` でカテゴリ別取得（遅延ロード）
- 推奨: 初回に全取得（タグ数は有限のマスタデータ）

---

## FC-05: PlanterCard

**配置**: `apps/web/components/planter/PlanterCard.tsx`
**Figma**: nodeId `12:3`（Home 画面のカード）
**種別**: Server Component（リンク付き）

### レイアウト（Figma 準拠）

```
[Seed Badge] [投稿タイプ名] · [アバター] [ユーザー名] · [時間]
[タイトル]
[Tag] [Tag] [Tag]
[X logs]  [X contributors]              [====ProgressBar====]
```

### Props

```typescript
interface PlanterCardProps {
  planter: PlanterCardResponse
}
```

### 表示仕様

| 要素 | 仕様 |
|---|---|
| Stage Badge | status に応じた表示。U2 では `Seed` のみ。`bg-brand-light` + `text-brand-primary` |
| 投稿タイプ名 | `seed_type.name`（「悩み」「疑問」等） |
| アバター | `user.avatar_url`（なければデフォルトアバター） |
| ユーザー名 | `user.display_name` |
| 時間 | 相対時間表示（「3時間前」「2日前」等） |
| タイトル | `title`。1行で表示（overflow は ellipsis） |
| タグ | 最大3個表示 + 「+N」バッジ |
| メタ情報 | `log_count` logs / `contributor_count` contributors |
| ProgressBar | FC-11 を使用 |

### リンク

- カード全体が `/p/{planter.id}` へのリンク

---

## FC-06: PlanterFeed（新着タブのみ）

**配置**: `apps/web/components/planter/PlanterFeed.tsx`
**Figma**: nodeId `12:3`（Home 画面のメインエリア）
**種別**: Client Component（無限スクロール）

### レイアウト

```
[タブ: 新着 | 注目 | 開花済み]       ← U2 では新着のみアクティブ
[PlanterCard]
[PlanterCard]
[PlanterCard]
...
[もっと読み込む / 自動ロード]
```

### Props & State

```typescript
interface PlanterFeedState {
  planters: PlanterCardResponse[]
  nextCursor: string | null
  hasNext: boolean
  isLoading: boolean
  isLoadingMore: boolean
}
```

### タブ

- 3タブ表示: 新着 / 注目 / 開花済み
- U2 では **新着タブのみ機能する**
- 注目・開花済みタブはクリック可能だが「Coming Soon」表示（U5 で実装）

### ページネーション

- 初回ロード: `GET /api/v1/planters?limit=20`
- 追加ロード: `GET /api/v1/planters?limit=20&cursor=xxx`
- Intersection Observer で画面下部到達時に自動ロード
- `has_next=false` でロード終了

### 空状態

- Planter が0件の場合:「まだSeedが投稿されていません。最初のSeedを蒔いてみましょう。」+ 「Seedを投稿する」ボタン

---

## FC-11: ProgressBar

**配置**: `apps/web/components/planter/ProgressBar.tsx`
**Figma**: nodeId `12:3`（カード内のプログレスバー）
**種別**: Server Component

### Props

```typescript
interface ProgressBarProps {
  progress: number   // 0.0 〜 1.0
  status: string     // "seed" | "sprout" | "louge"
}
```

### 表示仕様

- 高さ: 3px
- 幅: 120px（カード内右寄せ）
- Track: `bg-brand-light`
- Fill:
  - `status='seed'` or `status='sprout'`: `bg-brand-primary/50`（半透明）
  - `status='louge'`: `bg-brand-primary`（100% 幅）
- Fill 幅: `progress * 100%`
- U2 時点では progress=0 なので fill なし

---

## PlanterDetail ページ（U2 スコープ）

**配置**: `apps/web/app/p/[id]/page.tsx`
**Figma**: nodeId `57:29`（Seed Detail 画面）
**種別**: Server Component（ページ）

### U2 実装範囲（Q4 回答: A）

Seed 情報のみ表示。Log 一覧・Log 投稿フォームは U3 で追加。

### レイアウト

```
[Stage Badge: Seed] [投稿タイプ名]
[タイトル]
[アバター] [ユーザー名] · [投稿日時]
[本文]
[タグ一覧]
[ProgressBar]
[log_count logs · contributor_count contributors]
```

### 右サイドバー

- Seed 詳細ページの右サイドバーにはスコア表示（memory 参照: `feedback_seed_detail_right_sidebar.md`）
- U2 時点では全て 0 の初期状態
  - Progress: 0%
  - Logs: 0
  - Contributors: 0
  - Status: Seed

### API 連携

- Server Component から `GET /api/v1/planters/{id}` を呼び出し
- 404 の場合は Next.js の `notFound()` を返す

---

## OnboardingPage

**配置**: `apps/web/app/onboarding/page.tsx`
**種別**: Client Component

### レイアウト

標準3カラムレイアウト内のメインエリアに表示。

```
[見出し: "プロフィールを設定しましょう"]
[説明文: あなたに合った Seed を見つけやすくするために...]

[表示名 *]（text input、プリフィル、必須）
[自己紹介]（textarea、任意）

[あなたの業界・職種・スキル]（ラベル）
[TagSelector: 全6カテゴリタブ]

[設定を完了する]（display_name 未入力時は disabled）
```

### State

```typescript
interface OnboardingState {
  displayName: string       // プリフィル: user.display_name
  bio: string
  selectedTagIds: string[]
  isSubmitting: boolean
  errors: Record<string, string>
}
```

### API 連携

- **ページロード時**: auth-context から `user` を取得。`display_name` をプリフィル
- **タグ取得**: `GET /api/v1/tags`（TagSelector が内部で取得）
- **送信**: `PATCH /api/v1/users/me` に `{ display_name, bio, tag_ids, complete_onboarding: true }` を送信
- **成功時**: `redirect` クエリパラメータの URL へ遷移（なければ `/`）

### バリデーション（クライアント側）

| フィールド | ルール | エラーメッセージ |
|---|---|---|
| displayName | 必須、1〜100文字 | 「表示名を入力してください」 |

### リダイレクト制御

- URL: `/onboarding?redirect=/seed/new`
- 完了後: `router.push(redirect || '/')`
- `redirect` が外部URL（`http://` 等）の場合は無視して `/` へ

---

## Auth Context 拡張（オンボーディングリダイレクト）

**配置**: `apps/web/contexts/auth-context.tsx`

### 追加仕様

- `AppUser` インターフェースに `onboarded_at: string | null` を追加
- useEffect でオンボーディングリダイレクト判定:

```typescript
useEffect(() => {
  if (user && !user.onboarded_at) {
    const path = window.location.pathname
    // 閲覧ページ・ログイン・オンボーディング自体はリダイレクトしない
    const allowedPaths = ['/', '/login', '/onboarding']
    const isViewPage = path.startsWith('/p/')
    if (!allowedPaths.includes(path) && !isViewPage) {
      router.push(`/onboarding?redirect=${encodeURIComponent(path)}`)
    }
  }
}, [user])
```

---

## FC-10: TagSelector（拡張）

### Props 拡張

```typescript
interface TagSelectorProps {
  selectedTagIds: string[]
  onTagsChange: (tagIds: string[]) => void
  categories?: TagCategory[]  // 追加: 表示するカテゴリを制限（デフォルト: 全6カテゴリ）
}
```

- オンボーディング・Seed 投稿ともに全6カテゴリを表示（`categories` 未指定 = デフォルト全表示）

---

## 通信方式まとめ

| コンポーネント | 方式 | 理由 |
|---|---|---|
| PlanterFeed（初回ロード） | Client Component → FastAPI | 無限スクロールのため Client 側で状態管理 |
| PlanterDetail（ページ） | Server Component → FastAPI | SEO・初期描画速度 |
| SeedForm（投稿） | Client Component → FastAPI | ユーザー操作・楽観的更新 |
| TagSelector（取得） | Client Component → FastAPI | インタラクティブなツリー操作 |
| SeedType（取得） | Client Component → FastAPI | SeedForm 内で使用 |
| OnboardingPage（更新） | Client Component → FastAPI | ユーザー操作・プロフィール設定 |
