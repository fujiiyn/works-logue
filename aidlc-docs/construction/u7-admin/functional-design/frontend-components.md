# U7 Admin — Frontend Components

Figma 参照: page `admin`（nodeId `420:159`）。実装時は **Figma を単一の真実源** として `get_design_context` で各 nodeId を取得してから書く。

| nodeId | フレーム |
|---|---|
| 422:159 | Admin / Layout — desktop shell |
| 424:159 | Admin / Dashboard |
| 426:159 | Admin / Users — list |
| 427:159 / 427:400 | Admin / Users — BAN / BAN 解除 ダイアログ |
| 428:159 | Admin / Planters — list |
| 432:159 / 432:435 / 432:713 | Admin / Planters — Archive / Restore / Delete (typed) ダイアログ |
| 433:159 | Admin / SeedTypes — list |
| 464:2 | Admin / SeedTypes — Edit description ダイアログ |
| 434:159 / 434:391 / 434:678 / 434:949 | Empty / Loading state |

## 既存ファイルへの差分（U7 で同時に入れる）

| ファイル | 変更 | 理由 |
|---|---|---|
| `apps/web/contexts/auth-context.tsx` | `AppUser` interface に `is_banned: boolean` と `deleted_at: string \| null` を追加 | BR-A02b の `BannedBanner` と FC-A01 AdminGuard で必要 |
| `apps/api/app/routers/users.py` の `GET /users/me` レスポンス | `is_banned`, `deleted_at` を含める（既存スキーマで対応可） | 同上 |
| `apps/web/components/layout/banned-banner.tsx`（新規） | BR-A02b のバナー実装 | BAN ユーザー UX |
| `apps/web/app/layout.tsx` | `<BannedBanner />` をヘッダー直下に挿入 | 全ページ共通 |
| `apps/web/lib/auth-server.ts`（新規） | Server Component 用 `getCurrentUser()` ヘルパ | FC-A01 AdminGuard が依存 |
| `apps/web/package.json` | `@supabase/ssr` を追加（未導入の場合） | Server 認証ヘルパ実装に必要 |
| `docs/operations.md`（新規） | admin 昇格・降格・緊急 admin 無効化の SQL を記載（BR-A21） | 運用手順の単一の真実源 |
| `apps/api/app/schemas/users.py` の `UserMeResponse` | `is_banned: bool` / `deleted_at: datetime \| None` を追加 | AuthContext と Server `getCurrentUser` で使用（business-logic-model.md §8） |

## ルーティング

```
apps/web/app/admin/
├── layout.tsx              ← AdminLayout (RightSidebar 抑止、独立シェル)
├── page.tsx                ← AdminDashboard (/admin)
├── users/
│   └── page.tsx            ← UserManagementPage (/admin/users)
├── planters/
│   └── page.tsx            ← PlanterManagementPage (/admin/planters)
└── seed-types/
    └── page.tsx            ← SeedTypeAdminPage (/admin/seed-types)
```

## FC-A01: AdminGuard（Server）

`apps/web/app/admin/layout.tsx` の Server Component として実装。

### 前提: Server 用 `getCurrentUser` ヘルパが U7 で新規作成される

現状の `apps/web` には Client Component の `AuthContext` (`apps/web/contexts/auth-context.tsx`) しか存在しない。Server Component から認証ユーザーを取得する手段がないため、U7 で **`apps/web/lib/auth-server.ts`** に Server 用 `getCurrentUser()` を新設する。

```ts
// apps/web/lib/auth-server.ts (新規)
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr"; // 必要なら新規依存追加

export interface ServerUser {
  id: string;
  display_name: string;
  role: string;
  is_banned: boolean;
  deleted_at: string | null;
  // ... AdminGuard で必要な最小フィールド
}

export async function getCurrentUser(): Promise<ServerUser | null> {
  // 1. Next.js cookies() から sb-access-token を取得
  // 2. Supabase ssr クライアントでセッション検証
  // 3. 検証済 access_token を Authorization ヘッダーに乗せて
  //    バックエンド GET /api/v1/users/me を呼び、ServerUser を返す
  // 失敗時は null を返す（呼び出し側で notFound() にハンドリング）
}
```

実装上の注意:
- `@supabase/ssr` が未導入なら U7 で `package.json` に追加
- バックエンド `GET /users/me` のレスポンスに `is_banned` / `deleted_at` を含める修正も同時に必要（業務ロジック側 §1b 相当）
- `AuthContext` 側との二重 fetch を避けるため、Server で取得した user を Client Provider に渡すパターンも検討の余地はあるが、MVP では各々独立 fetch でよい

### AdminGuard 実装

```tsx
// apps/web/app/admin/layout.tsx
import { notFound } from "next/navigation";
import { getCurrentUser } from "@/lib/auth-server";
import { AdminShell } from "@/components/admin/admin-shell";

export default async function AdminLayout({ children }) {
  const user = await getCurrentUser();
  if (!user || user.role !== 'admin' || user.is_banned || user.deleted_at) {
    notFound();  // BR-A01 / Q10=B: 404 を返して存在を秘匿
  }
  return <AdminShell user={user}>{children}</AdminShell>;
}
```

- Q10=B により `notFound()`（403 ページ・リダイレクトは使わない）
- `useRightSidebar` は **一切呼ばない**（Q6=A に従い、Right Sidebar コンテナ自体を AdminShell でレンダリングしない）

## FC-A02: AdminShell（Client / Layout）

```
AdminShell
├── AdminHeader (top bar)
│   ├── ロゴ + "Admin Panel" ラベル
│   ├── 表示中ユーザー: avatar + display_name + "Admin"
│   ├── 「公開サイトに戻る」リンク (/)
│   └── ログアウトボタン (Supabase signOut → /login にリダイレクト、useAuth の signOut を再利用)
├── AdminSidebar (ダーク緑、固定 240px、Figma `422:159` 準拠)
│   ├── NavItem ダッシュボード (/admin)
│   ├── NavItem ユーザー管理 (/admin/users)
│   ├── NavItem Planter管理 (/admin/planters)
│   └── NavItem SeedType管理 (/admin/seed-types)
└── MainContent (children, クリーム背景)
```

スタイル要点:
- ダーク緑: `bg-primary-dark text-primary-light`（`#1F3833` ベース、Figma `422:159`）
- アクティブ NavItem は左に teal アクセント線（`#00B4CC` 4px）
- Sidebar 上部に蓮ロゴ（小型）

## FC-A03: AdminDashboard (`/admin`)

Figma `424:159`。

```
AdminDashboard
├── PageTitle "ダッシュボード"
├── StatsGrid (4 列)
│   ├── StatCard 総ユーザー数
│   ├── StatCard 総 Planter 数
│   ├── StatCard 本日の新規 Planter
│   └── StatCard 開花待ち Sprout
└── (将来用の余白。MVP では 4 カードのみ)
```

データソース: `GET /api/v1/admin/stats`

| StatCard | フィールド | アイコン (Lucide) |
|---|---|---|
| 総ユーザー数 | total_users | Users |
| 総 Planter 数 | total_planters | Sprout |
| 本日の新規 Planter | new_planters_today | TrendingUp |
| 開花待ち Sprout | pending_louge_count | Flower2 |

Server Component で取得して props として渡す（リロード時に最新化）。

## FC-A04: UserManagementPage (`/admin/users`)

Figma `426:159` / `427:159` / `427:400` / `434:159` (empty) / `434:391` (loading)。

```
UserManagementPage (Client)
├── PageTitle "ユーザー管理"
├── ToolbarRow
│   ├── SearchInput (display_name のみ。email 検索は Supabase 管理画面で対応)
│   └── FilterChipGroup [ すべて | 正常 | BAN中 ]
├── UserTable
│   ├── Column: ユーザー (avatar + display_name。email は表示しない)
│   ├── Column: ロール (Admin / User バッジ)
│   ├── Column: ステータス (正常 / BAN中 バッジ)
│   ├── Column: 投稿数 (planter_count + log_count)
│   ├── Column: 登録日
│   └── Column: アクション
│       ├── 自分の行 → 鍵アイコン (操作不可、BR-A06)
│       ├── role='admin' → 鍵アイコン (操作不可、BR-A07)
│       ├── 正常 → [BAN] ボタン (赤系 outline)
│       └── BAN中 → [BAN解除] ボタン (緑系 outline)
├── Pagination
└── Dialogs:
    ├── BanUserDialog (Figma 427:159)
    │   ├── Title: "ユーザーを BAN しますか？"
    │   ├── User の avatar + display_name + role
    │   ├── ReasonTextarea (任意、500 字)
    │   └── Actions: [キャンセル] [BAN する] (赤)
    └── UnbanUserDialog (Figma 427:400)
        ├── Title: "BAN を解除しますか？"
        ├── User 表示 (avatar + display_name)
        └── Actions: [キャンセル] [BAN を解除] (緑)
```

データソース:
- 一覧: `GET /api/v1/admin/users?q=...&status=...&page=...&per_page=50`
- BAN: `POST /api/v1/admin/users/{id}/ban` body `{ reason }`
- 解除: `POST /api/v1/admin/users/{id}/unban`

UX:
- BAN / 解除はダイアログ確認必須（誤操作防止）
- 成功時: 行を楽観更新 → API レスポンスで上書き
- エラー時: トースト表示、行は元に戻す
- Empty state: Figma `434:159` を参照（"ユーザーが見つかりません"）
- Loading state: Figma `434:391` を参照（テーブル行のスケルトン）

### `is_self` 判定の責務分担

`AdminUserItem.is_self` は **API 側で付与する**（business-logic-model.md §2a Step 8）。Client Component の UserManagementPage は単に `item.is_self` を読むだけで「自分の行 = 鍵アイコン」表示を切り替えられる。Client 側で `current_user.id` を fetch する必要はない。

これにより:
- AdminLayout（Server Component）が解決した admin user を Client に明示的に props で渡す必要がない
- 将来 BR-A07 のような追加ルール（admin 同士操作禁止）も `is_admin: bool` のような追加フラグを API レスポンスに足す形で同じパターンに乗せられる

## FC-A05: PlanterManagementPage (`/admin/planters`)

Figma `428:159` / `432:159` / `432:435` / `432:713` / `434:678`（empty）/ `434:949`（loading）。

```
PlanterManagementPage (Client)
├── PageTitle "Planter 管理"
├── ToolbarRow
│   ├── SearchInput (title 部分一致)
│   └── FilterChipGroup [ すべて | Seed | Sprout | Louge | アーカイブ | 削除済み ]
│                       ※「すべて」= フィードに出ているもの (= seed/sprout/louge)。archived/削除済みは含まない (BR-A09b)
├── PlanterTable
│   ├── Column: タイトル (title + seed_type_name)
│   ├── Column: 投稿者 (avatar + display_name)
│   ├── Column: 状態バッジ (Seed/Sprout/Louge/アーカイブ/削除)
│   ├── Column: Logs (log_count + contributor_count)
│   ├── Column: 更新日
│   └── Column: アクション
│       ├── 通常 (seed/sprout/louge) → [アーカイブ] [削除] ボタン
│       ├── archived → [復元] [削除] ボタン
│       └── deleted → アイコン表示 ("削除済み")、操作不可
├── Pagination
└── Dialogs:
    ├── ArchivePlanterDialog (Figma 432:159)
    │   ├── Title "この Planter をアーカイブしますか？"
    │   ├── Planter title + author
    │   └── Actions [キャンセル] [アーカイブ] (グレー)
    ├── RestorePlanterDialog (Figma 432:435)
    │   ├── Title "アーカイブから復元しますか？"
    │   ├── 補足: "復元後の状態は Seed になります" (BR-A10)
    │   └── Actions [キャンセル] [復元] (緑)
    └── DeletePlanterDialog (Figma 432:713) — typed confirmation
        ├── Title "この Planter を削除しますか？"
        ├── 警告文 (赤): "この操作は取り消せません"
        ├── Planter title (太字)
        ├── Input: "確認のため上のタイトルを入力してください"
        ├── 入力 = title でなければ [削除] ボタン disabled
        └── Actions [キャンセル] [削除] (赤、disabled gating)
```

データソース:
- 一覧: `GET /api/v1/admin/planters?q=...&status=...&page=...`
- アーカイブ: `POST /api/v1/admin/planters/{id}/archive`
- 復元: `POST /api/v1/admin/planters/{id}/restore`
- 削除: `DELETE /api/v1/admin/planters/{id}` body `{ confirm_title }`

UX:
- 削除ダイアログの typed confirmation は **クライアント・サーバー両方で検証**（BR-A12）
- 成功時: テーブル行は次ステータスに更新、削除時は行を消す（フィルタが「削除済み」のときは残す）
- エラー時: トースト表示

## FC-A06: SeedTypeAdminPage (`/admin/seed-types`)

Figma `433:159` / `464:2`（編集モーダル）。

```
SeedTypeAdminPage (Client)
├── PageTitle "SeedType 管理"
├── 補足テキスト: "新規追加・並び替え・名称変更は migration で行います" (BR-A15)
├── ToolbarRow
│   └── FilterChipGroup [ すべて | 公開中 | 非公開 ]
├── SeedTypeTable
│   ├── Column: 並び順 (sort_order, 読み取り専用)
│   ├── Column: 名称 (name, 読み取り専用)
│   ├── Column: slug (読み取り専用、薄字)
│   ├── Column: 説明 (description, 1 行 truncate)
│   ├── Column: 公開状態 (Switch: is_active トグル)
│   └── Column: アクション ([説明を編集] ボタン)
└── EditDescriptionDialog (Figma 464:2)
    ├── Title "{name} の説明を編集"
    ├── Read-only display: name / slug
    ├── Textarea: description (1〜1000 字、文字数カウンター)
    └── Actions [キャンセル] [保存] (primary)
```

データソース:
- 一覧: `GET /api/v1/admin/seed-types?status=...`
- 説明更新: `PATCH /api/v1/admin/seed-types/{id}` body `{ description }`
- is_active トグル: `POST /api/v1/admin/seed-types/{id}/toggle-active`

UX:
- is_active トグルは即時 API 呼び出し（楽観更新）
- 説明編集はモーダルで一括保存
- name / slug / sort_order は **input を一切置かない**（Q4=B）

## 共通 UI コンポーネント（既存 / 新規）

| コンポーネント | 出所 | 用途 |
|---|---|---|
| `Button` | 既存 | 全アクション |
| `Input` / `Textarea` | 既存 | 検索・編集 |
| `Switch` | 新規（Radix or 自作） | SeedType の is_active |
| `Dialog` | 既存 | 全モーダル |
| `Badge` | 既存（u6 で利用） | ロール・ステータス表示 |
| `Avatar` | 既存 | ユーザー一覧 |
| `Pagination` | 新規（admin 専用に簡易実装可） | テーブル用 |
| `FilterChipGroup` | 新規 | ToolbarRow 共通 |

## 状態管理

- 各ページは Client Component（フィルタ・ダイアログ状態のため）
- 一覧データは `useEffect` ベースの fetch + `useState`（MVP では SWR / React Query を導入しない）
- 楽観更新パターンを採用（U6 のフォローボタン同様）
- ダイアログは React state で開閉、ESC / 背景クリックで閉じる

## アクセシビリティ

- すべてのアクションボタンに aria-label
- ダイアログは focus trap（Radix Dialog がデフォルト対応）
- typed confirmation の input は aria-describedby で警告文と紐づける

## レスポンシブ

- AdminLayout は **デスクトップ専用**（min-width: 1024px 推奨）
- モバイル幅では「デスクトップでアクセスしてください」メッセージのみ表示（Figma に mobile レイアウトが存在しないため、MVP では割り切り）
