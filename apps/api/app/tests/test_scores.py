import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.score import LougeScoreSnapshot
from app.models.seed_type import SeedType
from app.models.user import User


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(
        slug="query", name="疑問", description="疑問", sort_order=1, is_active=True
    )
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def test_user(db_session: AsyncSession, mock_auth_user_sub) -> User:
    user = User(auth_id=mock_auth_user_sub, display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def planter(db_session: AsyncSession, test_user, seed_type) -> Planter:
    p = Planter(
        user_id=test_user.id,
        title="Test Seed",
        body="Body",
        seed_type_id=seed_type.id,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


class TestGetPlanterScore:
    """GET /api/v1/planters/{planter_id}/score"""

    async def test_score_no_snapshot_no_logs(self, client: AsyncClient, planter):
        """Snapshotなし + Logなし → score_pending=false"""
        resp = await client.get(f"/api/v1/planters/{planter.id}/score")
        assert resp.status_code == 200
        data = resp.json()
        assert data["score_pending"] is False
        assert data["last_scored_at"] is None
        assert data["score"]["id"] == str(planter.id)
        assert data["score"]["log_count"] == 0

    async def test_score_no_snapshot_with_logs(
        self, client: AsyncClient, planter, db_session: AsyncSession, test_user
    ):
        """Snapshotなし + Logあり → score_pending=true"""
        log = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="A log",
            is_ai_generated=False,
        )
        db_session.add(log)
        await db_session.commit()

        resp = await client.get(f"/api/v1/planters/{planter.id}/score")
        assert resp.status_code == 200
        data = resp.json()
        assert data["score_pending"] is True

    async def test_score_with_snapshot_no_new_logs(
        self, client: AsyncClient, planter, db_session: AsyncSession, test_user
    ):
        """Snapshotあり + 新Logなし → score_pending=false"""
        log = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Trigger log",
            is_ai_generated=False,
        )
        db_session.add(log)
        await db_session.flush()
        await db_session.refresh(log)

        snapshot = LougeScoreSnapshot(
            planter_id=planter.id,
            trigger_log_id=log.id,
            structure_fulfillment=0.5,
            structure_parts={"context": True, "problem": True, "solution": False, "name": False},
            passed_structure=False,
        )
        db_session.add(snapshot)
        await db_session.commit()

        resp = await client.get(f"/api/v1/planters/{planter.id}/score")
        assert resp.status_code == 200
        data = resp.json()
        assert data["score_pending"] is False
        assert data["last_scored_at"] is not None
        assert data["score"]["structure_parts"]["context"] is True
        assert data["score"]["structure_parts"]["solution"] is False

    async def test_score_planter_not_found(self, client: AsyncClient):
        """存在しないPlanter: 404"""
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/planters/{fake_id}/score")
        assert resp.status_code == 404

    async def test_score_returns_full_response(
        self, client: AsyncClient, planter
    ):
        """レスポンスに必要なフィールドが全て含まれる"""
        resp = await client.get(f"/api/v1/planters/{planter.id}/score")
        assert resp.status_code == 200
        data = resp.json()
        score = data["score"]
        assert "id" in score
        assert "status" in score
        assert "log_count" in score
        assert "contributor_count" in score
        assert "progress" in score
        assert "structure_fulfillment" in score
        assert "maturity_score" in score
        assert "structure_parts" in score


class TestGetScoreSettings:
    """GET /api/v1/settings/score"""

    async def test_settings_defaults(self, client: AsyncClient):
        """DB設定なしでデフォルト値が返る"""
        resp = await client.get("/api/v1/settings/score")
        assert resp.status_code == 200
        data = resp.json()
        assert data["min_contributors"] == 3
        assert data["min_logs"] == 5
        assert data["bloom_threshold"] == 0.7
        assert data["bud_threshold"] == 0.8

    async def test_settings_response_shape(self, client: AsyncClient):
        """レスポンスフィールドが正しい"""
        resp = await client.get("/api/v1/settings/score")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {
            "min_contributors",
            "min_logs",
            "bloom_threshold",
            "bud_threshold",
        }
