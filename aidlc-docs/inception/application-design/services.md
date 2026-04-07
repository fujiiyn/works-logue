# Services Definition

サービスレイヤーの定義とオーケストレーションパターン。

---

## サービスアーキテクチャ概要

```
+--Router Layer (HTTP)--------------------------------------------+
| PlanterRouter | LogRouter | UserRouter | SearchRouter | Follow  |
+--Service Layer (Business Logic)--------------------------------+
| ScoreEngine | LougeGenerator | InsightCalc | FeedRanker | AIFac |
+--Repository Layer (Data Access)--------------------------------+
| PlanterRepo | LogRepo | UserRepo | TagRepo                     |
+--Infrastructure Layer (External Services)----------------------+
| Database(SQLAlchemy) | SupabaseAuth | SupabaseStorage | Vertex  |
+----------------------------------------------------------------+
```

---

## オーケストレーションパターン

### パターン1: Seed 投稿フロー

```
Client --> PlanterRouter.create_planter()
             |-> PlanterRepository.create()
             |-> TagRepository.attach_to_planter()
             |-> return PlanterResponse
```

- 同期処理。Planter 作成 + タグ紐付けをトランザクション内で実行。
- 投稿者は自動で Planter をフォロー（FollowRepository 経由）。

### パターン2: Log 投稿 + スコア再計算フロー

```
Client --> LogRouter.create_log()
             |-> LogRepository.create()
             |-> [Planter状態が seed -> sprout 遷移チェック]
             |-> BackgroundTasks.add_task(score_pipeline)  ← apps/api/pipelines/score_pipeline.py
             |-> return LogResponse

BackgroundTasks: ScorePipeline.run(planter_id)
             |-> ScoreEngine.evaluate_structure()     ← 条件A: VertexAI で構造パーツ充足率を算出（毎回）
             |-> [条件A充足 + 最低参加ライン超過?]
             |     |-> YES: ScoreEngine.evaluate_maturity()  ← 条件B: VertexAI で成熟度4観点を採点
             |     |         |-> ScoreEngine.should_bloom()  ← 条件A AND 条件B の最終判定
             |     |         |     |-> YES: LougeGenerator.bloom()
             |     |         |     |-> NO: AIFacilitator.facilitate()
             |     |-> NO: ScoreEngine.save_snapshot()
             |-> PlanterRepository.update_status() (if needed)
```

- Log 作成は同期。スコア計算は BackgroundTasks で非同期実行。
- 条件A の軽量チェックは毎回実行。条件B の本格スコアリングは条件A 充足 + 最低参加ライン超過時のみ。
- Log 投稿者は自動で Planter をフォロー。

### パターン3: Louge 開花フロー

```
LougeGenerator.bloom(planter_id)
             |-> LougeGenerator.generate()     [Vertex AI 呼び出し]
             |-> PlanterRepository.update()     [louge_content 保存]
             |-> PlanterRepository.update_status(louge)
             |-> InsightScoreCalculator.calculate()
             |-> InsightScoreCalculator.apply()
             |-> NotificationRepository.create() [開花通知イベント記録]
```

- 全て BackgroundTasks 内で非同期実行。
- Vertex AI 呼び出しが最も重い処理。タイムアウト設定必須。
- 開花完了後、フォロワーへの通知イベントを DB に記録（通知送信自体はフェーズ2）。

### パターン4: フィード取得フロー

```
Client --> PlanterRouter.list_planters(tab)
             |-> tab == "recent":   PlanterRepository.list_feed(recent)
             |-> tab == "trending":
             |     |-> PlanterRepository.list_feed(trending_candidates)  ← データ取得は Router 側
             |     |-> PlanterRepository.get_view_counts(planter_ids)
             |     |-> LogRepository.get_log_velocities(planter_ids, window_hours)
             |     |-> FeedRanker.rank_trending(planters, view_counts, log_velocities, window_hours)
             |                      ↑ FeedRanker はスコア計算のみ。Repository に依存しない
             |-> tab == "flowering": PlanterRepository.list_feed(louge_only)
             |-> return PaginatedResponse
```

- Server Component からの取得（Next.js → FastAPI）。
- 「注目」タブのみ FeedRanker による複合スコア計算が入る。データ取得と計算を分離。

### パターン5: 検索フロー

```
Client --> SearchRouter.search_planters(keyword, tag_ids, status)
             |-> [キーワードあり?] PostgreSQL full-text search
             |-> [tag_idsあり?] TagRepository 経由でフィルタ
             |-> [statusあり?] Planter 状態フィルタ
             |-> 複合条件を AND で結合
             |-> return PaginatedResponse
```

- 全条件を SQL クエリレベルで結合。アプリケーション側でのフィルタリングは行わない。

---

## サービス間の責務分離

| サービス | 責務 | 依存先 |
|---|---|---|
| ScoreEngine | スコア計算ロジック（条件A/B）のみ。開花トリガーは判定するが実行しない | VertexAIClient, LogRepository, PlanterRepository |
| LougeGenerator | AI 記事生成 + 開花処理のオーケストレーション | VertexAIClient, PlanterRepository, InsightScoreCalculator |
| InsightScoreCalculator | 貢献度スコア計算のみ。Louge 生成には関与しない | LogRepository, UserRepository |
| FeedRanker | ランキングスコア計算のみ。データは Router 側が各 Repository から取得して渡す。Repository に依存しない | なし |
| AIFacilitator | ファシリテート Log 生成のみ。スコア判定には関与しない | VertexAIClient, LogRepository |

---

## 通信方式（Frontend - Backend）

回答 Q2 に基づく混合方式:

| シーン | 方式 | 理由 |
|---|---|---|
| ページロード（フィード・Planter詳細・プロフィール） | Next.js Server Components → FastAPI | SEO・初期描画速度。サーバー間通信でレイテンシ低 |
| ユーザー操作（Seed投稿・Log投稿・フォロー・プロフィール編集） | Client Component → FastAPI 直接 | リアルタイムなUI更新。楽観的更新が可能 |
| 認証 | Client Component（Supabase Auth JS）→ JWT を FastAPI に送信 | Supabase Auth SDK はブラウザで動作。取得した JWT を Authorization ヘッダーで送信 |

---

## エラーハンドリング方針

| レイヤー | 方針 |
|---|---|
| Router | HTTP ステータスコード + 構造化エラーレスポンス（`{ detail: str, code: str }`） |
| Service | ドメイン例外（`SeedNotFoundError`, `ScoreCalculationError` 等）を raise |
| Repository | DB 例外をキャッチし、ドメイン例外に変換 |
| Infrastructure | 外部サービスの例外をキャッチし、リトライ or ドメイン例外に変換 |

---

## バックグラウンドジョブ方針（Q5 回答）

- **MVP**: FastAPI `BackgroundTasks` を使用。プロセス内非同期で十分。
- **スケール時**: Cloud Tasks / Cloud Pub/Sub に移行。サービス層のインターフェースは変更なし（`bloom()` 等のメソッドをそのままタスクとしてキューイング）。
- **設計上の配慮**: サービスメソッドは同期的な関数として実装し、呼び出し側（Router）が BackgroundTasks に登録する形にする。これにより、将来の外部キューへの移行が Router 層の変更のみで済む。
