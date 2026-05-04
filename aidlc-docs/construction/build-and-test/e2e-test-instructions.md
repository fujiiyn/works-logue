# End-to-End Test Instructions

apps/web/e2e/ に置かれた Playwright スペック実行手順。Next.js（Server Component 含む）と FastAPI を実通信させ、ブラウザ越しの主要フローを検証する。

## Prerequisites

- `apps/web` で `npm ci` 完了
- `npx playwright install` でブラウザバイナリをローカル取得（初回のみ）
- API（apps/api）と Web（apps/web）の両方が起動可能な状態
- テストアカウント 3 名がテスト DB に投入済み（`apps/api/scripts/seed_test_data.sql`）

---

## Spec ファイル

| ファイル | カバー範囲 | テスト数 |
|---|---|---|
| `apps/web/e2e/admin.spec.ts` | U7 Admin smoke（一覧表示・検索・フィルタ・ナビ。破壊操作なし） | 5 |
| `apps/web/e2e/user-profile.spec.ts` | U6 プロフィール表示・編集・Follow | 8 |

合計: **13 シナリオ**

> 核心フロー（Seed → Log → Louge）の E2E 自動化は MVP 範囲外。手動統合テストでカバー。

---

## Run E2E Tests

### 1. ローカル実行

```bash
cd apps/web
# API・Web 両方を別ターミナルで起動した状態で
npx playwright test
```

### 2. ヘッドフルモード（ブラウザを見ながら）

```bash
npx playwright test --headed
```

### 3. UI モード（インタラクティブ）

```bash
npx playwright test --ui
```

### 4. 単一スペック

```bash
npx playwright test e2e/admin.spec.ts
npx playwright test e2e/user-profile.spec.ts
```

### 5. 単一テストケース

```bash
npx playwright test -g "admin can list users"
```

---

## E2E テスト方針

- **破壊操作（実 BAN・実削除）は行わない**: 本番テストデータの汚染を防ぐため、smoke レベルに留める
- **網羅は API テスト（pytest）でカバー**: U7 Admin の 11 エンドポイントは pytest 57 件で検証済み
- **data-testid をセレクタに使う**: クラス名や DOM 構造の変化に強くするため、UI 主要要素には `data-testid` を付与
- **自動 admin 昇格はしない**: admin スペックは「手動で role='admin' に昇格済みアカウント」を前提。Playwright は role 変更しない

---

## Expected Result

```
Running 13 tests using 1 worker
  ✓ admin.spec.ts (5)
  ✓ user-profile.spec.ts (8)

13 passed (XXs)
```

---

## CI への組み込み

**現状: CI に E2E は含まれていない。**

CI（`.github/workflows/ci.yml`）は lint + build + pytest のみで、Playwright は走らせていない。Cloud Run 上の本番に対しては手動 E2E もしくはローカルで実行する。

将来 E2E を CI に組み込む場合は：
1. PostgreSQL service コンテナを起動
2. `supabase db push` で migration 適用
3. `npx playwright install --with-deps`
4. API・Web を background 起動
5. `npx playwright test`
の順。MVP 範囲外。

---

## Troubleshooting

### `Error: page.goto: net::ERR_CONNECTION_REFUSED`
- API or Web が起動していない。`uvicorn app.main:app --port 8000` と `npm run dev` を確認

### `Error: Test timeout of 30000ms exceeded`
- Server Component の SSR が遅い、または Supabase 通信遅延。`playwright.config.ts` で timeout を延長

### `expect(locator).toBeVisible() failed`
- `data-testid` が変更されている。各 spec のセレクタと `components/admin/*` の testid を突き合わせる

### admin スペックが 404 で落ちる
- 使用アカウントが admin に昇格していない。`docs/operations.md` の SQL で role='admin' に更新する必要がある
