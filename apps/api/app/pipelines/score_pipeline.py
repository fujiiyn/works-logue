import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.log import Log
from app.models.planter import Planter
from app.models.score import LougeScoreSnapshot
from app.models.user import User
from app.repositories.log_repository import LogRepository
from app.repositories.planter_repository import PlanterRepository
from app.repositories.score_repository import ScoreRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.ai_facilitator import AIFacilitator
from app.services.score_engine import ScoreEngine

logger = logging.getLogger(__name__)


def calculate_progress(structure_fulfillment: float, maturity_total: float | None) -> float:
    structure_progress = min(structure_fulfillment * 0.5, 0.5)
    if maturity_total is not None:
        maturity_progress = min(maturity_total * 0.5, 0.5)
    else:
        maturity_progress = 0.0
    return structure_progress + maturity_progress


class ScorePipeline:
    def __init__(self, session_factory: async_sessionmaker | None = None) -> None:
        self.session_factory = session_factory
        self.score_engine = ScoreEngine()
        self.facilitator = AIFacilitator()

    async def execute(
        self,
        planter_id: uuid.UUID,
        trigger_log_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        try:
            await self._execute_inner(planter_id, trigger_log_id, db)
        except Exception:
            logger.error(
                "ScorePipeline failed for planter=%s", planter_id, exc_info=True
            )

    async def _execute_inner(
        self,
        planter_id: uuid.UUID,
        trigger_log_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        planter = await self._get_planter(planter_id, db)
        if planter is None:
            return

        settings = await self._get_settings(db)
        logs, users_map = await self._get_logs_with_users(planter_id, db)

        log_bodies = [log.body for log in logs]

        # Condition A: Structure evaluation (always runs)
        structure = await self.score_engine.evaluate_structure(
            planter.title, planter.body, log_bodies
        )

        # Condition B: Maturity evaluation (only if thresholds met)
        maturity_result = None
        passed_maturity = None
        should_run_b = (
            structure.fulfillment == 1.0
            and planter.contributor_count >= settings["min_contributors"]
            and planter.log_count >= settings["min_logs"]
        )

        if should_run_b:
            logs_with_users = []
            for log in logs:
                if log.user_id and log.user_id in users_map:
                    logs_with_users.append(
                        f"{users_map[log.user_id].display_name}: {log.body}"
                    )
                else:
                    logs_with_users.append(f"AI アシスタント: {log.body}")

            maturity_result = await self.score_engine.evaluate_maturity(
                planter.title, planter.body, logs_with_users
            )
            passed_maturity = maturity_result.total >= settings["bloom_threshold"]

            # AI Facilitation (when maturity below threshold)
            if not passed_maturity:
                should_fac = await self.facilitator.should_facilitate(planter_id, db)
                if should_fac:
                    text = await self.facilitator.generate_facilitation(
                        seed_title=planter.title,
                        seed_body=planter.body,
                        log_bodies=log_bodies,
                        maturity_scores=maturity_result.scores,
                    )
                    if text:
                        await self._create_ai_log(planter_id, text, db)

        # Calculate progress
        maturity_total = maturity_result.total if maturity_result else None
        progress = calculate_progress(structure.fulfillment, maturity_total)

        # Save snapshot
        snapshot = LougeScoreSnapshot(
            planter_id=planter_id,
            trigger_log_id=trigger_log_id,
            structure_fulfillment=structure.fulfillment,
            structure_parts=structure.parts,
            maturity_scores=maturity_result.scores if maturity_result else None,
            maturity_total=maturity_total,
            passed_structure=structure.fulfillment == 1.0,
            passed_maturity=passed_maturity,
        )
        await self._save_snapshot(db, snapshot)

        # Update planter
        await self._update_planter(
            db,
            planter_id,
            structure_fulfillment=structure.fulfillment,
            maturity_score=maturity_total,
            progress=progress,
            status=planter.status,
        )

        await db.commit()

    async def _get_planter(
        self, planter_id: uuid.UUID, db: AsyncSession
    ) -> Planter | None:
        repo = PlanterRepository(db)
        return await repo.get_by_id(planter_id)

    async def _get_logs_with_users(
        self, planter_id: uuid.UUID, db: AsyncSession
    ) -> tuple[list[Log], dict[uuid.UUID, User]]:
        log_repo = LogRepository(db)
        logs = await log_repo.get_all_by_planter(planter_id)

        user_ids = list({log.user_id for log in logs if log.user_id})
        users_map: dict[uuid.UUID, User] = {}
        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_map = {u.id: u for u in result.scalars().all()}

        return logs, users_map

    async def _get_settings(self, db: AsyncSession) -> dict:
        repo = SettingsRepository(db)
        return await repo.get_score_settings()

    async def _save_snapshot(
        self, db: AsyncSession, snapshot: LougeScoreSnapshot
    ) -> None:
        repo = ScoreRepository(db)
        await repo.create_snapshot(snapshot)

    async def _update_planter(
        self,
        db: AsyncSession,
        planter_id: uuid.UUID,
        *,
        structure_fulfillment: float,
        maturity_score: float | None,
        progress: float,
        status: str,
    ) -> None:
        repo = PlanterRepository(db)
        await repo.update_scores(
            planter_id,
            structure_fulfillment=structure_fulfillment,
            maturity_score=maturity_score,
            progress=progress,
            status=status,
        )

    async def _create_ai_log(
        self, planter_id: uuid.UUID, body: str, db: AsyncSession
    ) -> None:
        log_repo = LogRepository(db)
        ai_log = Log(
            planter_id=planter_id,
            user_id=None,
            body=body,
            is_ai_generated=True,
        )
        await log_repo.create(ai_log)
