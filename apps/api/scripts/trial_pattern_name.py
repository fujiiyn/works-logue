"""既存 Logue に現在のプロンプトを当て、パターン名の候補を生成する（DB は読み取りのみ）。

使い方（apps/api で実行）:
    export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud-private/application_default_credentials.json
    uv run python scripts/trial_pattern_name.py "限られた時間での業務効率化" --runs 3
    uv run python scripts/trial_pattern_name.py --all --runs 3 --out /path/to/result.md

- DB 接続は `.env` / `.env.local` の DATABASE_URL を使う
- トランザクションを READ ONLY で開始し、最後にロールバックする。DB には一切書き込まない
- 本文も生成されるが、表示するのはパターン名だけ（--show-content で本文も表示）
"""

import argparse
import asyncio
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import or_, select, text  # noqa: E402

from app.database import async_session, engine  # noqa: E402
from app.models.log import Log  # noqa: E402
from app.models.planter import Planter  # noqa: E402
from app.models.user import User  # noqa: E402
from app.repositories.log_repository import LogRepository  # noqa: E402
from app.services.logue_generator import GeneratedLogue, LogueGenerator  # noqa: E402


@dataclass
class Target:
    planter: Planter
    logs: list[Log]
    users_map: dict[uuid.UUID, User]
    candidates: list[str] = field(default_factory=list)

    @property
    def human_log_count(self) -> int:
        return sum(1 for log in self.logs if not log.is_ai_generated)


async def load_targets(title: str | None) -> list[Target]:
    async with async_session() as db:
        await db.execute(text("SET TRANSACTION READ ONLY"))
        try:
            query = select(Planter).where(
                Planter.status == "logue",
                Planter.deleted_at.is_(None),
                Planter.logue_content.is_not(None),
            )
            if title is not None:
                query = query.where(or_(Planter.logue_title == title, Planter.title == title))
            result = await db.execute(query.order_by(Planter.logue_generated_at.asc()))
            planters = list(result.scalars().all())

            targets = []
            log_repo = LogRepository(db)
            for planter in planters:
                logs = await log_repo.get_all_by_planter(planter.id)
                user_ids = list({log.user_id for log in logs if log.user_id})
                users_map: dict[uuid.UUID, User] = {}
                if user_ids:
                    rows = await db.execute(select(User).where(User.id.in_(user_ids)))
                    users_map = {u.id: u for u in rows.scalars().all()}
                targets.append(Target(planter, logs, users_map))
            return targets
        finally:
            # rollback() expires loaded instances; detach them first so their
            # already-loaded attributes stay readable after the session ends.
            db.expunge_all()
            await db.rollback()


GENERATE_TIMEOUT_SEC = 120
GENERATE_ATTEMPTS = 3


async def generate_with_timeout(generator: LogueGenerator, t: Target) -> GeneratedLogue | None:
    # The Vertex AI call has no timeout of its own and has been observed to
    # hang indefinitely on an open connection. Bound each attempt and retry.
    for attempt in range(1, GENERATE_ATTEMPTS + 1):
        try:
            return await asyncio.wait_for(
                generator.generate(t.planter, t.logs, t.users_map),
                timeout=GENERATE_TIMEOUT_SEC,
            )
        except TimeoutError:
            print(f"  （{GENERATE_TIMEOUT_SEC} 秒で応答なし。やり直し {attempt}/{GENERATE_ATTEMPTS}）")
    return None


def to_markdown(targets: list[Target], runs: int) -> str:
    header = "| Seed タイトル | Log 数 | 現在のパターン名 | " + " | ".join(
        f"候補 {i}" for i in range(1, runs + 1)
    )
    lines = [header + " |", "|" + "---|" * (3 + runs)]
    for t in targets:
        cells = [t.planter.title, str(t.human_log_count), t.planter.logue_title or ""]
        cells += t.candidates + [""] * (runs - len(t.candidates))
        lines.append("| " + " | ".join(c.replace("|", "／") for c in cells) + " |")
    return "\n".join(lines) + "\n"


async def main(title: str | None, runs: int, show_content: bool, out: Path | None) -> int:
    targets = await load_targets(title)
    if title is not None and len(targets) != 1:
        print(f"対象の Logue が {len(targets)} 件見つかりました（1 件である必要があります）")
        for t in targets:
            print(f"  - {t.planter.id} / title={t.planter.title}")
        await engine.dispose()
        return 1

    generator = LogueGenerator()
    for t in targets:
        print(f"[{t.planter.id}] {t.planter.title}")
        print(f"  現在のパターン名: {t.planter.logue_title}（Log {t.human_log_count} 件）")
        for i in range(1, runs + 1):
            generated = await generate_with_timeout(generator, t)
            name = generated.pattern_name if generated else "（生成失敗）"
            t.candidates.append(name)
            print(f"  候補 {i}: {name}")
            if show_content and generated:
                print(generated.content)
        print()

    if out is not None:
        out.write_text(to_markdown(targets, runs), encoding="utf-8")
        print(f"書き出し: {out}")

    await engine.dispose()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", nargs="?", help="対象 Logue のパターン名または Seed タイトル")
    parser.add_argument("--all", action="store_true", help="開花済みの全 Logue を対象にする")
    parser.add_argument("--runs", type=int, default=3, help="1 件あたりの生成回数（既定 3）")
    parser.add_argument("--show-content", action="store_true", help="本文も表示する")
    parser.add_argument("--out", type=Path, help="結果を Markdown の表で書き出すパス")
    args = parser.parse_args()
    if args.all == (args.title is not None):
        parser.error("title か --all のどちらか一方を指定してください")
    sys.exit(asyncio.run(main(args.title, args.runs, args.show_content, args.out)))
