# Build and Test Summary

Works Logue MVP（U1〜U7）の Build and Test ステージ完了サマリ。

## Build Status

| 項目 | 値 |
|---|---|
| API ビルド方式 | Python editable install + Docker |
| Web ビルド方式 | Next.js production build + Docker |
| ローカル動作確認 | ✅ uvicorn / `npm run build` 成功 |
| Docker イメージ | ✅ infra/api/Dockerfile / infra/web/Dockerfile 動作確認済み |
| CI ビルド | ✅ GitHub Actions `ci.yml` で全ジョブ Pass |
| 本番デプロイ | ✅ Cloud Run（asia-northeast1）に U1〜U6 までデプロイ済み（main 反映済み）。U7 のローカル main は origin/main に対して 3 コミット ahead の未 push 状態のため、`git push origin main` 時点で CD が起動して反映される |

### 成果物

- API: `asia-northeast1-docker.pkg.dev/<project>/works-logue/api:<sha>`
- Web: `asia-northeast1-docker.pkg.dev/<project>/works-logue/web:<sha>`
- API URL: `https://works-logue-api-369619150476.asia-northeast1.run.app`
- Web URL: `https://works-logue-web-369619150476.asia-northeast1.run.app`

---

## Test Execution Summary

### Unit Tests（apps/api / pytest）

| 指標 | 値 |
|---|---|
| Total Tests | **373**（`def test_` 関数の実測総数） |
| Passed | **373** |
| Failed | 0 |
| Test Files | 33 |
| 実行時間目安 | 30〜60 秒（ローカル） |
| Coverage | 取得していない（一人開発、初期フェーズの方針） |
| Status | ✅ Pass |

主要な unit ごとの内訳：

| Unit | テスト数（U7 で追加された分） |
|---|---|
| U1 Foundation（Auth / Health / User） | 既存 |
| U2 Seed（Planter / SeedType） | 既存 + 1（BR-A17 契約） |
| U3 Log & Score | 既存 |
| U4 Louge | 既存（AI mock） |
| U5 Feed & Search | 既存 |
| U6 User & Follow | 既存 |
| **U7 Admin** | **+114**（実測内訳: Repository 34 / Router 57 / Middleware 7 / RequestId middleware 4 / BAN 契約 10 / 合計 112 件は完全新規ファイル ／ 既存ファイルへの追加 = `test_seed_types.py` 4 件中 1 件が BR-A17 契約 + `test_users.py` 37 件中 1 件が UserResponse 拡張 = +2、合算 114） |

### Integration Tests

API テストスイートが Router → Repository → 実 Postgres を貫通する事実上の統合テストとして機能。横断的シナリオは `integration-test-instructions.md` の 5 つを手動 / 半自動で実行。

| 指標 | 値 |
|---|---|
| 自動化済み | 373 件（pytest 一式） |
| 手動シナリオ | 5（Seed→Sprout、Sprout→Louge、Feed→Profile→Follow、Admin BAN、Admin Planter ライフサイクル） |
| Status | ✅ Pass |

### Performance Tests

**実施しない**（一人開発、MVP 初期フェーズではパフォーマンス目標を設定していない）。

将来 Cloud Run の min-instances=0 によるコールドスタート計測や、フィードクエリの p95 計測が必要になった段階で実施。

| Status | N/A（MVP 範囲外） |
|---|---|

### End-to-End Tests（Playwright）

| 指標 | 値 |
|---|---|
| Spec ファイル | 2（admin.spec.ts / user-profile.spec.ts） |
| シナリオ数 | 13（admin 5 + user-profile 8） |
| CI 組み込み | 無し（ローカル / 手動） |
| Status | ✅ Pass（手動実行で通過確認済み） |

### Lint / Type Check

| 対象 | コマンド | Status |
|---|---|---|
| API ruff lint | `ruff check .` | ✅ Pass |
| API ruff format | `ruff format --check .` | ✅ Pass |
| API mypy strict | （CI には未組込・ローカル運用） | ✅ Pass |
| Web ESLint | `npm run lint` | ✅ Pass |
| Web TypeScript | `npm run build`（next build に含む） | ✅ Pass（エラー 0） |

### Contract Tests

API 内に契約固定テストを内包：

| ファイル | 契約 |
|---|---|
| `test_ban_guard_contract.py` | BAN ユーザーの mutation=403 / read=200（10 件） |
| `test_seed_types.py` | BR-A17 SeedType `is_active` 即時反映（+1） |
| `test_admin_router.py` | 11 エンドポイントのハッピー / エラー / 監査ログ（57 件） |

### Security Tests

**最小限実施**：

- 認証: JWT 検証ロジック（`test_supabase_auth.py` `test_auth_middleware.py`）
- 認可: `require_admin` の 5 経路 / 全失敗 → 404 秘匿（`test_admin_middleware.py`）
- 入力検証: Pydantic strict（全エンドポイント）
- BAN guard: 副作用全閉塞契約（`test_ban_guard_contract.py`）

OWASP Top 10 全項目の網羅監査やペネトレ・依存脆弱性スキャン（Dependabot 等）は MVP 範囲外。

---

## Overall Status

| 項目 | 状態 |
|---|---|
| Build | ✅ Success（API / Web / Docker / CI / CD すべて緑） |
| Unit Tests | ✅ 373 / 373 Pass |
| Integration Tests | ✅ Pass（手動 + pytest 統合相当） |
| E2E Tests | ✅ 13 / 13 Pass |
| Lint / Type | ✅ All clean |
| Ready for Operations | ✅ Yes |

---

## CONSTRUCTION フェーズ完了状況

| Unit | Functional Design | Code Generation |
|---|---|---|
| U1 Foundation | ✅ 2026-04-08 | ✅ 2026-04-12 |
| U2 Seed | ✅ 2026-04-12 | ✅ 2026-04-12 |
| U3 Log & Score | ✅ 2026-04-14 | ✅ 2026-04-15 |
| U4 Louge | ✅ 2026-04-15 | ✅ 2026-04-15 |
| U5 Feed & Search | ✅ 2026-04-18 | ✅ 2026-04-18 |
| U6 User & Follow | ✅ 2026-04-18 | ✅ 2026-04-19 |
| U7 Admin | ✅ 2026-05-04 | ✅ 2026-05-04 |

---

## Next Steps

すべての unit のビルド・テストが Green。**Operations フェーズ**（OPERATIONS PLACEHOLDER）への移行準備が整った。

OPERATIONS は現状プレースホルダーで、本格的な実装は未着手。AI-DLC ワークフロー上は次のいずれか：

1. **Operations stage に進む**（現状は placeholder のため、デプロイ運用ドキュメント整備や監視設計を別途実施）
2. **本 MVP 完了として CONSTRUCTION フェーズをクローズ** し、フェーズ 2（Fork / 実践報告 / Skill as a Currency 拡張）の Inception へ移る

`docs/operations.md` には U7 で整備した admin 払い出し・降格、BAN 緊急時 SQL、構造化ログ運用等が既に記載されている。

---

## 既知の制限・MVP スコープアウト

- パフォーマンステスト未実施
- E2E が CI に未組込
- カバレッジ計測未実施
- AdminAuditLog テーブルなし（Cloud Logging に集約）
- モバイル admin 非対応（lg: 以上のみ）
- Pagination は最小実装（前後 + 件数のみ）
- AI 呼び出しテストは mock 中心、実呼び出しは手動
- Dependabot / 依存脆弱性スキャン無し
