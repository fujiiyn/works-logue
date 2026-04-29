# U6 User & Follow — Code Generation Plan

## Unit Context

- **Unit**: U6 User & Follow
- **依存**: U1 Foundation (User model, auth), U3 Log & Score (insight_score_events), U5 Feed & Search (PlanterFeed)
- **DB テーブル**: users (拡張), user_follows (既存), planter_follows (拡張), avatars/covers Storage
- **Figma**: 公開プロフィール v2 (351:159), 編集ページ (356:159)

## Code Location

- **API**: `apps/api/app/` (models, repositories, routers, schemas, services)
- **Web**: `apps/web/` (app, components, contexts, lib)
- **Migration**: `supabase/migrations/`
- **Tests**: `apps/api/tests/`
- **Documentation**: `aidlc-docs/construction/u6-user-follow/code/`

## Design Decisions

| # | 決定 | 理由 |
|---|---|---|
| D1 | フォロワー/フォロー中一覧API・UIを追加 | ポートフォリオとしての価値、Skill as a Currency の可視化 |
| D2 | 画像は選択時即POST→サーバーが users.pending_avatar_path / pending_cover_path に Storage パスを記録。PATCH時にURLフィールドは受け取らず、サーバー側で pending を正式適用し旧画像を削除。beforeunload 警告あり（画像アップロード済みも未保存変更扱い）。未採用 pending は放置し次回 POST 時に上書き（孤立ファイルは将来バッチ削除） | URL注入防止、単一リクエスト保存、セッションまたぎはシンプルに破棄 |
| D3 | 貢献グラフは `GET /users/{id}/contributions` に分離 | 365日分データをプロフィール初期ロードに含めない |
| D4 | louge_count は動的計算で進める | 初期は許容。将来の非正規化ポイントとして記録 |
| D5 | planter_follows に `is_manually_unfollowed` 追加 | 手動アンフォロー後の自動再フォローを防止 |
| D6 | social_links → 4カラム分離 (x_url, linkedin_url, wantedly_url, website_url) | 固定4種、スキーマとして自然 |
| D7 | FollowButton モバイル: タップ→確認ダイアログ→解除 | hover がないモバイルの誤爆対策 |
| D8 | 貢献グラフ: クライアントから tz パラメータ送信 (Intl API)、SSRフォールバック=Asia/Tokyo | 日付境界ズレ防止 |
| D9 | 参加Louge: insight_score_events のスコア > 0 のもののみ | 挨拶Log 1件での「貢献者」表示を防止 |
| D10 | 編集ページ URL は `/profile/edit` 固定（ID不要） | 他人IDアクセスの挙動を考えなくて済む |
| D11 | similar users: user_tags 共通タグ COUNT DESC、上位5人。認証任意（未ログイン時はフォ��ー済み除外なし） | シンプルに開始、将来埋め込みに置換可能 |
| D12 | SNSリンク: ドメイン allowlist 適用 (x.com/twitter.com, linkedin.com, wantedly.com)、website は https:// のみ | フィッシング対策 |
| D13 | オンボーディングのアバターは任意。未設定時はイニシャルアイコン (display_name先頭1文字、IDハッシュ背景色) | 離脱率抑制 |
| D14 | MIME検証は Pillow Image.open() + verify() でマ��ックバイト判定。Content-Type ヘッダーは信用しない | SVG+script 等の偽装防止 |
| D15 | 古い画像削除: 新アップロード→PATCH成功(正式適用)→旧画像削除(失敗時ログのみ)の順。画像ゼロ状態を回避 | BR-U05/U06 準拠、安全な順序 |
| D16 | フォロワー/フォロー中一覧で BAN/deleted ユーザーは除外 | データ整合性 |
| D17 | FollowListModal 内の解除: 楽観更新で即リスト除外、失敗時リストに戻す | UXレスポンス |
| D18 | マイグレーション: 全追加カラム NULL 許可、デフォ��ト NULL | 既存行の互換性 |

---

## Steps

### Phase 1: DB・モデル・スキーマ基盤 (テストの前提)

- [x] **Step 1**: DB マイグレーション
  - `supabase/migrations/00008_u6_user_follow.sql`
  - users: headline(varchar60 NULL), cover_url(text NULL), location(varchar100 NULL), x_url(text NULL), linkedin_url(text NULL), wantedly_url(text NULL), website_url(text NULL), pending_avatar_path(text NULL), pending_cover_path(text NULL) 追加。全て NULL 許可、デフォルト NULL (D18)
  - planter_follows: is_manually_unfollowed(boolean default false) 追加

- [x] **Step 2**: User モデル拡張
  - 修正: `apps/api/app/models/user.py`
  - headline, cover_url, location, x_url, linkedin_url, wantedly_url, website_url, pending_avatar_path, pending_cover_path

- [x] **Step 3**: PlanterFollow モデル拡張
  - 修正: `apps/api/app/models/follow.py`
  - is_manually_unfollowed フィールド追加

- [x] **Step 4**: User スキーマ拡張
  - 修正: `apps/api/app/schemas/user.py`
  - UserResponse (認証ユーザー自身用): 全フィールド含む (pending_* 含む)
  - UserPublicResponse (他人から見える): display_name, headline, bio, avatar_url, cover_url, location, x_url, linkedin_url, wantedly_url, website_url, insight_score, created_at。auth_id, role, is_banned, onboarded_at, pending_* は除外
  - UserUpdate に headline, location, x_url, linkedin_url, wantedly_url, website_url 追加（avatar_url/cover_url はクライアントから受け取らない D2）
  - UserProfileResponse 新規（stats, tags, featured_contribution, is_following）
  - ContributionGraphResponse 新規（date + count の配列）
  - UserPlanterListResponse, UserLogListResponse 新規
  - FollowListResponse 新規（フォロワー/フォロー中一覧用）
  - SimilarUserResponse 新規
  - SNS URL バリデータ: ドメイン allowlist (D12)

### Phase 2: FollowRepository (TDD)

- [x] **Step 5**: FollowRepository テスト
  - 新規: `apps/api/tests/test_follow_repository.py`
  - ユーザーフォロー/アンフォロー冪等性、自己フォロー禁止、カウント
  - 手動アンフォロ��後の自動フォロースキップ (is_manually_unfollowed)
  - フォロワー/フォロー中一覧取得（BAN/deleted除外 D16）
  - Planterフォロー/アンフォロー

- [x] **Step 6**: FollowRepository 実装
  - 修正: `apps/api/app/repositories/follow_repository.py`
  - follow_user, unfollow_user, unfollow_planter
  - is_following_user, get_follower_count, get_following_count
  - get_followers (cursor pagination, BAN/deleted除外)
  - get_following_users (cursor pagination, BAN/deleted除外)
  - get_following_planter_ids, get_following_user_ids
  - follow_planter 改修: is_manually_unfollowed=true ならスキップ
  - unfollow_planter 改修: is_manually_unfollowed=true にセット

### Phase 3: UserRepository (TDD)

- [x] **Step 7**: UserRepository テスト
  - 新規: `apps/api/tests/test_user_repository.py`
  - プロフィール集計 (louge_count, featured_contribution)
  - 参加Louge の insight_score > 0 フィルタ (D9)
  - 貢献グラフ (tz 指定、日付境界テスト)
  - 投稿履歴 (seeds/louges/logs)
  - similar users (共通タグ、認証あり/なし)

- [x] **Step 8**: UserRepository 実装
  - 新規: `apps/api/app/repositories/user_repository.py`
  - get_by_id (deleted/banned チェック付き)
  - get_louge_count (Seed投稿者+Log貢献者の重複排除、insight_score > 0)
  - get_featured_contribution (最高スコアの Louge 貢献)
  - get_contribution_graph (365日分、tz パラメータで AT TIME ZONE 集計)
  - get_user_planters (tab=seeds/louges, cursor pagination)
  - get_user_logs (cursor pagination)
  - get_similar_users (共通タグ COUNT DESC、認証時は自分+フォロー済み除外、上位5人)

### Phase 4: StorageClient

- [x] **Step 9**: SupabaseStorageClient 実装
  - 新規: `apps/api/app/services/storage_client.py`
  - upload(bucket, path, file_data, content_type) → public_url
  - delete(bucket, path) — 失敗時はログ出力のみ (D15)
  - MIME 検証: Pillow Image.open() + verify() でマジックバイト判定 (D14)
  - サーバー側リサイズ: avatar 256x256, cover 1200x340 (Pillow)
  - 画像フロー (D2/D15):
    1. POST /avatar: 新画像アップロード → users.pending_avatar_path に Storage パスを記録
    2. PATCH /users/me: pending_avatar_path があれば avatar_url に正式適用 → 旧画像を delete(失敗時ログのみ) → pending_avatar_path を NULL クリア
    3. 次回 POST /avatar 時: 前回の pending があれば上書���（旧 pending ファイルは孤立許容）
  - cover も同様のフロー

### Phase 5: Users ルーター (TDD)

- [x] **Step 10**: Users ルーターテスト
  - 修正/新規: `apps/api/tests/test_users.py`
  - GET /users/{id} — プロフィール詳細 (is_following, stats, tags)
  - PATCH /users/me — 新フィールド、avatar_url/cover_url はリクエストから受け取らない (D2)、pending→正式適用フロー
  - PATCH /users/me SNS allowlist (D12): 正規ドメインで成功、allowlist逸脱で 422、空文字/NULLで成功(削除)
  - POST /users/me/avatar — サイズ/形式検証、Pillow MIME検証、URL返却
  - POST /users/me/cover — 同上
  - POST /users/{id}/follow, DELETE /users/{id}/follow — 冪等性、自己フォロー
  - GET /users/{id}/followers, GET /users/{id}/following — BAN/deleted除外
  - GET /users/{id}/planters?tab=seeds|louges
  - GET /users/{id}/logs
  - GET /users/{id}/contributions?tz=Asia/Tokyo
  - GET /users/{id}/similar — 認証あり/なし
  - deleted/banned ユーザーの 404

- [x] **Step 11**: Users ルーター実装
  - 修正: `apps/api/app/routers/users.py`
  - GET /users/{id} → UserProfileResponse
  - PATCH /users/me → 新フィールド対応。avatar_url/cover_url はサーバー側で pending から適用 (D2)
  - POST /users/me/avatar → 即アップロード、pending記録、URL返却
  - POST /users/me/cover → 同上
  - POST /users/{id}/follow, DELETE /users/{id}/follow
  - GET /users/{id}/followers, GET /users/{id}/following
  - GET /users/{id}/planters?tab=seeds|louges
  - GET /users/{id}/logs
  - GET /users/{id}/contributions?tz=Asia/Tokyo
  - GET /users/{id}/similar

### Phase 6: Planters ルーター (TDD)

- [x] **Step 12**: Planters ルーターテスト (フォロー中タブ + Planterフォロー)
  - 修正: `apps/api/tests/test_planters.py`
  - GET /planters?tab=following — 認証必須、フォロー中フィード
  - POST /planters/{id}/follow, DELETE /planters/{id}/follow

- [x] **Step 13**: Planters ルーター実装
  - 修正: `apps/api/app/routers/planters.py`
  - POST /planters/{id}/follow, DELETE /planters/{id}/follow
  - GET /planters?tab=following (認証必須、フォロー中フィード)

- [x] **Step 14**: main.py 確認 + Backend 全テスト実行
  - 新規ルート登録漏れチェック
  - pytest 全テスト pass 確認

### Phase 7: Frontend (Figma参照→実装→E2E)

- [x] **Step 15**: Figma参照 → UserProfilePage 実装
  - 新規: `apps/web/app/user/[id]/page.tsx`
  - 新規: `apps/web/components/user/ProfileHeader.tsx` (カバー、アバター/InitialAvatar、ユーザー情報、FollowButton、タグ、居住地+SNSリンク rel="noopener noreferrer" target="_blank")
  - 新規: `apps/web/components/user/StatsRow.tsx` (スコア、Louge貢献、フォロワー→モーダル、フォロー中→モーダル)
  - 新規: `apps/web/components/user/FollowListModal.tsx` (フォロワー/フォロー中一覧、cursor pagination、楽観更新でフォロー解除 D17)
  - 新規: `apps/web/components/user/ContributionGraph.tsx` (GitHub草風ヒートマップ、/contributions で遅延取得、Intl APIでtz取得→クエリ送信、SSRフォールバック=Asia/Tokyo D8)
  - 新規: `apps/web/components/user/FeaturedContribution.tsx`
  - 新規: `apps/web/components/user/ProfileTabs.tsx` (Seed/Log/参加Louge)
  - 新規: `apps/web/components/user/FollowButton.tsx` (デスクトップ: hover変化、モバイル: 確認ダイアログ D7)
  - 新規: `apps/web/components/user/UserProfileSidebar.tsx` (バッジ、似たユーザー + FollowButton)
  - 新規: `apps/web/components/user/InitialAvatar.tsx` (display_name先頭1文字、IDハッシュ背景色 D13)

- [x] **Step 16**: Figma参照 → ProfileEditPage 実装
  - 新規: `apps/web/app/profile/edit/page.tsx` (URL固定、ID不要 D10)
  - CoverImageEditor, AvatarEditor (選択時即アップロード→URLプレビュー、AbortController対応キャンセルボタン)
  - SocialLinksForm (4フィールド、ドメインヒント表示)
  - TagAccordionSelector 再利用
  - 保存は単一PATCH（avatar_url/cover_urlはサーバー側自動適用）
  - beforeunload 離脱警告 (テキスト未保存変更 + 画像アップロード済み未PATCH も対象 D2/D14補足)
  - 未ログイン → /login リダイレクト

- [x] **Step 17**: PlanterFeed にフォロー中タブ追加 + AuthContext・Header 拡張
  - 修正: `apps/web/components/planter/PlanterFeed.tsx` (following タブ追加、未ログイン時ログイン誘導)
  - 修正: `apps/web/contexts/auth-context.tsx` (AppUser に headline, cover_url, location, x_url, linkedin_url, wantedly_url, website_url 追加)
  - Header のユーザーアイコン → `/user/{id}` プロフィールページへのリンク（Header は全ページ共通 — 変更後に他ページへの影響がないか確認）

- [x] **Step 18**: api-client に画像アップロード用ヘルパー追加
  - 修正: `apps/web/lib/api-client.ts`
  - apiFetchUpload: multipart/form-data 対応��AbortController 対応

### Phase 8: E2E テスト

- [x] **Step 19**: Playwright E2E テスト
  - 新規: `apps/web/e2e/user-profile.spec.ts`
  - プロフィール表示（自分/他人）
  - プロフィール編集（テキスト変更→保存→反映確認）
  - 画像アップロード→保存→反映
  - フォロー/アンフォロー操作
  - フォロワー/フ���ロー中モーダル表示
  - フォロー中タブ表示
  - beforeunload 警告の発火確認

### Phase 9: Documentation

- [x] **Step 20**: コード生成サマリー
  - 新規: `aidlc-docs/construction/u6-user-follow/code/code-summary.md`

---

## Total: 20 Steps (9 Phases)
- Phase 1: DB・モデル・スキーマ基盤 (4 steps)
- Phase 2: FollowRepository TDD (2 steps: test → impl)
- Phase 3: UserRepository TDD (2 steps: test → impl)
- Phase 4: StorageClient (1 step)
- Phase 5: Users ルーター TDD (2 steps: test �� impl)
- Phase 6: Planters ルーター TDD (2 steps: test → impl) + Backend 全テスト確認 (1 step)
- Phase 7: Frontend Figma参照→実装 (4 steps)
- Phase 8: E2E テスト (1 step)
- Phase 9: Documentation (1 step)

## Future Optimization Notes
- louge_count: users テーブルへの非正規化カラム追加（アクセス増加時）
- contribution_graph: Redis/マテリアライズドビューによるキャッシュ（アクセス増加時）
- similar_users: タグ共通数 → ベクトル埋め込みによる類似度（ユーザー増加時）
- 孤立画像クリーンアップ: 定期バッチで pending のまま放置された画像を削除
