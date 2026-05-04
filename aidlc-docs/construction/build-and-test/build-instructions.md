# Build Instructions

Works Logue（apps/api・apps/web）のローカル / CI / 本番ビルド手順を集約する。

## Prerequisites

| 項目 | 値 |
|---|---|
| OS | Windows 11（開発機） / Ubuntu 24.04（CI / Cloud Run） |
| Python | 3.12（apps/api） |
| Node.js | 20 LTS（apps/web） |
| Docker | 27.x 以上（Cloud Run イメージ用） |
| gcloud CLI | 最新版（CD 用） |
| Supabase CLI | 1.x 以上（migration 適用） |

### 必須 Environment Variables

#### apps/api（FastAPI）
- `DATABASE_URL` — `postgresql+asyncpg://...`（Supabase の direct connection）
- `SUPABASE_URL` — Supabase プロジェクト URL
- `SUPABASE_PUBLISHABLE_KEY` — クライアント用 anon key
- `SUPABASE_SERVICE_ROLE_KEY` — service role key（管理操作）
- `CORS_ORIGINS` — 許可フロント Origin（カンマ区切り）

#### apps/web（Next.js）
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_API_URL` — Cloud Run の API URL

> **CI ビルドではプレースホルダー値（`https://placeholder.supabase.co` 等）を使用。本番値は Cloud Run の `--set-env-vars` 経由で注入する。**

---

## Build Steps

### 1. 依存関係のインストール

```bash
# API
cd apps/api
pip install -e ".[dev]"

# Web
cd apps/web
npm ci
```

### 2. データベースマイグレーション（初回 / スキーマ変更時のみ）

```bash
cd supabase
supabase db push
# または migrations/ 配下を直接 psql で適用
```

マイグレーションは `00001_create_tables.sql` から `00008_u6_user_follow.sql` まで 8 本（U7 Admin は既存の `role` / `is_banned` / `banned_at` / `ban_reason` / `deleted_at` を流用するため追加 migration なし）。

### 3. ローカルビルド

```bash
# API（ビルドステップなし、起動確認のみ）
cd apps/api
uvicorn app.main:app --reload --port 8000

# Web
cd apps/web
npm run build
```

`npm run build` は `next build` を実行し、`.next/` 配下にビルド成果物を生成する。CI と同等の検証になる。

### 4. Docker イメージビルド（本番相当）

```bash
# API イメージ
docker build -f infra/api/Dockerfile -t works-logue-api:local .

# Web イメージ（NEXT_PUBLIC_* は build-arg で渡す）
docker build -f infra/web/Dockerfile \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL \
  --build-arg NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=$SUPABASE_PUBLISHABLE_KEY \
  --build-arg NEXT_PUBLIC_API_URL=$API_URL \
  -t works-logue-web:local .
```

### 5. ビルド成果物

| 成果物 | パス | 用途 |
|---|---|---|
| API egg-info | `apps/api/works_logue_api.egg-info/` | editable install マーカー |
| Web build | `apps/web/.next/` | Next.js プロダクションビルド |
| API Docker image | `asia-northeast1-docker.pkg.dev/.../works-logue/api:<sha>` | Cloud Run（works-logue-api） |
| Web Docker image | `asia-northeast1-docker.pkg.dev/.../works-logue/web:<sha>` | Cloud Run（works-logue-web） |

### 6. Build 成功の判定

- **API**: `pip install` がエラー無く完了し、`uvicorn` がポート 8000 で listen できる
- **Web**: `npm run build` が exit code 0 で完了し、`.next/` 以下に成果物が生成される
- **Docker**: 両 Dockerfile が `docker build` で成功し、コンテナ起動でヘルスチェック通過

### 許容される警告

- Next.js の `metadata` 関連 deprecation 警告（Next 15 の段階では非ブロッキング）
- Pydantic v2 の `Config` 旧スタイル警告（依存ライブラリ起因のため対象外）

---

## CI（GitHub Actions）

`.github/workflows/ci.yml` が以下のジョブを並列実行する：

| ジョブ | 条件 | コマンド |
|---|---|---|
| api-lint | apps/api/ 変更時 or PR | `ruff check . && ruff format --check .` |
| api-test | apps/api/ 変更時 or PR | `pytest --tb=short -q` |
| web-lint | apps/web/ 変更時 or PR | `npm run lint` |
| web-build | apps/web/ 変更時 or PR | `npm run build`（NEXT_PUBLIC_* はプレースホルダー） |

push トリガーは `branches: ["**"]` に対して全ブランチで動く。PR は `main` 宛て。

---

## CD（GitHub Actions）

`.github/workflows/cd.yml` が `main` への push でトリガー：

1. `deploy-api`: Docker build → Artifact Registry push → Cloud Run（works-logue-api / asia-northeast1）デプロイ
2. `deploy-web`: API デプロイ完了後、同様に web イメージをビルド → デプロイ
3. 環境変数は `gcloud run deploy --set-env-vars` で注入（DATABASE_URL / SUPABASE_* / CORS_ORIGINS）

デプロイ済み URL:
- API: `https://works-logue-api-369619150476.asia-northeast1.run.app`
- Web: `https://works-logue-web-369619150476.asia-northeast1.run.app`

---

## Troubleshooting

### `pip install -e ".[dev]"` が失敗する

- **原因**: Python 3.12 未満、または asyncpg のビルド依存（libpq）不足
- **対応**:
  - `python --version` で 3.12+ を確認
  - Linux/macOS: `apt install libpq-dev` / `brew install libpq`
  - Windows: 通常はホイールが配布されるためビルド不要

### `npm run build` が型エラーで失敗する

- **原因**: Next.js 15 の strict 型チェック、または Server Component の async/await 漏れ
- **対応**:
  1. `npx tsc --noEmit` で詳細エラーを取得
  2. 該当ファイルの Promise 型 / async シグネチャを修正
  3. 再度 `npm run build`

### Docker ビルドで `NEXT_PUBLIC_*` が undefined

- **原因**: `--build-arg` を渡し忘れ
- **対応**: build-arg 3 つ（SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY / API_URL）を必ず指定する

### Cloud Run デプロイ後 API が 503

- **原因**: `DATABASE_URL` 未設定 or Supabase の direct connection が pooler 経由でない
- **対応**: `gcloud run services describe works-logue-api --region=asia-northeast1` で env を確認、`DATABASE_URL` に `?prepared_statement_cache_size=0&statement_cache_size=0` を付与（asyncpg + Supabase pooler 互換のため）
