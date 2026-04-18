import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.planter_view import PlanterView
from app.models.seed_type import SeedType
from app.models.tag import PlanterTag, Tag
from app.models.user import User
from app.repositories.planter_repository import PlanterRepository


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="desc", sort_order=1, is_active=True)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(auth_id=uuid.uuid4(), display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def repo(db_session: AsyncSession) -> PlanterRepository:
    return PlanterRepository(db_session)


async def _create_planter(
    db: AsyncSession,
    user: User,
    seed_type: SeedType,
    *,
    title: str = "Test",
    status: str = "seed",
    created_at: datetime | None = None,
    louge_generated_at: datetime | None = None,
    structure_fulfillment: float = 0.0,
) -> Planter:
    p = Planter(
        user_id=user.id,
        title=title,
        body="Body",
        seed_type_id=seed_type.id,
        status=status,
        structure_fulfillment=structure_fulfillment,
    )
    if created_at:
        p.created_at = created_at
    if louge_generated_at:
        p.louge_generated_at = louge_generated_at
        p.louge_content = "# Generated Article"
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


class TestListTrendingCandidates:
    async def test_returns_recent_active_planters(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        # Recent planter
        p1 = await _create_planter(db_session, test_user, seed_type, title="Recent", created_at=now - timedelta(days=1))
        # Old planter (outside window)
        await _create_planter(db_session, test_user, seed_type, title="Old", created_at=now - timedelta(days=30))

        results = await repo.list_trending_candidates(window_days=7, limit=10)
        titles = [r.title for r in results]
        assert "Recent" in titles
        assert "Old" not in titles

    async def test_includes_planter_with_recent_log(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        # Old planter but with recent log activity
        p = await _create_planter(db_session, test_user, seed_type, title="OldWithLog", created_at=now - timedelta(days=30))
        log = Log(planter_id=p.id, user_id=test_user.id, body="Recent log", created_at=now - timedelta(hours=1))
        db_session.add(log)
        await db_session.commit()

        results = await repo.list_trending_candidates(window_days=7, limit=10)
        titles = [r.title for r in results]
        assert "OldWithLog" in titles

    async def test_excludes_archived(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        await _create_planter(db_session, test_user, seed_type, title="Archived", status="archived", created_at=now)

        results = await repo.list_trending_candidates(window_days=7, limit=10)
        assert len(results) == 0


class TestListBloomed:
    async def test_returns_louge_only(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        await _create_planter(db_session, test_user, seed_type, title="Seed", status="seed")
        await _create_planter(
            db_session, test_user, seed_type,
            title="Louge", status="louge", louge_generated_at=now,
        )

        results = await repo.list_bloomed(limit=10)
        assert len(results) == 1
        assert results[0].title == "Louge"

    async def test_ordered_by_louge_generated_at_desc(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        await _create_planter(
            db_session, test_user, seed_type,
            title="Older", status="louge", louge_generated_at=now - timedelta(days=1),
        )
        await _create_planter(
            db_session, test_user, seed_type,
            title="Newer", status="louge", louge_generated_at=now,
        )

        results = await repo.list_bloomed(limit=10)
        assert results[0].title == "Newer"
        assert results[1].title == "Older"


class TestSearch:
    async def test_keyword_filter(self, repo, test_user, seed_type, db_session):
        await _create_planter(db_session, test_user, seed_type, title="人事評価の悩み")
        await _create_planter(db_session, test_user, seed_type, title="マーケティング施策")

        results = await repo.search(keyword="人事", limit=10)
        assert len(results) == 1
        assert results[0].title == "人事評価の悩み"

    async def test_tag_filter(self, repo, test_user, seed_type, db_session):
        tag = Tag(name="IT", category="industry", is_leaf=True, is_active=True)
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        p1 = await _create_planter(db_session, test_user, seed_type, title="With tag")
        await _create_planter(db_session, test_user, seed_type, title="Without tag")

        pt = PlanterTag(planter_id=p1.id, tag_id=tag.id)
        db_session.add(pt)
        await db_session.commit()

        results = await repo.search(tag_ids=[tag.id], limit=10)
        assert len(results) == 1
        assert results[0].title == "With tag"

    async def test_status_filter(self, repo, test_user, seed_type, db_session):
        await _create_planter(db_session, test_user, seed_type, title="Seed", status="seed")
        await _create_planter(db_session, test_user, seed_type, title="Sprout", status="sprout")

        results = await repo.search(status="sprout", limit=10)
        assert len(results) == 1
        assert results[0].title == "Sprout"

    async def test_combined_filters(self, repo, test_user, seed_type, db_session):
        tag = Tag(name="HR", category="occupation", is_leaf=True, is_active=True)
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)

        p1 = await _create_planter(db_session, test_user, seed_type, title="人事の悩み", status="sprout")
        p2 = await _create_planter(db_session, test_user, seed_type, title="人事の種", status="seed")
        pt1 = PlanterTag(planter_id=p1.id, tag_id=tag.id)
        pt2 = PlanterTag(planter_id=p2.id, tag_id=tag.id)
        db_session.add_all([pt1, pt2])
        await db_session.commit()

        results = await repo.search(keyword="人事", tag_ids=[tag.id], status="sprout", limit=10)
        assert len(results) == 1
        assert results[0].title == "人事の悩み"

    async def test_no_filters_returns_all(self, repo, test_user, seed_type, db_session):
        await _create_planter(db_session, test_user, seed_type, title="A")
        await _create_planter(db_session, test_user, seed_type, title="B")

        results = await repo.search(limit=10)
        assert len(results) == 2

    async def test_cursor_pagination(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        for i in range(5):
            await _create_planter(
                db_session, test_user, seed_type,
                title=f"Item {i}", created_at=now + timedelta(seconds=i),
            )

        page1 = await repo.search(limit=3)
        assert len(page1) == 3
        assert page1[0].title == "Item 4"

        last = page1[-1]
        page2 = await repo.search(limit=3, cursor_created_at=last.created_at, cursor_id=last.id)
        assert len(page2) == 2


class TestGetViewCounts:
    async def test_counts_views(self, repo, test_user, seed_type, db_session):
        now = datetime.now(timezone.utc)
        p = await _create_planter(db_session, test_user, seed_type, title="Viewed")

        user2 = User(auth_id=uuid.uuid4(), display_name="User 2")
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)

        for user in [test_user, user2]:
            view = PlanterView(planter_id=p.id, user_id=user.id, viewed_at=now)
            db_session.add(view)
        await db_session.commit()

        counts = await repo.get_view_counts([p.id], since=now - timedelta(days=7))
        assert counts[p.id] == 2

    async def test_no_views_returns_zero(self, repo, test_user, seed_type, db_session):
        p = await _create_planter(db_session, test_user, seed_type, title="NoViews")
        now = datetime.now(timezone.utc)

        counts = await repo.get_view_counts([p.id], since=now - timedelta(days=7))
        assert counts.get(p.id, 0) == 0


class TestRecordView:
    async def test_record_view_logged_in(self, repo, test_user, seed_type, db_session):
        p = await _create_planter(db_session, test_user, seed_type, title="ToView")

        await repo.record_view(p.id, user_id=test_user.id, ip_address="1.2.3.4")
        await db_session.commit()

        now = datetime.now(timezone.utc)
        counts = await repo.get_view_counts([p.id], since=now - timedelta(days=1))
        assert counts[p.id] == 1

    async def test_upsert_existing_logged_in_view(self, repo, test_user, seed_type, db_session):
        p = await _create_planter(db_session, test_user, seed_type, title="ReView")

        await repo.record_view(p.id, user_id=test_user.id)
        await db_session.commit()
        await repo.record_view(p.id, user_id=test_user.id)
        await db_session.commit()

        now = datetime.now(timezone.utc)
        counts = await repo.get_view_counts([p.id], since=now - timedelta(days=1))
        assert counts[p.id] == 1

    async def test_record_anonymous_view(self, repo, test_user, seed_type, db_session):
        p = await _create_planter(db_session, test_user, seed_type, title="AnonView")

        await repo.record_view(p.id, ip_address="10.0.0.1")
        await db_session.commit()

        now = datetime.now(timezone.utc)
        counts = await repo.get_view_counts([p.id], since=now - timedelta(days=1))
        assert counts[p.id] == 1

    async def test_anonymous_dedup_within_window(self, repo, test_user, seed_type, db_session):
        p = await _create_planter(db_session, test_user, seed_type, title="DedupView")

        await repo.record_view(p.id, ip_address="10.0.0.2")
        await db_session.commit()
        # Same IP within 10 min → should not create new record
        await repo.record_view(p.id, ip_address="10.0.0.2")
        await db_session.commit()

        now = datetime.now(timezone.utc)
        counts = await repo.get_view_counts([p.id], since=now - timedelta(days=1))
        assert counts[p.id] == 1

    async def test_anonymous_different_ips_count_separately(self, repo, test_user, seed_type, db_session):
        p = await _create_planter(db_session, test_user, seed_type, title="MultiIP")

        await repo.record_view(p.id, ip_address="10.0.0.3")
        await db_session.commit()
        await repo.record_view(p.id, ip_address="10.0.0.4")
        await db_session.commit()

        now = datetime.now(timezone.utc)
        counts = await repo.get_view_counts([p.id], since=now - timedelta(days=1))
        assert counts[p.id] == 2
