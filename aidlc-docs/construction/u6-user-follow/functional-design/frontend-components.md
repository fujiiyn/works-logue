# U6 User & Follow — Frontend Components

Figma 参照: 公開プロフィール v2 (351:159) / 編集ページ (356:159)

**仕様変更（2026-04-18決定）:**
- 得意テーマ (`specialty_themes`) → 削除
- 居住地 (`location`) + SNSリンク (`social_links`) → 追加
- マイページ → 不要。公開プロフィールに貢献グラフ・編集ボタンを含める
- オンボーディング → アバター画像アップロード追加

## FC-12: UserProfilePage (`/user/[id]/page.tsx`)

### 構成

```
UserProfilePage (Server Component)
├── ProfileHeader
│   ├── CoverImage (カバー画像エリア)
│   ├── Avatar (88px, カバーに被せる)
│   ├── UserInfo (表示名, ヘッドライン, bio)
│   ├── FollowButton (Client Component)
│   ├── EditButton (自分のプロフィールのみ表示)
│   ├── TagPills (職種・業界・スキルタグ)
│   └── LocationAndLinks (居住地 + SNSリンクアイコン)
├── StatsRow
│   ├── StatCard (総合スコア)
│   ├── StatCard (Louge貢献)
│   ├── StatCard (フォロワー)
│   └── StatCard (フォロー中)
├── ContributionGraph (GitHub草風ヒートマップ, Client Component)
├── FeaturedContribution (注目の貢献カード)
├── ProfileTabs (Client Component)
│   ├── Tab: Seed一覧 → PlanterCard リスト
│   ├── Tab: Log一覧 → LogHistoryItem リスト
│   └── Tab: 参加Louge → PlanterCard リスト (Lougeのみ)
└── RightSidebar
    ├── BadgeSection (バッジ一覧)
    └── SimilarUsers (似た専門性のユーザー + フォローボタン)
```

### Props / API

| コンポーネント | データソース |
|---|---|
| ProfileHeader | `GET /api/v1/users/{id}` |
| StatsRow | 同上（stats フィールド） |
| FeaturedContribution | 同上（featured_contribution フィールド） |
| ProfileTabs - Seed | `GET /api/v1/users/{id}/planters?tab=seeds` |
| ProfileTabs - Log | `GET /api/v1/users/{id}/logs` |
| ProfileTabs - Louge | `GET /api/v1/users/{id}/planters?tab=louges` |

### FollowButton (Client Component)

| 状態 | 表示 | アクション |
|---|---|---|
| 未フォロー | 「フォロー」(primary塗り) | POST /users/{id}/follow |
| フォロー中 | 「フォロー中」(outline) | クリックで即時 DELETE（確認ダイアログなし、楽観更新） |
| 自分 | 非表示 | — |
| 未ログイン | 「フォロー」→ クリックでログイン誘導 | — |

### ProfileHeader アクション領域の排他表示（BR-N02）

ProfileHeader 右上のアクションスロットには **どちらか一方** のみ表示する。

| 閲覧者 | 表示 |
|---|---|
| 自分のプロフィール | 「編集」ボタン（`/profile/edit` への Link）のみ |
| 他人のプロフィール | FollowButton（フォロー/フォロー中）のみ |

実装: `FollowButton` は `isOwnProfile` で null を返し、`編集` Link は `isOwnProfile` 時のみレンダリング。

## FC-13: PlanterFollowButton (Client Component)

`apps/web/components/planter/PlanterFollowButton.tsx`

Seed/Louge 詳細画面のヘッダーに配置する Planter フォローボタン（BR-F06）。

### Props

```ts
interface Props {
  planterId: string;
  initialIsFollowing: boolean; // 詳細 API の is_following から
  size?: "sm" | "md"; // sm をメタ行に合わせて使用
}
```

### スタイル

- アウトライン: 透明背景 + teal ボーダー（`border-primary`）+ teal テキスト（`text-primary`）
- サイズ sm: `h-[22px] px-2 text-[10px] rounded`
- メタ情報行（投稿時刻の直後）に馴染むよう小型

### 状態と表示

| 状態 | 表示 | アクション |
|---|---|---|
| 未フォロー | 「+ フォロー」 | POST /planters/{id}/follow |
| フォロー中 | 「フォロー中」（薄い teal 背景） | クリックで即時 DELETE（確認ダイアログなし、楽観更新） |
| 未ログイン | 「+ フォロー」→ クリックで /login へ | — |

### 配置

- Seed/Sprout 詳細: stats 行で `[X logs] [Y contributors] [+ フォロー]` を等間隔（gap-3）で並べる
- Louge 詳細: 右サイドバー（ContributorsSidebar）下部の stats バーで `[X logs · Y contributors] [+ フォロー]` を等間隔（gap-3）で並べる

## FC-14: ユーザー名リンク化（BR-N01）

下記コンポーネントの投稿者表示部で `display_name` を `<Link href="/user/{user.id}">` でラップする。

| コンポーネント | 該当箇所 |
|---|---|
| PlanterCard | メタ行の投稿者名（カード全体リンクと両立するため overlay link 技法を使用） |
| planter-detail-client | 詳細ヘッダーの投稿者名 |
| LogItem | Log の投稿者名（`is_ai_generated=true` を除く） |
| ContributorsSidebar | 貢献者一覧の各エントリ（既存リンクを維持） |
| FollowListModal | 既存リンクを維持 |

### PlanterCard のネスト解決

カード全体が `<Link href="/p/{id}">` のため、内部にもう一つ Link を入れると anchor のネストになる。
overlay link パターン（`<article className="relative">` 内で背景に `absolute inset-0` の Link、ユーザー名 Link は `relative z-10`）で両立させる。

## ProfileEditPage (`/user/[id]/edit/page.tsx`)

### 構成

```
ProfileEditPage (Client Component)
├── LeftSidebar (ホーム, フォロー中, 注目, 探索)
├── MainContent
│   ├── Header ("< プロフィールに戻る" リンク)
│   ├── PageTitle ("プロフィールを編集")
│   ├── CoverImageEditor
│   │   ├── CoverPreview (現在のカバー画像)
│   │   └── ChangeButton ("カバー画像を変更")
│   ├── AvatarEditor
│   │   ├── AvatarPreview (現在のアバター)
│   │   └── ChangeButton ("アバターを変更")
│   ├── HeadlineInput (60文字制限カウンター付き)
│   ├── DisplayNameInput (必須)
│   ├── BioTextarea (200文字制限カウンター付き)
│   ├── TagEditSection (TagAccordionSelector 再利用)
│   ├── LocationInput (居住地、自由テキスト)
│   └── SocialLinksSection
│       ├── XInput (https://x.com/...)
│       ├── LinkedInInput (https://linkedin.com/in/...)
│       ├── WantedlyInput (https://wantedly.com/id/...)
│       └── WebsiteInput (https://...)
└── RightSidebar
    ├── ProfilePreview (ミニプレビューカード)
    ├── SaveButton → PATCH /users/me + 画像アップロード
    └── CancelButton → /user/{id} に戻る
```

### 画像アップロードフロー

```
1. ユーザーがファイル選択
2. クライアント側でファイルサイズ・形式チェック（即座にエラー表示）
3. 選択画像をプレビュー表示（FileReader API）
4. 保存ボタン押下時に POST /users/me/avatar or /cover
5. レスポンスの URL をプレビューに反映
```

### タグ編集UI

- 既存の TagAccordionSelector コンポーネントを再利用（オンボーディングで実装済み）
- 選択済みタグは pill 形式で表示、× で削除可能
- 「+ 追加」で アコーディオン展開

## フォロー中フィードタブ

### 既存サイドバー連携

- サイドバーの「フォロー中」ナビ項目 → `/?tab=following`
- 既存の PlanterFeed コンポーネントに `following` タブを追加
- 未ログイン時はログイン誘導表示

### データフロー

```
/?tab=following
→ PlanterFeed (tab="following")
→ GET /api/v1/planters?tab=following (認証ヘッダー付き)
→ PlanterCard リスト表示
```
