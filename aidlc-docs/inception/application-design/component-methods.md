# Component Methods

メソッドシグネチャと I/O 型定義。詳細なビジネスルールは CONSTRUCTION フェーズの Functional Design で定義する。

---

## Frontend Methods

### FC-08: SeedForm

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `handleSubmit(data: SeedFormData)` | `{ type, title, body, tagIds[] }` | `Planter` | Seed 投稿を API に送信 |

### FC-09: LogThread

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `handlePostLog(data: LogFormData)` | `{ planterId, body, parentLogId? }` | `Log` | Log 投稿を API に送信 |

### FC-06: PlanterFeed

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `fetchFeed(tab, cursor?)` | `{ tab: "recent" \| "trending" \| "flowering", cursor? }` | `PlanterCard[]` | タブに応じたフィードを Server Component で取得 |

### FC-13: SearchExplore

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `search(params)` | `{ keyword?, tagIds[]?, status?, cursor? }` | `PlanterCard[]` | 検索条件で Planter を取得 |

### FC-12: UserProfile

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `updateProfile(data)` | `{ displayName?, bio?, avatar?, tagIds[]? }` | `User` | プロフィール更新を API に送信 |

---

## Backend — Router Methods（RESTful エンドポイント）

### BC-02: PlanterRouter

| エンドポイント | メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|---|
| `POST /api/planters` | `create_planter` | `CreatePlanterRequest { type, title, body, tag_ids[] }` | `PlanterResponse` | Seed 投稿（Planter 作成） |
| `GET /api/planters/{id}` | `get_planter` | `planter_id: UUID` | `PlanterDetailResponse` | Planter 詳細取得（状態に応じた Seed/Louge 情報含む） |
| `GET /api/planters` | `list_planters` | `tab: str, cursor?: str, limit?: int` | `PaginatedResponse[PlanterSummary]` | フィード取得（新着/注目/開花済み） |
| `DELETE /api/planters/{id}` | `delete_planter` | `planter_id: UUID` | `None` | ソフトデリート |

### BC-03: LogRouter

| エンドポイント | メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|---|
| `POST /api/planters/{id}/logs` | `create_log` | `CreateLogRequest { body, parent_log_id? }` | `LogResponse` | Log 投稿。投稿後にスコア再計算をトリガー |
| `GET /api/planters/{id}/logs` | `list_logs` | `planter_id: UUID, cursor?: str` | `PaginatedResponse[LogResponse]` | Planter に紐づく Log 一覧取得 |
| `DELETE /api/planters/{id}/logs/{log_id}` | `delete_log` | `planter_id: UUID, log_id: UUID` | `None` | ソフトデリート |

### BC-04: UserRouter

| エンドポイント | メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|---|
| `GET /api/users/{id}` | `get_user` | `user_id: UUID` | `UserProfileResponse` | プロフィール取得（インサイトスコア含む） |
| `PATCH /api/users/me` | `update_profile` | `UpdateProfileRequest { display_name?, bio?, tag_ids[]? }` | `UserProfileResponse` | 自身のプロフィール更新 |
| `POST /api/users/me/avatar` | `upload_avatar` | `file: UploadFile` | `{ avatar_url: str }` | アバター画像アップロード |
| `GET /api/users/{id}/seeds` | `list_user_seeds` | `user_id: UUID, cursor?: str` | `PaginatedResponse[PlanterSummary]` | ユーザーが投稿した Seed 一覧 |
| `GET /api/users/{id}/logs` | `list_user_logs` | `user_id: UUID, cursor?: str` | `PaginatedResponse[LogSummary]` | ユーザーが投稿した Log 一覧 |

### BC-05: SearchRouter

| エンドポイント | メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|---|
| `GET /api/search` | `search_planters` | `keyword?: str, tag_ids[]?: UUID, status?: str, cursor?: str` | `PaginatedResponse[PlanterSummary]` | 複合検索（タグ + キーワード全文検索 + 状態フィルタ） |
| `GET /api/tags` | `list_tags` | `category?: str, q?: str` | `Tag[]` | タグ一覧・検索（カテゴリ別） |

### BC-06: FollowRouter

| エンドポイント | メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|---|
| `POST /api/planters/{id}/follow` | `follow_planter` | `planter_id: UUID` | `None` | Planter をフォロー |
| `DELETE /api/planters/{id}/follow` | `unfollow_planter` | `planter_id: UUID` | `None` | フォロー解除 |
| `POST /api/users/{id}/follow` | `follow_user` | `user_id: UUID` | `None` | ユーザーをフォロー |
| `DELETE /api/users/{id}/follow` | `unfollow_user` | `user_id: UUID` | `None` | フォロー解除 |
| `GET /api/feed/following` | `get_following_feed` | `cursor?: str` | `PaginatedResponse[PlanterSummary]` | フォロー中フィード |

---

## Backend — Repository Methods

### BC-07: PlanterRepository

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `create(data)` | `PlanterCreate` | `Planter` | Planter レコード作成 |
| `get_by_id(id)` | `UUID` | `Planter \| None` | ID で取得 |
| `list_feed(tab, cursor, limit)` | `str, str?, int` | `list[Planter]` | フィード用リスト取得 |
| `list_by_user(user_id, cursor, limit)` | `UUID, str?, int` | `list[Planter]` | ユーザーの投稿一覧 |
| `update_status(id, status)` | `UUID, PlanterStatus` | `Planter` | 状態遷移 |
| `soft_delete(id)` | `UUID` | `None` | ソフトデリート |
| `record_view(planter_id, user_id?)` | `UUID, UUID?` | `None` | 閲覧記録 |

### BC-08: LogRepository

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `create(data)` | `LogCreate` | `Log` | Log レコード作成 |
| `list_by_planter(planter_id, cursor, limit)` | `UUID, str?, int` | `list[Log]` | Planter の Log 一覧（ネスト構造含む） |
| `list_by_user(user_id, cursor, limit)` | `UUID, str?, int` | `list[Log]` | ユーザーの Log 一覧 |
| `count_by_planter(planter_id)` | `UUID` | `int` | Planter の Log 件数 |
| `count_unique_authors(planter_id)` | `UUID` | `int` | ユニーク投稿者数 |
| `soft_delete(id)` | `UUID` | `None` | ソフトデリート |

### BC-09: UserRepository

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `get_by_id(id)` | `UUID` | `User \| None` | ID で取得 |
| `upsert_from_auth(auth_user)` | `SupabaseAuthUser` | `User` | Supabase Auth からの初回ログイン時にユーザー作成 or 更新 |
| `update_profile(id, data)` | `UUID, ProfileUpdate` | `User` | プロフィール更新 |
| `update_insight_score(id, delta)` | `UUID, float` | `User` | インサイトスコア加算 |

### BC-10: TagRepository

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `list_by_category(category)` | `str?` | `list[Tag]` | カテゴリ別タグ一覧 |
| `search(query)` | `str` | `list[Tag]` | タグ名で部分一致検索 |
| `attach_to_planter(planter_id, tag_ids)` | `UUID, list[UUID]` | `None` | Planter にタグを紐付け |
| `attach_to_user(user_id, tag_ids)` | `UUID, list[UUID]` | `None` | User にタグを紐付け |

### BC-20: FollowRepository

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `follow_planter(user_id, planter_id)` | `UUID, UUID` | `None` | Planter をフォロー（重複は無視） |
| `unfollow_planter(user_id, planter_id)` | `UUID, UUID` | `None` | Planter フォロー解除 |
| `follow_user(follower_id, followee_id)` | `UUID, UUID` | `None` | ユーザーをフォロー |
| `unfollow_user(follower_id, followee_id)` | `UUID, UUID` | `None` | ユーザーフォロー解除 |
| `list_followed_planters(user_id, cursor, limit)` | `UUID, str?, int` | `list[UUID]` | フォロー中 Planter の ID 一覧 |
| `list_followed_users(user_id, cursor, limit)` | `UUID, str?, int` | `list[UUID]` | フォロー中ユーザーの ID 一覧 |
| `is_following_planter(user_id, planter_id)` | `UUID, UUID` | `bool` | フォロー中かを確認（自動フォロー判定に使用） |

### BC-21: NotificationRepository

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `create_event(type, planter_id, actor_id?)` | `str, UUID, UUID?` | `Notification` | 通知イベントを記録。`type` 例: `"louge_bloomed"`, `"status_changed"`, `"new_seed"` |

---

## Backend — Service Methods

### BC-11: ScoreEngine

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `evaluate_structure(planter_id)` | `UUID` | `StructureResult { fulfillment_rate: float, parts: dict }` | 条件A: VertexAI で構造パーツ充足率をチェック。Log 投稿のたびに毎回実行（MVP はシンプルさ優先）。条件A/B 両方で VertexAI を使用 |
| `evaluate_maturity(planter_id)` | `UUID` | `MaturityResult { scores: dict, total: float, passed: bool }` | 条件B: 成熟度4観点スコアリング（条件A 充足 + 最低参加ライン超過時のみ実行） |
| `should_bloom(planter_id)` | `UUID` | `bool` | 条件A AND 条件B の判定結果を返す |
| `save_snapshot(planter_id, result)` | `UUID, ScoreResult` | `None` | louge_score_snapshots にスコア記録 |

### BC-12: LougeGenerator

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `generate(planter_id)` | `UUID` | `LougeContent` | Vertex AI で Louge 記事を生成。Seed + Log 群を入力とし、パターンランゲージ形式で出力 |
| `bloom(planter_id)` | `UUID` | `None` | 開花処理の全体オーケストレーション（記事生成 → Planter 状態更新 → インサイトスコア計算） |

### BC-13: InsightScoreCalculator

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `calculate(planter_id)` | `UUID` | `list[InsightScoreEvent]` | Louge 開花時に各 Log 投稿者の貢献度を算出 |
| `apply(events)` | `list[InsightScoreEvent]` | `None` | スコア加算を各ユーザーに反映し、イベントを DB に記録 |

### BC-14: FeedRanker

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `rank_trending(planters, view_counts, log_velocities, window_hours)` | `list[Planter], dict[UUID, int], dict[UUID, float], int` | `list[RankedPlanter]` | 複合スコア計算（閲覧数 + Log 投稿速度 + 構造充足率）で「注目」フィードを並び替え。データは Router 側が各 Repository から取得して渡す。FeedRanker 自身は Repository に依存しない |

### BC-15: AIFacilitator

| メソッド | 入力 | 出力 | 概要 |
|---|---|---|---|
| `facilitate(planter_id, maturity_result)` | `UUID, MaturityResult` | `Log` | 不足観点を特定し、AI ファシリテート Log を生成・保存（`is_ai_generated=True`） |
