# U1 Foundation — Frontend Components

## 概要

U1 で実装するフロントエンドコンポーネントの詳細設計。3カラムレイアウト + 認証基盤。

---

## FC-01: LayoutShell

**種別**: Server Component（`app/layout.tsx`）

### 構造

```
<html>
  <body>
    <AuthProvider>
      <Header />
      <div class="layout-container">
        <Sidebar />
        <main>{children}</main>
        <RightSidebar />
      </div>
    </AuthProvider>
  </body>
</html>
```

### レスポンシブ方針（フルレスポンシブ）

| ブレークポイント | レイアウト |
|---|---|
| >= 1280px (xl) | 3カラム（Sidebar 固定 + Main + RightSidebar 固定） |
| 768px - 1279px (md-lg) | 2カラム（Sidebar 折りたたみ + Main）。RightSidebar は非表示 |
| < 768px (sm) | 1カラム。Sidebar はハンバーガーメニューから展開するドロワー。RightSidebar 非表示 |

### Tailwind 設計

- Sidebar 幅: `w-60`（240px）
- RightSidebar 幅: `w-72`（288px）
- Main: `flex-1 min-w-0`
- Container: `max-w-[1440px] mx-auto`

---

## FC-02: Header

**種別**: Client Component（認証状態で表示切替）

### Props

なし（AuthProvider のコンテキストから認証状態を取得）

### 表示要素

| 位置 | 要素 | 条件 |
|---|---|---|
| 左 | 蓮の花アイコン + "Works Logue" テキスト | 常時 |
| 右 | ~~通知ベル~~ | MVP では非表示（フェーズ2） |
| 右 | ログインボタン | 非ログイン時 |
| 右 | ユーザーアバター + ドロップダウン | ログイン時 |
| 右 | "+ Seed" ボタン（CTA） | 常時（非ログイン時はクリックでログインへ） |

### モバイル対応

- `< 768px`: ハンバーガーメニューボタン（Lucide: `Menu`）を左端に追加
- ロゴテキスト "Works Logue" を非表示、アイコンのみ

### ユーザーインタラクション

| アクション | 動作 |
|---|---|
| ロゴクリック | `/` へ遷移 |
| ~~ベルクリック~~ | ~~MVP では非表示~~ |
| ログインボタン | `/login` へ遷移 |
| "+ Seed" ボタン | `/seed/new` へ遷移（非ログイン時は `/login?redirect=/seed/new`） |
| アバタークリック | ドロップダウン（プロフィール / ログアウト） |
| ハンバーガー | Sidebar ドロワーを開閉 |

---

## FC-03: Sidebar

**種別**: Client Component（アクティブ状態の管理 + モバイルドロワー）

### ナビ項目

| ラベル | アイコン（Lucide） | パス | 認証要否 |
|---|---|---|---|
| ホーム | `Home` | `/` | 不要 |
| フォロー中 | `Users` | `/?tab=following` | 必要 |
| 注目 | `TrendingUp` | `/?tab=trending` | 不要 |
| 探索 | `Search` | `/explore` | 不要 |

### 状態管理

- 現在のパス（`usePathname`）に基づきアクティブ項目をハイライト
- アクティブ: `bg-primary-light/20 text-primary font-semibold`
- ホバー: `hover:bg-primary-light/10`

### モバイルドロワー

- `< 768px`: `fixed inset-y-0 left-0 z-50` + 背景オーバーレイ
- 開閉は Header のハンバーガーメニューボタンでトリガー
- ドロワー外クリックまたはナビ項目クリックで閉じる

---

## FC-04: RightSidebar

**種別**: Server Component

### 表示コンテキスト

| ページ | 表示内容 |
|---|---|
| ホーム (`/`) | About Works Logue カード |
| Planter 詳細 (louge 状態) | 貢献者一覧 + スコア（U4 で実装） |
| Planter 詳細 (seed/sprout) | Planter 統計・開花進捗（U3 で実装） |
| その他 | About Works Logue カード（デフォルト） |

### About Works Logue カード（U1 で実装）

```
+-- About Works Logue ----------------+
| [蓮の花アイコン]                      |
|                                      |
| ビジネスの知恵を共創する              |
| プラットフォーム                      |
|                                      |
| 現場のリアルな悩み（Seed）に           |
| みんなで知恵（Log）を集め、            |
| AIがナレッジ（Louge）を開花させます。   |
|                                      |
| Seeds: XX  Louges: XX               |
| Contributors: XX                     |
|                                      |
| [Seed を投稿する] (CTA button)       |
+--------------------------------------+
```

Stats はデータベースから集計（Server Component で fetch）。

### レスポンシブ

- `< 1280px`: 非表示（`hidden xl:block`）

---

## FC-14: AuthProvider

**種別**: Client Component（React Context）

### Context Value

```typescript
interface AuthContext {
  user: User | null;           // 現在のログインユーザー
  session: Session | null;     // Supabase セッション
  isLoading: boolean;          // 初期化中フラグ
  signIn: (provider: 'google' | 'email', credentials?) => Promise<void>;
  signOut: () => Promise<void>;
}
```

### 初期化フロー

1. マウント時に `supabase.auth.getSession()` でセッション復元
2. セッション存在時: JWT を FastAPI に送信してユーザー情報取得
3. `supabase.auth.onAuthStateChange()` でセッション変更を監視
4. ログイン/ログアウト時にコンテキストを更新

### API クライアント統合

- `lib/api-client.ts` で Authorization ヘッダーに JWT を自動付与
- セッション切れ時: 自動リフレッシュ（Supabase SDK が処理）
- リフレッシュ失敗時: ログアウト状態に戻す

---

## ログインページ（`/login`）

U1 の認証基盤として最低限のログインページを含む。

### 表示要素

- Works Logue ロゴ + サービス名
- "Google でログイン" ボタン（Supabase Auth OAuth）
- メール + パスワードフォーム（Supabase Auth email）
- "アカウント作成" リンク → サインアップフォーム表示切替

### リダイレクト

- `?redirect=` パラメータがある場合、ログイン後にそのパスへ遷移
- なければ `/` へ遷移

---

## 横断的デザインルール（全ユニット共通）

### カード Meta 行の表示ルール（FC-05 PlanterCard に適用）

| Planter 状態 | 投稿者名 | 表示例 |
|---|---|---|
| Seed / Sprout | 表示する | `Sprout · 悩み · HR_Tanaka · 2h` |
| Louge | **表示しない**（AI生成のため） | `Louge · シェア · 3d` |

---

## デザイントークン（Tailwind カスタム設定）

Figma design-system ページ (nodeId: 95:34) から実測。

```
colors:
  # Primary
  primary:         '#29736B'  (ボタン・アクティブ状態・CTA)
  primary-dark:    '#1F3833'  (テキスト — 見出し・本文)
  primary-light-bg:'#E0F0ED'  (アクティブナビ背景・バッジ背景)
  accent:          '#00B4CC'  (ロゴ蓮の花・ブランドアクセント)

  # Background & Surface
  bg:              '#F7F5ED'  (ページ背景)
  bg-card:         '#FBF9F5'  (ヘッダー・サイドバー・カード背景)
  border:          '#E5E3DB'  (ボーダー・区切り線)

  # Text
  text-secondary:  '#596B66'  (サブテキスト・タグテキスト)
  text-muted:      '#99998F'  (タイムスタンプ・メタ情報)
  text-sage:       '#A6B89E'  (セパレーター・プレースホルダー)
  white:           '#FFFFFF'  (Lougeバッジテキスト・CTAテキスト)

fontFamily:
  sans: ['Inter', 'Noto Sans JP', 'sans-serif']

borderRadius:
  xs: '2px'   (プログレスバー)
  sm: '4px'   (タグ・バッジ)
  md: '6px'   (ボタン・ナビ項目)
  lg: '10px'  (カード・About Card)

fontSize:
  display:    '28px / Semi Bold'  (Louge記事タイトル・大見出し)
  heading-xl: '24px / Semi Bold'  (ページ見出し・セクションタイトル)
  heading-l:  '18px / Medium'     (カードタイトル・投稿タイトル)
  heading-m:  '15px / Semi Bold'  (About Cardタイトル・セクション見出し)
  body-m:     '13px / Medium'     (ナビゲーション・ボタンラベル・本文)
  body-s:     '12px / Medium'     (メタ情報・ユーザー名・統計テキスト)
  caption:    '11px / Medium'     (バッジ・タグ・ラベル)

icons:
  library: lucide-react
  size: 20px
  strokeWidth: 1.5
```
