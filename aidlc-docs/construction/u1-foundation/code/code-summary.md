# U1 Foundation — Code Summary

## 作成ファイル一覧

### Backend (apps/api/)
| ファイル | 概要 |
|---|---|
| `pyproject.toml` | Python 依存定義（FastAPI, SQLAlchemy, pytest 等） |
| `.env.example` | 環境変数テンプレート |
| `app/__init__.py` | パッケージ初期化 |
| `app/main.py` | FastAPI アプリファクトリ（CORS, ルーター, 構造化ログ） |
| `app/config.py` | pydantic-settings による環境変数管理 |
| `app/database.py` | AsyncEngine + async_sessionmaker + get_db |
| `app/dependencies.py` | get_current_user / get_optional_user（認証ミドルウェア） |
| `app/models/base.py` | Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin |
| `app/models/user.py` | User モデル |
| `app/models/planter.py` | Planter モデル |
| `app/models/log.py` | Log モデル |
| `app/models/tag.py` | Tag, PlanterTag, UserTag モデル |
| `app/models/follow.py` | PlanterFollow, UserFollow モデル |
| `app/models/notification.py` | Notification モデル |
| `app/models/planter_view.py` | PlanterView モデル |
| `app/models/score.py` | LougeScoreSnapshot, InsightScoreEvent モデル |
| `app/models/ai_config.py` | AiConfig モデル |
| `app/models/seed_type.py` | SeedType モデル |
| `app/routers/health.py` | GET /health |
| `app/routers/users.py` | GET/PATCH /api/v1/users/me, GET /api/v1/users/{id} |
| `app/schemas/user.py` | UserResponse, UserUpdate, UserPublicResponse |
| `app/services/supabase_auth.py` | SupabaseAuthClient（JWT 検証 + JWKS キャッシュ） |
| `app/tests/conftest.py` | テストフィクスチャ（SQLite, JWT モック, AsyncClient） |
| `app/tests/test_supabase_auth.py` | SupabaseAuthClient テスト |
| `app/tests/test_auth_middleware.py` | 認証ミドルウェアテスト |
| `app/tests/test_health.py` | ヘルスチェックテスト |
| `app/tests/test_users.py` | Users API テスト |

### Frontend (apps/web/)
| ファイル | 概要 |
|---|---|
| `package.json` | Next.js + Supabase + Lucide 依存定義 |
| `tsconfig.json` | TypeScript strict 設定 |
| `next.config.ts` | Next.js 設定（Supabase Storage 画像許可） |
| `tailwind.config.ts` | Figma 実測値デザイントークン |
| `postcss.config.mjs` | PostCSS 設定 |
| `.env.example` | 環境変数テンプレート |
| `app/globals.css` | Tailwind ベーススタイル |
| `app/layout.tsx` | LayoutShell（3カラムレスポンシブ） |
| `app/page.tsx` | ホームページ（placeholder） |
| `app/login/page.tsx` | ログイン/サインアップページ |
| `lib/supabase.ts` | Supabase クライアント初期化 |
| `lib/api-client.ts` | FastAPI 呼び出し用 HTTP クライアント |
| `contexts/auth-context.tsx` | AuthProvider（認証コンテキスト） |
| `components/header.tsx` | Header（ロゴ + CTA + ユーザーメニュー） |
| `components/sidebar.tsx` | Sidebar（ナビ + モバイルドロワー） |
| `components/right-sidebar.tsx` | RightSidebar + About Card |

### Database (supabase/)
| ファイル | 概要 |
|---|---|
| `config.toml` | Supabase CLI 設定 |
| `migrations/00001_create_tables.sql` | 全14テーブル + インデックス + トリガー |
| `migrations/00002_seed_master_data.sql` | seed_types + ai_configs 初期データ |
| `migrations/00003_seed_tags.sql` | docs/tags.md 全タグ（階層構造） |

### Infrastructure (infra/)
| ファイル | 概要 |
|---|---|
| `api/Dockerfile` | FastAPI multi-stage build |
| `web/Dockerfile` | Next.js multi-stage build |

### Root
| ファイル | 概要 |
|---|---|
| `.gitignore` | Git 除外設定 |

## アーキテクチャ概要

```
Browser
  ├── Next.js (apps/web) ─── Supabase Auth (OAuth/Email)
  │     └── api-client.ts ──→ FastAPI (apps/api)
  │                              ├── JWT 検証 (SupabaseAuthClient)
  │                              ├── SQLAlchemy Models
  │                              └── PostgreSQL (Supabase DB)
  └── Supabase Storage (avatars)
```

## ローカル開発手順

### Backend
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env       # 値を設定
uvicorn app.main:app --reload
```

### Frontend
```bash
cd apps/web
npm install
cp .env.example .env.local  # 値を設定
npm run dev
```

### テスト実行
```bash
cd apps/api
pip install aiosqlite      # テスト用 SQLite ドライバ
pytest
```
