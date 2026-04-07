# Component Dependency

コンポーネント間の依存関係と通信パターン。

---

## 依存関係マトリクス（Backend）

行が依存元、列が依存先。`x` は直接依存を示す。

| 依存元 / 依存先 | PlanterRepo | LogRepo | UserRepo | TagRepo | FollowRepo | NotifRepo | ScoreEngine | LougeGen | InsightCalc | FeedRanker | AIFacil | VertexAI | SupaAuth | SupaStorage | Database |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PlanterRouter** | x | x | | x | x | | | | | x | | | | | |
| **LogRouter** | | x | | | x | | x | x | | | x | | | | |
| **UserRouter** | | | x | x | | | | | | | | | | x | |
| **SearchRouter** | x | | | x | | | | | | | | | | | |
| **FollowRouter** | x | | x | | x | | | | | | | | | | |
| **AuthMiddleware** | | | | | | | | | | | | | x | | |
| **ScoreEngine** | x | x | | | | | | | | | | x | | | |
| **LougeGenerator** | x | x | | | | x | | | x | | | x | | | |
| **InsightCalc** | | x | x | | | | | | | | | | | | |
| **FeedRanker** | | | | | | | | | | | | | | | |
| **AIFacilitator** | | x | | | | | | | | | | x | | | |
| **ScorePipeline** | | | | | | | x | x | | | x | | | | |
| **全 Repository** | | | | | | | | | | | | | | | x |

注: FeedRanker は Repository に依存しない。必要なデータ（planters, view_counts, log_velocities）は PlanterRouter が各 Repository から取得して渡す。ScoreEngine は条件A/B 両方で VertexAI を使用。

---

## 通信パターン

### Frontend → Backend

```
+--Next.js (apps/web)---+         +--FastAPI (apps/api)--+
|                       |         |                      |
| Server Components ----+--HTTP-->+ PlanterRouter        |
| (page load)           |  GET    | LogRouter            |
|                       |         | UserRouter           |
| Client Components ----+--HTTP-->+ SearchRouter         |
| (user actions)        | POST/   | FollowRouter         |
|                       | PATCH/  |                      |
|                       | DELETE  |                      |
| AuthProvider ---------+--JWT--->+ AuthMiddleware       |
| (Supabase Auth JS)    | Header  | (JWT verify)         |
+--+--------------------+         +--+-------------------+
   |                                 |
   | Supabase Auth JS               | SQLAlchemy
   v                                 v
+--Supabase Auth---+          +--Supabase PostgreSQL--+
+------------------+          +-----------------------+
```

### Backend 内部（同期呼び出し）

```
Router --> Service --> Repository --> Database
                  |
                  +--> Infrastructure (VertexAI / SupabaseAuth / SupabaseStorage)
```

全てのサービス呼び出しは同期的な関数呼び出し。非同期処理は Router 層で BackgroundTasks に登録する形で実現。

### BackgroundTasks フロー

```
LogRouter
  |-> LogRepository.create()          [同期: DB書き込み]
  |-> BackgroundTasks.add_task(        [非同期登録]
  |     score_pipeline,
  |     planter_id
  |   )
  |-> return Response                  [即座にレスポンス]

--- 以下バックグラウンド ---

score_pipeline(planter_id)
  |-> ScoreEngine.evaluate_structure()
  |-> [条件分岐]
  |     |-> ScoreEngine.evaluate_maturity()
  |     |-> LougeGenerator.bloom()
  |           |-> InsightScoreCalculator.calculate()
  |           |-> InsightScoreCalculator.apply()
```

---

## データフロー

### Seed 投稿 → Louge 開花の全体フロー

```
[User] --POST /api/planters--> [PlanterRouter]
                                  |
                                  v
                            [PlanterRepo] --INSERT--> planters
                            [TagRepo]     --INSERT--> planter_tags
                                  |
                                  v
                            return Planter(status=seed)


[User] --POST /api/planters/{id}/logs--> [LogRouter]
                                            |
                                            v
                                      [LogRepo] --INSERT--> logs
                                            |
                                      [BackgroundTasks]
                                            |
                                            v
                                      [ScoreEngine]
                                        evaluate_structure()
                                            |
                           +----------------+----------------+
                           |                                 |
                     (not ready)                       (ready: 条件A充足
                           |                         + 最低参加ライン超過)
                           v                                 |
                     save_snapshot()                          v
                                                    evaluate_maturity()
                                                             |
                                                +------------+------------+
                                                |                         |
                                          (条件B不足)               (条件B突破)
                                                |                         |
                                                v                         v
                                        [AIFacilitator]          [LougeGenerator]
                                        facilitate()              bloom()
                                          |                         |
                                          v                         +-> generate()
                                     logs(is_ai=true)               +-> update planter
                                                                    +-> InsightCalc
                                                                    +-> notifications
```

---

## 循環依存の回避

以下の原則で循環依存を防止する:

1. **Router → Service → Repository → Infrastructure**: 一方向のみ
2. **Service 間**: LougeGenerator → InsightScoreCalculator は許可（開花フロー内）。逆方向は禁止
3. **Repository 間**: 依存なし。各 Repository は自テーブルのみ操作
4. **Infrastructure 間**: 依存なし

---

## URL 設計（Q8 回答）

| パス | ページ | 備考 |
|---|---|---|
| `/` | ホームフィード | PlanterFeed（新着タブ） |
| `/p/{id}` | Planter 詳細 | 状態に応じた表示切替 |
| `/explore` | 探索・検索 | SearchExplore |
| `/user/{id}` | ユーザープロフィール | UserProfile |
| `/seed/new` | Seed 投稿 | SeedForm |
| `/login` | ログイン | Supabase Auth UI |
