import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.score import InsightScoreEvent
from app.models.seed_type import SeedType
from app.models.user import User


async def _setup_seed_type(db: AsyncSession) -> SeedType:
    st = SeedType(name="疑問", slug="query", description="test", sort_order=1)
    db.add(st)
    await db.flush()
    await db.refresh(st)
    return st


async def _setup_user(
    db: AsyncSession, auth_id: uuid.UUID, display_name: str = "Test User"
) -> User:
    user = User(auth_id=auth_id, display_name=display_name, insight_score=0.0)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _setup_bloomed_planter(
    db: AsyncSession, user: User, seed_type: SeedType
) -> Planter:
    planter = Planter(
        user_id=user.id,
        title="Bloomed Seed",
        body="Body text",
        seed_type_id=seed_type.id,
        status="louge",
        louge_content="# Test Article",
        progress=1.0,
    )
    db.add(planter)
    await db.flush()
    await db.refresh(planter)
    return planter


class TestContributorsEndpoint:
    async def test_get_contributors_success(
        self, client: AsyncClient, db_session: AsyncSession, mock_auth_user_sub
    ):
        """GET /planters/{id}/contributors should return contributors for a bloomed planter."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession as AS
        from app.database import get_db
        from app.main import app

        seed_type = await _setup_seed_type(db_session)
        seed_author = await _setup_user(db_session, mock_auth_user_sub, "Seed Author")
        contributor = await _setup_user(db_session, uuid.uuid4(), "Contributor")
        planter = await _setup_bloomed_planter(db_session, seed_author, seed_type)

        # Create insight score events
        events = [
            InsightScoreEvent(
                user_id=seed_author.id,
                planter_id=planter.id,
                log_id=None,
                score_delta=1.0,
                reason="seed_author",
            ),
            InsightScoreEvent(
                user_id=contributor.id,
                planter_id=planter.id,
                log_id=uuid.uuid4(),
                score_delta=0.85,
                reason="log_contribution",
            ),
        ]
        for e in events:
            db_session.add(e)

        # Create a log for contributor
        log = Log(
            planter_id=planter.id,
            user_id=contributor.id,
            body="Test log",
        )
        db_session.add(log)
        await db_session.commit()

        resp = await client.get(f"/api/v1/planters/{planter.id}/contributors")
        assert resp.status_code == 200

        data = resp.json()
        assert "contributors" in data
        assert len(data["contributors"]) == 2

        # Should be sorted by score descending
        assert data["contributors"][0]["insight_score_earned"] >= data["contributors"][1]["insight_score_earned"]

    async def test_get_contributors_not_bloomed(
        self, client: AsyncClient, db_session: AsyncSession, mock_auth_user_sub
    ):
        """GET /planters/{id}/contributors should return 404 for non-louge planters."""
        seed_type = await _setup_seed_type(db_session)
        user = await _setup_user(db_session, mock_auth_user_sub)
        planter = Planter(
            user_id=user.id,
            title="Not Bloomed",
            body="Body",
            seed_type_id=seed_type.id,
            status="sprout",
        )
        db_session.add(planter)
        await db_session.commit()
        await db_session.refresh(planter)

        resp = await client.get(f"/api/v1/planters/{planter.id}/contributors")
        assert resp.status_code == 404

    async def test_get_contributors_seed_author_flag(
        self, client: AsyncClient, db_session: AsyncSession, mock_auth_user_sub
    ):
        """Contributors response should mark seed author with is_seed_author=true."""
        seed_type = await _setup_seed_type(db_session)
        seed_author = await _setup_user(db_session, mock_auth_user_sub, "Author")
        planter = await _setup_bloomed_planter(db_session, seed_author, seed_type)

        event = InsightScoreEvent(
            user_id=seed_author.id,
            planter_id=planter.id,
            log_id=None,
            score_delta=1.0,
            reason="seed_author",
        )
        db_session.add(event)
        await db_session.commit()

        resp = await client.get(f"/api/v1/planters/{planter.id}/contributors")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["contributors"]) == 1
        assert data["contributors"][0]["is_seed_author"] is True
