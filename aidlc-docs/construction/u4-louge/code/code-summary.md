# U4 Louge - Code Summary

## 作成ファイル

### Backend - Services

| ファイル | 内容 |
|---|---|
| `apps/api/app/services/louge_generator.py` | LougeGenerator: Vertex AI でパターンランゲージ形式の記事生成 + 開花オーケストレーション |
| `apps/api/app/services/insight_calculator.py` | InsightScoreCalculator: AI 評価による貢献度スコア計算 + ユーザースコア更新 |

### Backend - Repositories

| ファイル | 内容 |
|---|---|
| `apps/api/app/repositories/insight_repository.py` | InsightScoreRepository: InsightScoreEvent の CRUD + ユーザースコア集計 |

### Backend - Routers

| ファイル | 内容 |
|---|---|
| `apps/api/app/routers/contributors.py` | ContributorsRouter: `GET /planters/{id}/contributors` |

### Backend - Schemas

| ファイル | 内容 |
|---|---|
| `apps/api/app/schemas/contributor.py` | ContributorResponse, ContributorsListResponse |

### Backend - Tests

| ファイル | テスト数 |
|---|---|
| `apps/api/app/tests/test_louge_generator.py` | 5 tests |
| `apps/api/app/tests/test_insight_calculator.py` | 5 tests |
| `apps/api/app/tests/test_insight_repository.py` | 3 tests |
| `apps/api/app/tests/test_contributors.py` | 3 tests |

### Frontend

| ファイル | 内容 |
|---|---|
| `apps/web/components/louge/LougeArticle.tsx` | Markdown 記事レンダリング（react-markdown） |
| `apps/web/components/louge/ContributorsSidebar.tsx` | 右サイドバーの貢献者一覧 |
| `apps/web/components/louge/LougeCopyButton.tsx` | Louge 記事のクリップボードコピー |

## 更新ファイル

| ファイル | 変更内容 |
|---|---|
| `apps/api/app/pipelines/score_pipeline.py` | 開花トリガー: `passed_maturity=True` → `LougeGenerator.bloom()` 呼び出し、status を louge に遷移 |
| `apps/api/app/repositories/planter_repository.py` | `update_louge_content()` メソッド追加 |
| `apps/api/app/schemas/planter.py` | `PlanterResponse` に louge_content, louge_generated_at, bloom_pending 追加 |
| `apps/api/app/routers/planters.py` | レスポンスに louge フィールドを含める、bloom_pending 導出ロジック |
| `apps/api/app/main.py` | contributors router 登録 |
| `apps/api/app/tests/test_score_pipeline.py` | 開花トリガーテスト 2 件追加 |
| `apps/api/app/tests/test_planter_repository.py` | update_louge_content テスト追加 |
| `apps/web/app/p/[id]/page.tsx` | PlanterDetail 型に louge フィールド追加 |
| `apps/web/app/p/[id]/planter-detail-client.tsx` | Louge 状態表示、bloom ポーリング、ContributorsSidebar 統合 |

## API エンドポイント

| メソッド | パス | 内容 |
|---|---|---|
| GET | `/api/v1/planters/{id}/contributors` | 開花 Planter の貢献者一覧（louge 状態のみ） |

既存エンドポイントの拡張:

| メソッド | パス | 変更内容 |
|---|---|---|
| GET | `/api/v1/planters/{id}` | louge_content, louge_generated_at, bloom_pending フィールド追加 |

## テストカバレッジ

- Backend: 143/143 passed（U4 追加分: 18 tests）
- Frontend: TypeScript コンパイル成功（`tsc --noEmit` exit code 0）

## DB マイグレーション

不要。既存スキーマで全要件を満たす。
