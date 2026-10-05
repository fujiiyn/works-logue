import logging
import uuid
from dataclasses import dataclass
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


@dataclass(frozen=True)
class GeneratedLogue:
    content: str
    pattern_name: str


DEFAULT_PATTERN_NAME = "パターン名"

LOGUE_SYSTEM_INSTRUCTION = """\
あなたはビジネスナレッジの編纂者です。
Seed（問い）とLog（コメント群）から、パターンランゲージ形式のナレッジ記事を生成してください。

## 出力フォーマット（JSON）

{
  "pattern_name": "解決の本質を表すパターン名（下記「パターン名の付け方」に従う）",
  "context": "状況セクション（Markdown形式）",
  "problem": "問題セクション（Markdown形式）",
  "solution": "解決策セクション（Markdown形式）",
  "counterarguments": "反論・例外セクション（Markdown形式）",
  "references": [
    {"log_index": 1, "user_name": "@投稿者名", "excerpt": "引用スニペット（50文字程度）"}
  ]
}

## パターン名（pattern_name）の付け方
パターン名は、議論から導かれた解決策の考え方を、キャッチーな一言で表す名前です。
1. テーマの言い換えにしない。議論から導かれた解決の本質を名前にする
2. 短く、記憶に残る言葉にする（目安は15文字以内）
3. 他のパターンと並べたときに違いがわかる、このLogue固有の名前にする
4. 「〜の方法」「〜について」「〜のコツ」のような説明的な語尾を付けない
5. 命令形・禁止形にしない（例：「先に決めろ」→「先に決める」、「無理をするな」→「無理をしない」）
6. 「AよりB」の対比や、読点で区切る形を使ってよい

例:
- 悪い例（テーマ名）：「会議の生産性向上」
- 良い例（解決の本質）：「議論より、まず決める」「決めない会議は開かない」「報告は結論の一行から」

## ルール
1. 本文中で出典を参照する場合は脚注番号 [1], [2] を使用してください
2. references の log_index は 1 から始まる通し番号です
3. 反論・例外セクションは必ず含めてください
4. 解決策は具体的かつ実行可能なレベルで記述してください
5. テーマや議論の性質に応じて最適な構成を判断してください（対立軸の整理、ステップバイステップ、チェックリスト等）
6. 全て日本語で記述してください"""


class LogueGenerator:
    def __init__(self) -> None:
        self.client = VertexAIClient(model_name=MODEL_STANDARD)

    async def generate(
        self,
        planter: Planter,
        logs: list[Log],
        users_map: dict[uuid.UUID, User],
    ) -> GeneratedLogue | None:
        logs_text = self._build_logs_text(logs, users_map)
        prompt = (
            f"## Seed\nタイトル: {planter.title}\n本文: {planter.body}\n\n"
            f"## Log 一覧（投稿者情報付き）\n{logs_text}"
        )

        try:
            data = await self.client.generate_json(
                prompt, system_instruction=LOGUE_SYSTEM_INSTRUCTION
            )
            pattern_name = str(data.get("pattern_name") or "").strip() or DEFAULT_PATTERN_NAME
            return GeneratedLogue(
                content=self._build_markdown(data),
                pattern_name=pattern_name,
            )
        except Exception:
            logger.error("Logue generation failed", exc_info=True)
            return None

    async def bloom(self, planter_id: uuid.UUID, db: AsyncSession) -> None:
        planter = await self._get_planter(planter_id, db)
        if planter is None:
            return

        logs, users_map = await self._get_logs_with_users(planter_id, db)

        result = await self.generate(planter, logs, users_map)
        if result is None:
            logger.warning("Logue generation failed for planter=%s, logue_content remains None", planter_id)
            return

        await self._update_logue_content(
            planter_id, result.content, result.pattern_name, db
        )

        calculator = InsightScoreCalculator()
        events = await calculator.calculate(planter_id, result.content, db)
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

    async def _update_logue_content(
        self,
        planter_id: uuid.UUID,
        content: str,
        logue_title: str,
        db: AsyncSession,
    ) -> None:
        repo = PlanterRepository(db)
        await repo.update_logue_content(
            planter_id,
            content=content,
            logue_title=logue_title,
            generated_at=datetime.now(timezone.utc),
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
                type="logue_bloomed",
                planter_id=planter_id,
                actor_id=None,
            )
            db.add(notification)
        await db.flush()
