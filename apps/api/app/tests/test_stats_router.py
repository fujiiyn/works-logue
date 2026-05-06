import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="疑問を投稿", sort_order=1)
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


def _make_user(name: str) -> User:
    return User(auth_id=uuid.uuid4(), display_name=name)


class TestPublicStats:
    async def test_returns_zero_when_empty(self, client):
        resp = await client.get("/api/v1/stats")
        assert resp.status_code == 200
        assert resp.json() == {"seeds": 0, "louges": 0, "contributors": 0}

    async def test_no_authentication_required(self, client):
        resp = await client.get("/api/v1/stats")
        assert resp.status_code == 200

    async def test_counts_seeds_louges_contributors(
        self, client, db_session: AsyncSession, seed_type: SeedType
    ):
        u1 = _make_user("Alice")
        u2 = _make_user("Bob")
        u3 = _make_user("Carol")
        db_session.add_all([u1, u2, u3])
        await db_session.commit()
        for u in (u1, u2, u3):
            await db_session.refresh(u)

        # 3 planters total: 2 seed-status (one by u1, one by u2), 1 louge by u1
        p_seed_1 = Planter(
            user_id=u1.id, title="s1", body="b", seed_type_id=seed_type.id, status="seed"
        )
        p_seed_2 = Planter(
            user_id=u2.id, title="s2", body="b", seed_type_id=seed_type.id, status="sprout"
        )
        p_louge = Planter(
            user_id=u1.id,
            title="bloomed",
            body="b",
            seed_type_id=seed_type.id,
            status="louge",
            louge_content="generated",
            louge_generated_at=datetime.now(UTC),
        )
        # deleted planter must NOT count
        p_deleted = Planter(
            user_id=u1.id,
            title="gone",
            body="b",
            seed_type_id=seed_type.id,
            status="seed",
            deleted_at=datetime.now(UTC),
        )
        db_session.add_all([p_seed_1, p_seed_2, p_louge, p_deleted])
        await db_session.commit()
        for p in (p_seed_1, p_seed_2, p_louge):
            await db_session.refresh(p)

        # u3 contributes only via a Log (still counts as contributor).
        # is_hidden is set explicitly because SQLite (test backend) coerces
        # the string server_default "false" into Python True on readback.
        log_visible = Log(
            planter_id=p_seed_1.id, user_id=u3.id, body="hello", is_hidden=False
        )
        # hidden log must NOT promote a non-author to contributor
        u4 = _make_user("Dave")
        db_session.add(u4)
        await db_session.commit()
        await db_session.refresh(u4)
        log_hidden = Log(
            planter_id=p_seed_1.id,
            user_id=u4.id,
            body="hidden",
            is_hidden=True,
        )
        # deleted log must NOT promote a non-author to contributor
        u5 = _make_user("Eve")
        db_session.add(u5)
        await db_session.commit()
        await db_session.refresh(u5)
        log_deleted = Log(
            planter_id=p_seed_1.id,
            user_id=u5.id,
            body="deleted",
            is_hidden=False,
            deleted_at=datetime.now(UTC),
        )
        db_session.add_all([log_visible, log_hidden, log_deleted])
        await db_session.commit()

        resp = await client.get("/api/v1/stats")
        assert resp.status_code == 200
        body = resp.json()
        # seeds = non-deleted planters
        assert body["seeds"] == 3
        # louges = planters with status='louge'
        assert body["louges"] == 1
        # contributors = distinct (planter authors u1,u2) ∪ (visible-log authors u3) = 3
        assert body["contributors"] == 3
