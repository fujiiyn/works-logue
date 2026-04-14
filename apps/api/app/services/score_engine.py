import logging
from dataclasses import dataclass

from app.infra.vertex_ai_client import MODEL_LITE, MODEL_STANDARD, VertexAIClient

logger = logging.getLogger(__name__)

STRUCTURE_PARTS = ["context", "problem", "solution", "name"]

STRUCTURE_SYSTEM_INSTRUCTION = """\
あなたはビジネスナレッジの構造分析の専門家です。
Seed（問い）とLog（コメント）群を分析し、ビジネスノウハウとしての構造パーツが揃っているかを判定してください。

判定する構造パーツ:
1. context（状況）: 具体的な前提条件や環境の説明があるか
2. problem（問題）: ジレンマや障害が明確に言語化されているか
3. solution（解決策）: 実行可能な具体的アクションが提示されているか
4. name（パターン名）: 上記3つが揃い、汎用ノウハウとして命名可能か

出力形式（JSONのみ）:
{"context": true/false, "problem": true/false, "solution": true/false, "name": true/false}"""

MATURITY_SYSTEM_INSTRUCTION = """\
あなたはビジネスナレッジの品質評価の専門家です。
Seed（問い）とLog（コメント）群の「集団知性」としての成熟度を4つの観点で評価してください。
各観点は 0.0〜1.0 のスコアで返してください。

評価観点:
1. comprehensiveness（網羅度）: 原因・対策・予防策など、テーマ全体を俯瞰できているか
2. diversity（多様性）: 異なる背景を持つ複数ユーザーの視点が含まれているか
3. counterarguments（反論/例外）: 「このケースでは逆効果」等の検証ログが含まれるか
4. specificity（具体性）: 明日から実行できるレベルのアクションが抽出可能か

出力形式（JSONのみ）:
{"comprehensiveness": 0.0〜1.0, "diversity": 0.0〜1.0, "counterarguments": 0.0〜1.0, "specificity": 0.0〜1.0}"""


@dataclass
class StructureResult:
    parts: dict[str, bool]
    fulfillment: float


@dataclass
class MaturityResult:
    scores: dict[str, float]
    total: float


class ScoreEngine:
    def __init__(self) -> None:
        self.lite_client = VertexAIClient(model_name=MODEL_LITE)
        self.standard_client = VertexAIClient(model_name=MODEL_STANDARD)

    async def evaluate_structure(
        self, seed_title: str, seed_body: str, log_bodies: list[str]
    ) -> StructureResult:
        logs_text = "\n".join(f"- {body}" for body in log_bodies)
        prompt = f"## Seed\nタイトル: {seed_title}\n本文: {seed_body}\n\n## Log 一覧\n{logs_text}"

        try:
            data = await self.lite_client.generate_json(
                prompt, system_instruction=STRUCTURE_SYSTEM_INSTRUCTION
            )
            parts = {k: bool(data.get(k, False)) for k in STRUCTURE_PARTS}
        except Exception:
            logger.warning("Structure evaluation failed, using fallback", exc_info=True)
            parts = {k: False for k in STRUCTURE_PARTS}

        fulfillment = sum(1 for v in parts.values() if v) / len(STRUCTURE_PARTS)
        return StructureResult(parts=parts, fulfillment=fulfillment)

    async def evaluate_maturity(
        self, seed_title: str, seed_body: str, logs_with_users: list[str]
    ) -> MaturityResult:
        logs_text = "\n".join(f"- {entry}" for entry in logs_with_users)
        prompt = f"## Seed\nタイトル: {seed_title}\n本文: {seed_body}\n\n## Log 一覧（投稿者情報付き）\n{logs_text}"

        maturity_keys = ["comprehensiveness", "diversity", "counterarguments", "specificity"]

        try:
            data = await self.standard_client.generate_json(
                prompt, system_instruction=MATURITY_SYSTEM_INSTRUCTION
            )
            scores = {k: float(data.get(k, 0.0)) for k in maturity_keys}
        except Exception:
            logger.warning("Maturity evaluation failed, using fallback", exc_info=True)
            scores = {k: 0.0 for k in maturity_keys}

        total = sum(scores.values()) / len(maturity_keys)
        return MaturityResult(scores=scores, total=total)
