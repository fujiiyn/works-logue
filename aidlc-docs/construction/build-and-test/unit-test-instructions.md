# Unit Test Instructions

apps/api（pytest）の単体テスト実行手順。Web 側の単体テストは持たず、UI は Playwright E2E で検証する方針。

## Prerequisites

- `apps/api/` で `pip install -e ".[dev]"` 完了済み
- 環境変数 `DATABASE_URL` 等は `.env.test` か直接 export しておく（pytest が pydantic-settings を読む）
- Supabase のテスト DB を用意（migrations 適用済み、`scripts/seed_test_data.sql` で users 行を 3 名分投入）

> **テストアカウント** — `seed_test_data.sql` は `users` テーブルに 3 行投入するのみで、対応する Supabase Auth ユーザーは事前に Auth Admin API or Supabase Dashboard で作成しておく必要がある（同 SQL 冒頭コメント参照）。Auth 側のメール / パスワードは tanaka / sato / suzuki @ test.works-logue.com / `TestPass123!`（運用記録）で固定。

---

## Run Unit Tests

### 1. 全テスト実行

```bash
cd apps/api
pytest --tb=short -q
```

期待結果：

```
========== 373 passed in XX.XXs ==========
```

### 2. Unit ごとに実行

```bash
# U7 Admin のみ
pytest app/tests/test_admin_router.py app/tests/test_admin_repository.py \
       app/tests/test_admin_middleware.py app/tests/test_request_id_middleware.py \
       app/tests/test_ban_guard_contract.py -v

# 認証関連
pytest app/tests/test_auth_middleware.py app/tests/test_supabase_auth.py -v

# スコア / Louge 関連
pytest app/tests/test_score_engine.py app/tests/test_score_pipeline.py \
       app/tests/test_louge_generator.py -v
```

### 3. カバレッジ取得（任意）

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
# htmlcov/index.html をブラウザで開く
```

---

## テストファイル一覧（33 ファイル / 373 テスト関数）

| カテゴリ | ファイル | 内容 |
|---|---|---|
| Health | `test_health.py` | `/health` エンドポイント |
| Auth | `test_auth_middleware.py`, `test_supabase_auth.py` | JWT 検証、`require_user` |
| User | `test_users.py`, `test_user_repository.py` | プロフィール CRUD、is_banned/deleted_at 拡張 |
| Planter / Seed | `test_planters.py`, `test_planter_repository.py`, `test_planter_repository_feed.py`, `test_planters_router_feed.py` | Seed 投稿・取得・フィード |
| Log | `test_logs.py`, `test_log_repository.py`, `test_log_repository_velocity.py` | Log 投稿・取得・velocity |
| Score | `test_scores.py`, `test_score_engine.py`, `test_score_pipeline.py`, `test_score_repository.py` | Lougeスコア計算 |
| Louge | `test_louge_generator.py` | AI 生成パイプライン |
| AI Facilitator | `test_ai_facilitator.py` | AI による議論誘導 |
| Insight | `test_insight_calculator.py`, `test_insight_repository.py` | インサイトスコア |
| Contributor | `test_contributors.py` | 貢献度集計 |
| Search / Feed | `test_search_router.py`, `test_feed_ranker.py` | 検索・並び替え |
| Tags | `test_tags.py`, `test_tag_repository.py` | タグ |
| SeedType | `test_seed_types.py` | seed_type マスタ + BR-A17 契約 |
| Follow | `test_follow_repository.py` | U6 フォロー |
| Settings | `test_settings_repository.py` | アプリ設定（feature_flags 等の SettingsRepository） |
| Admin | `test_admin_router.py`, `test_admin_repository.py`, `test_admin_middleware.py`, `test_request_id_middleware.py`, `test_ban_guard_contract.py` | U7 Admin |

---

## テスト戦略のキー判断

- **TDD 必須**: API 実装は Red→Green→Refactor を厳守。U2 以降の全 unit でテストを先に書いてから実装した
- **Repository 層の commit は呼び出さない**: ルーター層の commit に統一。Repository は flush までで止める
- **時刻 DI**: 集計のテストで JST 境界を跨ぐ flakiness を避けるため `now: datetime` 引数で注入
- **Auth クライアントのモック**: `app/tests/conftest.py` で `app.dependency_overrides` を使い `get_auth_client` を差し替える
- **データベースは実 Postgres**: SQLite モックは使わず Supabase 互換の Postgres でテスト（CI でも同様）

---

## Expected Result

- **Total Tests**: 373（`def test_` 関数の実測総数。`grep -rE "^\s*(async def|def) test_" app/tests/ | wc -l`）
- **Pass**: 373
- **Fail**: 0
- **Coverage**: 取得していない（一人開発、初期フェーズではカバレッジ目標なし）
- **Test Report Location**: stdout（CI ログ）/ `htmlcov/`（ローカル）

---

## 失敗した場合の対応

1. `--tb=long -v` で詳細を取得し、最初の失敗テストから順に修正
2. AsyncSession の `await` 漏れ、commit 忘れがよくある原因
3. `pytest -k <test_name>` で単一テストを集中デバッグ
4. テストデータがリーク（前のテストの副作用）している場合は `conftest.py` の fixture スコープを確認
5. Supabase 接続失敗の場合、`DATABASE_URL` の pooler/direct を切り替えて再試行
