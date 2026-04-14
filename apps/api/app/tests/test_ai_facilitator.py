import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User
from app.services.ai_facilitator import AIFacilitator


@pytest.fixture
def mock_vertex_ai():
    with patch("app.services.ai_facilitator.VertexAIClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def facilitator(mock_vertex_ai):
    return AIFacilitator()


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(slug="query", name="疑問", description="テスト用", sort_order=1, is_active=True)
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
async def planter(db_session: AsyncSession, test_user: User, seed_type: SeedType) -> Planter:
    p = Planter(
        user_id=test_user.id, title="Test Seed", body="Test body", seed_type_id=seed_type.id
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


class TestGenerateFacilitation:
    async def test_generates_facilitation_text(self, facilitator, mock_vertex_ai):
        """generate_facilitation() should return facilitation text based on lowest score."""
        mock_vertex_ai.generate_json.return_value = {
            "facilitation": "反論や例外ケースについて、具体的な経験をお持ちの方はいますか？"
        }

        maturity_scores = {
            "comprehensiveness": 0.8,
            "diversity": 0.7,
            "counterarguments": 0.3,
            "specificity": 0.6,
        }

        result = await facilitator.generate_facilitation(
            seed_title="テスト",
            seed_body="本文",
            log_bodies=["ログ1", "ログ2"],
            maturity_scores=maturity_scores,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_facilitation_within_500_chars(self, facilitator, mock_vertex_ai):
        """generate_facilitation() should return text within 500 characters."""
        long_text = "あ" * 600
        mock_vertex_ai.generate_json.return_value = {"facilitation": long_text}

        maturity_scores = {
            "comprehensiveness": 0.5,
            "diversity": 0.5,
            "counterarguments": 0.5,
            "specificity": 0.5,
        }

        result = await facilitator.generate_facilitation(
            seed_title="テスト", seed_body="本文", log_bodies=["ログ1"], maturity_scores=maturity_scores
        )
        assert len(result) <= 500


class TestShouldFacilitate:
    async def test_should_facilitate_after_3_user_logs(
        self, facilitator, planter, test_user, db_session
    ):
        """should_facilitate() should return true when 3+ user logs since last AI log."""
        now = datetime.now(timezone.utc)

        # AI facilitation log
        ai_log = Log(
            planter_id=planter.id,
            user_id=None,
            body="AI facilitation",
            is_ai_generated=True,
            created_at=now,
        )
        db_session.add(ai_log)
        await db_session.commit()

        # 3 user logs after AI log
        for i in range(3):
            db_session.add(
                Log(
                    planter_id=planter.id,
                    user_id=test_user.id,
                    body=f"User log {i}",
                    is_ai_generated=False,
                    created_at=now + timedelta(seconds=i + 1),
                )
            )
        await db_session.commit()

        result = await facilitator.should_facilitate(planter.id, db_session)
        assert result is True

    async def test_should_not_facilitate_under_3_logs(
        self, facilitator, planter, test_user, db_session
    ):
        """should_facilitate() should return false when fewer than 3 user logs since last AI log."""
        now = datetime.now(timezone.utc)

        ai_log = Log(
            planter_id=planter.id,
            user_id=None,
            body="AI facilitation",
            is_ai_generated=True,
            created_at=now,
        )
        db_session.add(ai_log)
        await db_session.commit()

        # Only 2 user logs
        for i in range(2):
            db_session.add(
                Log(
                    planter_id=planter.id,
                    user_id=test_user.id,
                    body=f"User log {i}",
                    is_ai_generated=False,
                    created_at=now + timedelta(seconds=i + 1),
                )
            )
        await db_session.commit()

        result = await facilitator.should_facilitate(planter.id, db_session)
        assert result is False

    async def test_should_facilitate_first_time(
        self, facilitator, planter, test_user, db_session
    ):
        """should_facilitate() should return true when no prior AI logs exist."""
        for i in range(3):
            db_session.add(
                Log(
                    planter_id=planter.id,
                    user_id=test_user.id,
                    body=f"User log {i}",
                    is_ai_generated=False,
                )
            )
        await db_session.commit()

        result = await facilitator.should_facilitate(planter.id, db_session)
        assert result is True
