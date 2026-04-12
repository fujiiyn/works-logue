# U2 Seed -- Code Summary

## Created Files

### Backend (apps/api/)

| File | Purpose |
|---|---|
| `app/repositories/__init__.py` | Repository layer package |
| `app/repositories/planter_repository.py` | PlanterRepository (create, get_by_id, list_recent) |
| `app/repositories/tag_repository.py` | TagRepository (list_by_category, get_by_ids, attach_to_planter, replace_user_tags) |
| `app/repositories/follow_repository.py` | FollowRepository (follow_planter) |
| `app/routers/planters.py` | POST/GET /api/v1/planters, GET /api/v1/planters/{id} |
| `app/routers/seed_types.py` | GET /api/v1/seed-types |
| `app/routers/tags.py` | GET /api/v1/tags + build_tree() |
| `app/schemas/planter.py` | PlanterCreateRequest, PlanterResponse, PlanterCardResponse, CursorPaginatedResponse |
| `app/schemas/seed_type.py` | SeedTypeResponse |
| `app/schemas/tag.py` | TagResponse, TagTreeNode |
| `app/tests/test_planter_repository.py` | 8 tests |
| `app/tests/test_tag_repository.py` | 6 tests |
| `app/tests/test_follow_repository.py` | 2 tests |
| `app/tests/test_planters.py` | 16 tests |
| `app/tests/test_seed_types.py` | 3 tests |
| `app/tests/test_tags.py` | 4 tests |

### Updated Backend Files

| File | Changes |
|---|---|
| `app/models/user.py` | Added `onboarded_at` column, Python-side defaults |
| `app/models/planter.py` | Added Python-side defaults for SQLite test compatibility |
| `app/models/seed_type.py` | Added Python-side defaults |
| `app/models/tag.py` | Added Python-side defaults |
| `app/routers/users.py` | Extended PATCH /users/me with tag_ids, complete_onboarding |
| `app/schemas/user.py` | Added onboarded_at to UserResponse, tag_ids/complete_onboarding to UserUpdate |
| `app/main.py` | Registered planters, seed_types, tags routers |
| `app/tests/conftest.py` | Added _adapt_schema_for_sqlite() for JSONB/UUID compatibility |
| `app/tests/test_users.py` | Added 4 onboarding tests |

### Database

| File | Purpose |
|---|---|
| `supabase/migrations/00004_add_onboarded_at.sql` | ALTER TABLE users ADD COLUMN onboarded_at |

### Frontend (apps/web/)

| File | Purpose |
|---|---|
| `components/planter/ProgressBar.tsx` | FC-11: Progress bar (3px track, status-based fill) |
| `components/planter/PlanterCard.tsx` | FC-05: Feed card with badge, meta, title, tags, stats |
| `components/planter/PlanterFeed.tsx` | FC-06: Infinite scroll feed with tabs |
| `components/common/TagSelector.tsx` | FC-10: 6-tab hierarchical tree selector |
| `components/seed/SeedForm.tsx` | FC-08: Seed creation form |
| `lib/format-time.ts` | Relative time formatter |
| `app/page.tsx` | Updated: placeholder -> PlanterFeed |
| `app/seed/new/page.tsx` | /seed/new page with auth guard |
| `app/p/[id]/page.tsx` | Planter detail (Server Component) |
| `app/p/[id]/planter-detail-client.tsx` | Planter detail client component |
| `app/onboarding/page.tsx` | Onboarding page |
| `contexts/auth-context.tsx` | Updated: onboarded_at + redirect logic |

## API Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /api/v1/planters | Required | Create Seed (Planter) |
| GET | /api/v1/planters | Optional | List feed (cursor pagination) |
| GET | /api/v1/planters/{id} | Optional | Get planter detail |
| GET | /api/v1/seed-types | None | List active seed types |
| GET | /api/v1/tags | None | Get tag tree (optional category filter) |
| PATCH | /api/v1/users/me | Required | Update profile + onboarding |

## Test Coverage

- **62 tests total** (all passing)
- Repository: 17 tests (PlanterRepo 8, TagRepo 6, FollowRepo 2, conftest improvements)
- Endpoints: 39 tests (Planters 16, SeedTypes 3, Tags 4, Users 10, Auth 6)
- Frontend: Playwright E2E planned for Build & Test phase
