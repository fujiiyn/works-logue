import json
import logging

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_location,
        )
    return _client


MODEL_LITE = "gemini-2.5-flash-lite"  # 条件A（構造パーツ判定）: 毎回実行・軽量
MODEL_STANDARD = "gemini-2.5-flash"  # 条件B（成熟度スコア）/ AIファシリテート


class VertexAIClient:
    def __init__(self, model_name: str = MODEL_STANDARD) -> None:
        self.client = _get_client()
        self.model_name = model_name

    async def generate_json(
        self, prompt: str, system_instruction: str | None = None
    ) -> dict:
        config: dict = {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        }
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        text = response.text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error("Failed to parse Vertex AI response as JSON: %s", text)
            raise
