# AI-DLC State Tracking

## Project Information
- **Project Type**: Greenfield
- **Start Date**: 2026-04-05T00:00:00Z
- **Current Stage**: OPERATIONS / Domain Mapping を 2026-05-04 に再開。CONSTRUCTION 全ステージ完了（U1〜U7 + Build and Test）。本番 URL は `*.run.app` のままで稼働中。`workslogue.com`（apex=Web、`api.workslogue.com`=API）への切替を Cloud Run domain mappings 方式で実施するため、Operations の placeholder を解除して正式ステージに昇格。

## Workspace State
- **Existing Code**: No
- **Reverse Engineering Needed**: No
- **Workspace Root**: C:\Users\pinkb\Workspace\10_Projects\works-logue

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | No | Requirements Analysis |
| Property-Based Testing | No | Requirements Analysis |

## Execution Plan Summary
- **Total Stages to Execute**: 5 (Application Design, Units Generation, Functional Design x N, Code Generation x N, Build and Test)
- **Stages to Skip**: User Stories, NFR Requirements, NFR Design, Infrastructure Design
- **Unit Strategy**: Feature Slice (vertical, UI+API per unit, Figma MCP 参照)

## Stage Progress

### INCEPTION PHASE
- [x] Workspace Detection — Completed 2026-04-05
- [x] Requirements Analysis — Completed 2026-04-05
- [ ] User Stories — SKIP (一人開発、要件に詳細シーン記載済み)
- [x] Workflow Planning — Completed 2026-04-05
- [x] Application Design — Completed 2026-04-06
- [x] Units Generation — Completed 2026-04-06

### CONSTRUCTION PHASE
- [ ] Per-Unit Loop (feature slice x N)
  - [ ] U1 Foundation
    - [x] Functional Design — Completed 2026-04-08
    - [x] Code Generation — Completed 2026-04-12
  - [ ] U2 Seed
    - [x] Functional Design — Completed 2026-04-12
    - [x] Code Generation — Completed 2026-04-12
  - [ ] U3 Log & Score
    - [x] Functional Design — Completed 2026-04-14
    - [x] Code Generation — Completed 2026-04-15
  - [ ] U4 Louge
    - [x] Functional Design — Completed 2026-04-15
    - [x] Code Generation — Completed 2026-04-15
  - [ ] U5 Feed & Search
    - [x] Functional Design — Completed 2026-04-18
    - [x] Code Generation — Completed 2026-04-18
  - [x] U6 User & Follow — Approved 2026-04-30
    - [x] Functional Design — Completed 2026-04-18
    - [x] Code Generation — Completed 2026-04-19
  - [x] U7 Admin — Completed 2026-05-04
    - [x] Functional Design — Completed 2026-05-04
    - [x] Code Generation — Completed 2026-05-04
      - [x] Part 1 Plan v2 — Approved 2026-05-04 (`construction/plans/u7-admin-code-generation-plan.md`、全 42 Step / Phase 1〜18)
      - [x] Part 2 Generation — Step 1〜42 完了
        - Phase 1 (Step 1): UserResponse 拡張
        - Phase 2 (Step 2): RequestIdMiddleware + structlog contextvars
        - Phase 3 (Step 3): require_admin Depends + 7 テスト
        - Phase 4 (Step 4-5): AdminRepository (テスト 34 件 + 実装)
        - Phase 5 (Step 6): Admin Pydantic スキーマ
        - Phase 6 (Step 7-17): AdminRouter 11 エンドポイント (router テスト 57 件、契約 1 件)
        - Phase 7 (Step 18): BAN ガード契約テスト 10 件
        - Phase 8 (Step 19-21): AppUser 拡張 + auth-server.ts (getCurrentUser / serverFetch)
        - Phase 9 (Step 22-23): BannedBanner + ルートレイアウト挿入
        - Phase 10 (Step 24-27): AdminLayout / Shell / Header / Sidebar + PublicChrome bypass
        - Phase 11 (Step 28): Dashboard ページ + StatCard
        - Phase 12 (Step 29-30): UserManagement + Ban/Unban ダイアログ
        - Phase 13 (Step 31-32): PlanterManagement + Archive/Restore/Delete ダイアログ
        - Phase 14 (Step 33-34): SeedType マスタ + EditDescription ダイアログ
        - Phase 15 (Step 35-39): 共通 Dialog/Switch/Pagination/FilterChipGroup + adminApi
        - Phase 16 (Step 40): docs/operations.md
        - Phase 17 (Step 41): apps/web/e2e/admin.spec.ts (smoke 5 シナリオ)
        - Phase 18 (Step 42): aidlc-docs/construction/u7-admin/code/code-summary.md
      - 検証: API テスト 350 件 全 Pass / Web TypeScript エラー 0
- [x] Build and Test — Completed 2026-05-04
  - 生成ファイル: `aidlc-docs/construction/build-and-test/{build-instructions,unit-test-instructions,integration-test-instructions,e2e-test-instructions,build-and-test-summary}.md`
  - 検証結果: API 373/373 Pass（test 関数実測総数 / 33 ファイル）、Web build clean、E2E 13/13、CI/CD 緑、本番 Cloud Run へ U1〜U6 反映済み（U7 はローカル main が origin/main に対し 3 コミット ahead の未 push 状態。`git push origin main` 時点で CD が起動）

### OPERATIONS PHASE
- [x] Operations (placeholder) — 形式承認 2026-05-04。本格的な運用設計（監視・SLO・インシデント対応）は MVP 範囲外として別途実施。`docs/operations.md` に admin 払い出し / BAN 緊急時 SQL / 構造化ログ等の最低限の運用手順は集約済み。
- [ ] Domain Mapping — 開始 2026-05-04
  - **目的**: Cloud Run の `*.run.app` URL から本番ドメイン `workslogue.com` への切替。SSL は Google managed cert（Let's Encrypt）で自動運用。
  - **構成**:
    - apex `workslogue.com` → `works-logue-web`（A/AAAA レコード 4 本）
    - `api.workslogue.com` → `works-logue-api`（CNAME → `ghs.googlehosted.com.`）
    - `www.workslogue.com` → 301 リダイレクト（DNS or Cloud Run リライト、後続検討）
  - **方式**: Cloud Run domain mappings（asia-northeast1 GA）。Load Balancer / Cloud Armor は MVP 不要のため採用しない。
  - **対応する Brownfield 変更**:
    - `.github/workflows/cd.yml` の `CORS_ORIGINS` を `https://workslogue.com` に切替
    - 同 workflow の `--build-arg NEXT_PUBLIC_API_URL` を `https://api.workslogue.com` に切替
    - Supabase Auth の **Site URL / Redirect URLs** に新ドメインを追加（旧 URL は移行期間中は残す）
  - **生成ドキュメント**:
    - `aidlc-docs/operations/plans/domain-mapping-plan.md` — 実行プラン（チェックボックス）
    - `aidlc-docs/operations/domain-mapping/dns-records.md` — DNS レコード仕様
    - `aidlc-docs/operations/domain-mapping/cloud-run-mapping.md` — gcloud / コンソール手順
    - `aidlc-docs/operations/domain-mapping/verification.md` — 疎通・SSL・CORS 検証手順
    - `aidlc-docs/operations/domain-mapping/rollback.md` — DNS / mapping 削除によるロールバック
  - **運用ドキュメント反映**: `docs/operations.md` にドメイン運用セクション追加（証明書再発行・サブドメイン追加・CORS 切替・cutover 手順）
