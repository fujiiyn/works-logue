from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_setting import AppSetting

SCORE_DEFAULTS = {
    "min_contributors": 3,
    "min_logs": 5,
    "bloom_threshold": 0.7,
    "bud_threshold": 0.8,
}

SCORE_KEYS = [f"score.{k}" for k in SCORE_DEFAULTS]


class SettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_score_settings(self) -> dict:
        result = await self.db.execute(
            select(AppSetting).where(AppSetting.key.in_(SCORE_KEYS))
        )
        rows = {r.key: r.value for r in result.scalars().all()}

        return {
            k: rows.get(f"score.{k}", v)
            for k, v in SCORE_DEFAULTS.items()
        }
