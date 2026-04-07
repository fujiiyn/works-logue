# U1 Foundation — Business Logic Model

## 概要

U1 はビジネスロジックよりもインフラ・基盤構築が中心。ここでは各インフラコンポーネントの振る舞いと接続パターンを定義する。

---

## Infrastructure Components

### Database（SQLAlchemy AsyncSession）

```
アプリ起動時:
  1. AsyncEngine を create_async_engine() で生成
     - pool_size: 5（MVP）
     - max_overflow: 10
     - pool_timeout: 30s
     - pool_recycle: 1800s
  2. async_sessionmaker を生成
  3. FastAPI の Depends で get_db() を提供

get_db():
  async with session_maker() as session:
      yield session
```

接続先: 環境変数 `DATABASE_URL`（Supabase PostgreSQL 接続文字列）

---

### SupabaseAuthClient

```
初期化:
  1. SUPABASE_URL + SUPABASE_ANON_KEY で Supabase クライアントを生成
  2. JWKS エンドポイント URL を構成: {SUPABASE_URL}/auth/v1/.well-known/jwks.json
  3. JWKS をフェッチしメモリキャッシュ（TTL: 1時間）

verify_token(token: str) -> AuthUser:
  1. JWKS からRS256公開鍵を取得
  2. jwt.decode(token, key, algorithms=["RS256"], audience="authenticated")
  3. payload から sub, email, user_metadata を抽出
  4. AuthUser dataclass を返す

get_user_metadata(auth_id: UUID) -> dict:
  1. Supabase Admin API (service_role_key) でユーザー情報を取得
  2. display_name, email, avatar_url 等を返す
```

---

### SupabaseStorageClient

```
初期化:
  1. SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY で Admin クライアントを生成
  2. バケット名: "avatars"

upload_avatar(user_id: UUID, file: bytes, content_type: str) -> str:
  1. ファイルパス: avatars/{user_id}/{timestamp}.{ext}
  2. Supabase Storage にアップロード
  3. 公開 URL を返す: {SUPABASE_URL}/storage/v1/object/public/avatars/...

delete_avatar(path: str) -> None:
  1. 旧ファイルを削除
```

---

### VertexAIClient

```
初期化:
  1. GCP_PROJECT_ID + GCP_LOCATION (us-central1) で Vertex AI クライアントを生成
  2. サービスアカウント認証（GOOGLE_APPLICATION_CREDENTIALS）
  3. モデルは呼び出し時に指定（ai_configs テーブルから取得）

generate_text(model_name: str, prompt: str, system_instruction: str, temperature: float = 0.7) -> str:
  1. model_name で Vertex AI Generative AI API を呼び出し
  2. レスポンスのテキスト部分を返す
  3. タイムアウト: 60s（Louge 生成は 120s）
  4. リトライ: 最大3回（exponential backoff）
  5. エラー時: VertexAIError を raise
```

モデル使い分け（ai_configs から取得）:

| 用途 | 初期モデル | 頻度 | 理由 |
|---|---|---|---|
| スコアリング（条件A/B） | gemini-2.0-flash | 高（Log 投稿ごと） | コスト最優先 |
| Louge 記事生成 | gemini-2.0-pro | 低（開花時のみ） | 品質重視 |
| AI ファシリテート | gemini-2.0-flash | 中 | コスト効率 |

---

### AuthMiddleware（FastAPI Dependency）

```
get_current_user(request: Request, db: AsyncSession) -> User:
  1. Authorization ヘッダーから Bearer トークンを取得
  2. SupabaseAuthClient.verify_token(token)
  3. users テーブルで auth_id を検索
  4. 存在しない場合: 自動作成（BR-02）
  5. deleted_at IS NOT NULL: 403 raise
  6. User を返す

get_optional_user(request: Request, db: AsyncSession) -> User | None:
  1. Authorization ヘッダーがない場合: None を返す
  2. ある場合: get_current_user と同じフロー
```

---

## 環境変数一覧

| 変数名 | 説明 | 例 |
|---|---|---|
| DATABASE_URL | Supabase PostgreSQL 接続文字列 | postgresql+asyncpg://... |
| SUPABASE_URL | Supabase プロジェクト URL | https://xxx.supabase.co |
| SUPABASE_ANON_KEY | Supabase anonymous key | eyJ... |
| SUPABASE_SERVICE_ROLE_KEY | Supabase service role key | eyJ... |
| GCP_PROJECT_ID | GCP プロジェクト ID | works-logue-dev |
| GCP_LOCATION | Vertex AI リージョン | us-central1 |
| GOOGLE_APPLICATION_CREDENTIALS | GCP サービスアカウント JSON パス | /path/to/sa.json |
| CORS_ORIGINS | CORS 許可オリジン | http://localhost:3000 |
