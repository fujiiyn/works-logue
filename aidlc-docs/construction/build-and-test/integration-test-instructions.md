# Integration Test Instructions

apps/api のテストは **httpx の AsyncClient + 実 Postgres** で動かしているため、エンドポイント単位のテストは事実上の統合テスト（Router → Repository → DB）として機能する。本章では「複数ユニットを横断する」シナリオに絞る。

## Purpose

Seed → Log → Score → Louge → Admin の一連の流れが、複数ユニットの境界を越えて期待通りに連動することを保証する。

---

## 共有テスト環境のセットアップ

### 1. テスト用 Supabase プロジェクト

```bash
cd supabase
supabase start              # ローカル Supabase
supabase db push            # migrations 適用
```

または既存のクラウド Supabase の test schema を流用。

### 2. テストデータ投入

```bash
psql "$DATABASE_URL" -f apps/api/scripts/seed_test_data.sql
```

`seed_test_data.sql` は `users` テーブルに 3 行（田中 / 佐藤 / 鈴木 + 開発者の auth_id 参照）を入れるのみ。**Supabase Auth ユーザー本体は事前に Auth Admin API or Dashboard で作成しておく必要がある**（同 SQL 冒頭コメント参照）。Auth 側のメール / パスワードは tanaka / sato / suzuki @ test.works-logue.com / `TestPass123!` で運用固定。

### 3. API / Web の同時起動

```bash
# Terminal A
cd apps/api && uvicorn app.main:app --reload --port 8000

# Terminal B
cd apps/web && npm run dev
```

---

## Test Scenarios

### Scenario 1: Seed 投稿 → Log 集積 → Sprout 状態遷移（U2 → U3）

- **対象 Unit**: U2 Seed, U3 Log & Score
- **手順**:
  1. tanaka でログイン → `/seed/new` から Seed 投稿
  2. レスポンスの planter_id を控える
  3. sato でログイン → 同 planter に Log を 1 件投稿
  4. `GET /api/v1/planters/{id}` で `status='sprout'` に遷移していることを確認
  5. Lougeスコアが 0 → 正の値になっていることを確認
- **期待結果**: `status` が seed → sprout、`louge_score` > 0
- **クリーンアップ**: 該当 planter を archive または delete

### Scenario 2: Sprout → Louge 開花（U3 → U4）

- **対象 Unit**: U3 Log & Score, U4 Louge
- **手順**:
  1. Scenario 1 で生成した planter に対し、複数ユーザーから Log を継続投入
  2. Lougeスコアが開花閾値に到達した時点で `POST /api/v1/planters/{id}/generate-louge` を発火
  3. AI（Vertex AI）が記事を生成、`status='louge'` に遷移
- **期待結果**: `louge_content` フィールドが埋まり、status='louge'
- **注意**: AI 呼び出しを伴うため、CI では mock。手動統合テスト時のみ実呼び出し

### Scenario 3: Feed → Profile → Follow（U5 → U6）

- **対象 Unit**: U5 Feed & Search, U6 User & Follow
- **手順**:
  1. tanaka でホーム `/` にアクセス → フィードが表示される
  2. フィード上の Seed 投稿者 sato をクリック → `/user/sato`
  3. Follow ボタンクリック
  4. tanaka のホームで `following` タブに切り替え → sato の投稿のみ表示
- **期待結果**: フォロー後の following タブが正しくフィルタリング

### Scenario 4: Admin BAN → 通常ユーザーの mutation 拒否（U7）

- **対象 Unit**: U7 Admin × U2/U3/U6（被影響）
- **手順**:
  1. admin（手動で role='admin' に昇格させたアカウント）で `/admin/users` を開く
  2. 対象ユーザー suzuki を BAN（理由: "integration test"）
  3. suzuki でログイン → BannedBanner が常時表示されることを確認
  4. suzuki から Seed 投稿を試行 → 403 が返る（`test_ban_guard_contract.py` 相当）
  5. `/admin/users` で suzuki を unban
  6. suzuki が再度 Seed 投稿可能になることを確認
- **期待結果**: BAN 中は全 mutation が 403、read は 200。unban で復旧

### Scenario 5: Admin Planter Archive → Restore → Delete（U7）

- **対象 Unit**: U7 Admin × U2 Seed
- **手順**:
  1. admin で `/admin/planters` を開く
  2. 任意の seed を archive → フィードから消失
  3. restore → status='seed' でフィード復帰
  4. delete（typed confirmation 必要）→ 物理削除フラグ
- **期待結果**: 各操作後にフィード（U5）の表示が一致

---

## Run Integration Tests

API テストスイート全体が事実上の統合テスト。

```bash
cd apps/api
pytest --tb=short -q
```

これで Router 〜 Repository 〜 DB の貫通テストを 373 件実行。

特定シナリオの自動化が必要な場合は Playwright E2E（`apps/web/e2e/`）を使用：

```bash
cd apps/web
npx playwright test
```

---

## Cleanup

```bash
# テスト DB を初期化したい場合
cd supabase
supabase db reset
supabase db push
psql "$DATABASE_URL" -f ../apps/api/scripts/seed_test_data.sql
```

---

## 既知の制約

- **AI 呼び出しを含むテスト**: `test_louge_generator.py` `test_ai_facilitator.py` は Vertex AI を mock。実呼び出しは手動統合テストでのみ実施
- **Supabase Auth 連携**: テストアカウントの作成は `seed_test_data.sql` 側で SQL ベース。Supabase Dashboard 経由ではない
- **タイムゾーン**: スコア集計は JST 境界で flaky になりやすいため、各テストで `now: datetime` を明示注入
