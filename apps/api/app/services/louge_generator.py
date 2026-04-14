import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.vertex_ai_client import MODEL_STANDARD, VertexAIClient
from app.models.log import Log
from app.models.notification import Notification
from app.models.planter import Planter
from app.models.user import User
from app.repositories.log_repository import LogRepository
from app.repositories.planter_repository import PlanterRepository
from app.services.insight_calculator import InsightScoreCalculator

logger = logging.getLogger(__name__)

LOUGE_SYSTEM_INSTRUCTION = """\
あなたはビジネスナレッジの編纂者です。
Seed（問い）とLog（コメント群）から、パターンランゲージ形式のナレッジ記事を生成してください。

## 出力フォーマット（JSON）

{
  "pattern_name": "このノウハウに付ける名前",
  "context": "状況セクション（Markdown形式）",
  "problem": "問題セクション（Markdown形式）",
  "solution": "解決策セクション（Markdown形式）",
  "counterarguments": "反論・例外セクション（Markdown形式）",
  "references": [
    {"log_index": 1, "user_name": "@投稿者名", "excerpt": "引用スニペット（50文字程度）"}
  ]
}

## ルール
1. 本文中で出典を参照する場合は脚注番号 [1], [2] を使用してください
2. references の log_index は 1 から始まる通し番号です
3. 反論・例外セクションは必ず含めてください
4. 解決策は具体的かつ実行可能なレベルで記述してください
5. テーマや議論の性質に応じて最適な構成を判断してください（対立軸の整理、ステップバイステップ、チェックリスト等）
6. 全て日本語で記述してください"""


class LougeGenerator:
    def __init__(self) -> None:
        self.client = VertexAIClient(model_name=MODEL_STANDARD)

    async def generate(
        self,
        planter: Planter,
        logs: list[Log],
        users_map: dict[uuid.UUID, User],
    ) -> str | None:
        logs_text = self._build_logs_text(logs, users_map)
        prompt = (
            f"## Seed\nタイトル: {planter.title}\n本文: {planter.body}\n\n"
            f"## Log 一覧（投稿者情報付き）\n{logs_text}"
        )

        try:
            data = await self.client.generate_json(
                prompt, system_instruction=LOUGE_SYSTEM_INSTRUCTION
            )
            return self._build_markdown(data)
        except Exception:
            logger.error("Louge generation failed", exc_info=True)
            return None

    async def bloom(self, planter_id: uuid.UUID, db: AsyncSession) -> None:
        planter = await self._get_planter(planter_id, db)
        if planter is None:
            return

        logs, users_map = await self._get_logs_with_users(planter_id, db)

        content = await self.generate(planter, logs, users_map)
        if content is None:
            logger.warning("Louge generation failed for planter=%s, louge_content remains None", planter_id)
            return

        await self._update_louge_content(planter_id, content, db)

        calculator = InsightScoreCalculator()
        events = await calculator.calculate(planter_id, content, db)
        await calculator.apply(events, db)

        await self._create_notifications(planter_id, planter.user_id, logs, db)
        await db.commit()

    def _build_logs_text(
        self, logs: list[Log], users_map: dict[uuid.UUID, User]
    ) -> str:
        lines = []
        for i, log in enumerate(logs, 1):
            if log.is_ai_generated:
                continue
            if log.user_id and log.user_id in users_map:
                name = users_map[log.user_id].display_name
            else:
                name = "匿名"
            lines.append(f"{i}. @{name}: {log.body}")
        return "\n".join(lines)

    def _build_markdown(self, data: dict) -> str:
        sections = [
            f"# {data.get('pattern_name', 'パターン名')}",
            "",
            "## 状況（Context）",
            data.get("context", ""),
            "",
            "## 問題（Problem）",
            data.get("problem", ""),
            "",
            "## 解決策（Solution）",
            data.get("solution", ""),
            "",
            "## 反論・例外（Counterarguments）",
            data.get("counterarguments", ""),
            "",
            "---",
            "",
            "## 出典",
        ]

        references = data.get("references", [])
        for ref in references:
            idx = ref.get("log_index", "?")
            user = ref.get("user_name", "?")
            excerpt = ref.get("excerpt", "")
            sections.append(f"[{idx}] {user} - 「{excerpt}」")

        return "\n".join(sections)

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

    async def _update_louge_content(
        self, planter_id: uuid.UUID, content: str, db: AsyncSession
    ) -> None:
        repo = PlanterRepository(db)
        await repo.update_louge_content(
            planter_id, content, datetime.now(timezone.utc)
        )

    async def _create_notifications(
        self,
        planter_id: uuid.UUID,
        seed_author_id: uuid.UUID,
        logs: list[Log],
        db: AsyncSession,
    ) -> None:
        contributor_ids = {seed_author_id}
        for log in logs:
            if log.user_id and not log.is_ai_generated:
                contributor_ids.add(log.user_id)

        for user_id in contributor_ids:
            notification = Notification(
                user_id=user_id,
                type="louge_bloomed",
                planter_id=planter_id,
                actor_id=None,
            )
            db.add(notification)
        await db.flush()
