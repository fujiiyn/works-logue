import logging
import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.vertex_ai_client import VertexAIClient
from app.models.log import Log

logger = logging.getLogger(__name__)

FACILITATION_SYSTEM_INSTRUCTION = """\
あなたはビジネスナレッジの共創を促進するファシリテーターです。
議論の成熟度が低い観点を補強するための問いかけを1つ生成してください。

ルール:
- 500文字以内で簡潔に
- 具体的な経験や事例を引き出す問いかけにする
- 丁寧語で、参加者に敬意を持った口調にする

出力形式（JSONのみ）:
{"facilitation": "問いかけのテキスト"}"""

ASPECT_LABELS = {
    "comprehensiveness": "網羅度（原因・対策・予防策の俯瞰）",
    "diversity": "多様性（異なる背景からの視点）",
    "counterarguments": "反論/例外（逆効果のケースや例外）",
    "specificity": "具体性（明日から実行可能なアクション）",
}


class AIFacilitator:
    def __init__(self) -> None:
        self.client = VertexAIClient()

    async def generate_facilitation(
        self,
        seed_title: str,
        seed_body: str,
        log_bodies: list[str],
        maturity_scores: dict[str, float],
    ) -> str:
        # Find the weakest aspect
        weakest = min(maturity_scores, key=maturity_scores.get)  # type: ignore[arg-type]
        weakest_label = ASPECT_LABELS.get(weakest, weakest)

        logs_text = "\n".join(f"- {body}" for body in log_bodies)
        prompt = (
            f"## Seed\nタイトル: {seed_title}\n本文: {seed_body}\n\n"
            f"## Log 一覧\n{logs_text}\n\n"
            f"## 最もスコアが低い観点\n{weakest_label}（スコア: {maturity_scores[weakest]:.2f}）\n\n"
            f"この観点を補強する問いかけを生成してください。"
        )

        try:
            data = await self.client.generate_json(
                prompt, system_instruction=FACILITATION_SYSTEM_INSTRUCTION
            )
            text = str(data.get("facilitation", ""))
        except Exception:
            logger.warning("Facilitation generation failed", exc_info=True)
            return ""

        return text[:500]

    async def should_facilitate(
        self, planter_id: uuid.UUID, db: AsyncSession
    ) -> bool:
        # Find the latest AI-generated log for this planter
        latest_ai_log = await db.execute(
            select(Log)
            .where(
                Log.planter_id == planter_id,
                Log.is_ai_generated.is_(True),
                Log.deleted_at.is_(None),
            )
            .order_by(Log.created_at.desc())
            .limit(1)
        )
        ai_log = latest_ai_log.scalar_one_or_none()

        # Count user logs since the last AI log (or all user logs if no AI log exists)
        conditions = [
            Log.planter_id == planter_id,
            Log.deleted_at.is_(None),
            Log.user_id.is_not(None),
            Log.is_ai_generated.is_(False),
        ]
        if ai_log is not None:
            conditions.append(Log.created_at > ai_log.created_at)

        result = await db.execute(
            select(func.count()).select_from(Log).where(and_(*conditions))
        )
        user_log_count = result.scalar_one()

        return user_log_count >= 3
