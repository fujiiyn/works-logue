import logging
import uuid
from collections import defaultdict

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.vertex_ai_client import MODEL_STANDARD, VertexAIClient
from app.models.planter import Planter
from app.models.score import InsightScoreEvent
from app.models.user import User
from app.repositories.log_repository import LogRepository
from app.repositories.planter_repository import PlanterRepository

logger = logging.getLogger(__name__)

INSIGHT_SYSTEM_INSTRUCTION = """\
あなたはビジネスナレッジの貢献度評価の専門家です。
生成された Louge 記事と、それの元となった各 Log を比較し、
各 Log が Louge 記事にどの程度貢献したかを 0.0〜1.0 のスコアで評価してください。

評価基準:
- 0.8〜1.0: 記事の核心的な解決策やインサイトを提供した
- 0.5〜0.7: 記事の補足情報や具体例を提供した
- 0.2〜0.4: 間接的に記事の方向性に影響を与えた
- 0.0〜0.1: ほとんど記事に反映されなかった

出力形式（JSONのみ）:
{
  "evaluations": [
    {"log_id": "UUID文字列", "score": 0.0〜1.0, "reason": "評価理由（20文字以内）"}
  ]
}"""

FALLBACK_SCORE = 0.5


class InsightScoreCalculator:
    def __init__(self) -> None:
        self.client = VertexAIClient(model_name=MODEL_STANDARD)

    async def calculate(
        self,
        planter_id: uuid.UUID,
        louge_content: str,
        db: AsyncSession,
    ) -> list[InsightScoreEvent]:
        planter = await self._get_planter(planter_id, db)
        if planter is None:
            return []

        logs = await self._get_logs(planter_id, db)
        user_logs = [log for log in logs if not log.is_ai_generated]

        events: list[InsightScoreEvent] = []

        if user_logs:
            scores = await self._evaluate_contributions(louge_content, user_logs)
            for log in user_logs:
                score = scores.get(str(log.id), FALLBACK_SCORE)
                events.append(
                    InsightScoreEvent(
                        user_id=log.user_id,
                        planter_id=planter_id,
                        log_id=log.id,
                        score_delta=score,
                        reason="log_contribution",
                    )
                )

        # Seed author bonus
        events.append(
            InsightScoreEvent(
                user_id=planter.user_id,
                planter_id=planter_id,
                log_id=None,
                score_delta=1.0,
                reason="seed_author",
            )
        )

        return events

    async def apply(
        self, events: list[InsightScoreEvent], db: AsyncSession
    ) -> None:
        await self._save_events(events, db)

        user_deltas: dict[uuid.UUID, float] = defaultdict(float)
        for event in events:
            user_deltas[event.user_id] += event.score_delta

        await self._update_user_scores(user_deltas, db)

    async def _evaluate_contributions(
        self, louge_content: str, user_logs: list
    ) -> dict[str, float]:
        logs_text = "\n".join(
            f"- log_id={log.id}: {log.body[:200]}" for log in user_logs
        )
        prompt = (
            f"## Louge 記事\n{louge_content}\n\n"
            f"## 評価対象の Log 一覧\n{logs_text}"
        )

        try:
            data = await self.client.generate_json(
                prompt, system_instruction=INSIGHT_SYSTEM_INSTRUCTION
            )
            evaluations = data.get("evaluations", [])
            return {
                e["log_id"]: min(max(float(e.get("score", FALLBACK_SCORE)), 0.0), 1.0)
                for e in evaluations
                if "log_id" in e
            }
        except Exception:
            logger.warning("Insight score evaluation failed, using fallback", exc_info=True)
            return {str(log.id): FALLBACK_SCORE for log in user_logs}

    async def _get_planter(
        self, planter_id: uuid.UUID, db: AsyncSession
    ) -> Planter | None:
        repo = PlanterRepository(db)
        return await repo.get_by_id(planter_id)

    async def _get_logs(self, planter_id: uuid.UUID, db: AsyncSession) -> list:
        log_repo = LogRepository(db)
        return await log_repo.get_all_by_planter(planter_id)

    async def _save_events(
        self, events: list[InsightScoreEvent], db: AsyncSession
    ) -> None:
        for event in events:
            db.add(event)
        await db.flush()

    async def _update_user_scores(
        self, user_deltas: dict[uuid.UUID, float], db: AsyncSession
    ) -> None:
        for user_id, delta in user_deltas.items():
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(insight_score=User.insight_score + delta)
            )
        await db.flush()
