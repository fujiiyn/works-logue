# U6 User & Follow — Code Generation Summary

## Overview

U6 implements the user profile system, follow functionality, and following feed for Works Logue's "Skill as a Currency" vision.

## Files Created / Modified

### Database
- **Created**: `supabase/migrations/00008_u6_user_follow.sql` — users table extension (headline, cover_url, location, SNS URLs, pending image paths) + planter_follows.is_manually_unfollowed

### Backend (apps/api)

#### Models (Modified)
- `app/models/user.py` — Added headline, cover_url, location, x_url, linkedin_url, wantedly_url, website_url, pending_avatar_path, pending_cover_path
- `app/models/follow.py` — Added is_manually_unfollowed to PlanterFollow

#### Schemas (Modified)
- `app/schemas/user.py` — UserResponse, UserPublicResponse expanded; UserProfileResponse, ContributionGraphResponse, UserPlanterListResponse, UserLogListResponse, FollowListResponse, SimilarUserResponse, ImageUploadResponse added; SNS URL domain allowlist validators (D12)

#### Repositories
- **Created**: `app/repositories/user_repository.py` — get_by_id (BR-U08), get_louge_count (D9), get_featured_contribution, get_contribution_graph (D8), get_user_planters, get_user_logs, get_similar_users (D11)
- **Modified**: `app/repositories/follow_repository.py` — follow_user, unfollow_user, is_following_user, get_follower_count, get_following_count, get_followers (D16), get_following_users (D16), get_following_planter_ids, get_following_user_ids, unfollow_planter (D5)
- **Modified**: `app/repositories/tag_repository.py` — get_user_tags
- **Modified**: `app/repositories/planter_repository.py` — list_following (BR-FF01)

#### Services
- **Created**: `app/services/storage_client.py` — SupabaseStorageClient with Pillow MIME validation (D14), center-crop resize, pending image flow (D2/D15)

#### Routers
- **Modified**: `app/routers/users.py` — GET /users/{id} (full profile), PATCH /users/me (new fields + pending image apply), POST avatar/cover upload, POST/DELETE follow, GET followers/following, GET planters/logs, GET contributions, GET similar
- **Modified**: `app/routers/planters.py` — POST/DELETE planter follow, GET ?tab=following (BR-FF01)

#### Tests
- `app/tests/test_follow_repository.py` — 18 tests
- `app/tests/test_user_repository.py` — 17 tests (new)
- `app/tests/test_users.py` — 35 tests (expanded)
- `app/tests/test_planters.py` — 21 tests (expanded)
- **Total: 245 backend tests passing**

### Frontend (apps/web)

#### Pages
- **Created**: `app/user/[id]/page.tsx` — User profile page
- **Created**: `app/profile/edit/page.tsx` — Profile edit page (D10: fixed URL)

#### Components
- **Created**: `components/user/InitialAvatar.tsx` — ID-hash colored initial (D13)
- **Created**: `components/user/FollowButton.tsx` — Follow/unfollow（静的「フォロー」/「フォロー中」、確認ダイアログなしで即時解除）
- **Created**: `components/user/ProfileHeader.tsx` — Cover, avatar, user info, tags, location, SNS links
- **Created**: `components/user/StatsRow.tsx` — Score, louge count, follower/following counts
- **Created**: `components/user/FollowListModal.tsx` — Follower/following list with cursor pagination, optimistic unfollow (D17)
- **Created**: `components/user/ContributionGraph.tsx` — GitHub-style heatmap, Intl API tz (D8)
- **Created**: `components/user/ProfileTabs.tsx` — Seed/Log/Louge tabs with infinite scroll
- **Created**: `components/user/UserProfileSidebar.tsx` — Badges placeholder, similar users (D11)

#### Modified
- `lib/api-client.ts` — apiFetchUpload (multipart/form-data, AbortController)
- `contexts/auth-context.tsx` — AppUser extended with new fields
- `components/planter/PlanterFeed.tsx` — "Following" tab added, login prompt for unauthenticated

#### E2E
- **Created**: `e2e/user-profile.spec.ts` — 8 Playwright tests
- **Created**: `playwright.config.ts`

## Design Decisions Applied

| # | Decision | Implementation |
|---|---|---|
| D2 | Pending image flow | POST uploads to pending_*_path, PATCH applies to URL |
| D5 | Manual unfollow flag | planter_follows.is_manually_unfollowed prevents auto-refollow |
| D7 | ~~Mobile unfollow confirm~~ → 撤回 | 2026-04-30: 確認ダイアログ廃止、楽観更新で即時解除 |
| D8 | Timezone-aware contributions | Intl API → tz query param → server DATE() |
| D9 | Score > 0 filter | insight_score_events.score_delta > 0 for louge count |
| D10 | Fixed edit URL | /profile/edit (no user ID) |
| D11 | Similar users by tags | Common tag COUNT DESC, top 5 |
| D12 | SNS domain allowlist | Pydantic validators with domain check |
| D13 | Initial avatar | display_name[0] + ID-hash background color |
| D14 | Pillow MIME validation | Image.open() + verify() magic bytes |
| D15 | Safe image deletion | Upload → PATCH apply → delete old (log-only on failure) |
| D16 | BAN/deleted exclusion | Follower/following lists filter is_banned/deleted_at |
| D17 | Optimistic unfollow in modal | Immediate list removal, rollback on error |
| D18 | NULL-safe migration | All new columns NULL default |

## Addendum (2026-04-30): UI 拡張

| 範囲 | 変更内容 |
|---|---|
| BR-F06 / FC-13 | `components/planter/PlanterFollowButton.tsx` を新規追加。Seed/Louge 詳細ヘッダー（時刻の直後）にアウトラインスタイルで配置 |
| API | `PlanterResponse.is_following` を追加。`GET /planters/{id}` で認証ユーザーの follow 状態を返却 |
| Repository | `FollowRepository.is_following_planter` を追加（is_manually_unfollowed=true は False 扱い） |
| BR-N01 / FC-14 | ユーザー名を Link 化: `PlanterCard`（overlay link 技法でカード全体リンクと両立）/ `planter-detail-client` / `LogItem`（AI ログ除く）/ `ContributorsSidebar` |
| BR-N02 | `ProfileHeader` のアクションスロット: 既存実装（FollowButton が isOwnProfile で null、編集 Link が isOwnProfile 時のみ）が要件を満たすため変更なし。仕様としてドキュメント化 |
