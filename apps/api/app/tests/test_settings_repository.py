import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_setting import AppSetting
from app.repositories.settings_repository import SettingsRepository


@pytest.fixture
def repo(db_session: AsyncSession) -> SettingsRepository:
    return SettingsRepository(db_session)


class TestGetScoreSettings:
    async def test_get_score_settings_from_db(self, repo, db_session):
        """get_score_settings() should return values from the database."""
        settings = [
            AppSetting(key="score.min_contributors", value=5),
            AppSetting(key="score.min_logs", value=10),
            AppSetting(key="score.bloom_threshold", value=0.8),
            AppSetting(key="score.bud_threshold", value=0.9),
        ]
        db_session.add_all(settings)
        await db_session.commit()

        result = await repo.get_score_settings()
        assert result["min_contributors"] == 5
        assert result["min_logs"] == 10
        assert result["bloom_threshold"] == 0.8
        assert result["bud_threshold"] == 0.9

    async def test_get_score_settings_defaults(self, repo):
        """get_score_settings() should return defaults when DB has no settings."""
        result = await repo.get_score_settings()
        assert result["min_contributors"] == 3
        assert result["min_logs"] == 5
        assert result["bloom_threshold"] == 0.7
        assert result["bud_threshold"] == 0.8
