from unittest.mock import AsyncMock, patch

import pytest

from app.services.score_engine import ScoreEngine


@pytest.fixture
def mock_vertex_ai():
    with patch("app.services.score_engine.VertexAIClient") as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def engine(mock_vertex_ai):
    return ScoreEngine()


class TestEvaluateStructure:
    async def test_all_parts_fulfilled(self, engine, mock_vertex_ai):
        """evaluate_structure() should return fulfillment=1.0 when all parts are true."""
        mock_vertex_ai.generate_json.return_value = {
            "context": True,
            "problem": True,
            "solution": True,
            "name": True,
        }

        result = await engine.evaluate_structure(
            "人事施策の失敗", "評価制度を導入したら炎上した", ["うちも同じ", "解決策はこうだった"]
        )
        assert result.fulfillment == 1.0
        assert result.parts == {"context": True, "problem": True, "solution": True, "name": True}

    async def test_partial_fulfillment(self, engine, mock_vertex_ai):
        """evaluate_structure() should calculate correct fulfillment for partial parts."""
        mock_vertex_ai.generate_json.return_value = {
            "context": True,
            "problem": True,
            "solution": False,
            "name": False,
        }

        result = await engine.evaluate_structure("タイトル", "本文", ["ログ1"])
        assert result.fulfillment == 0.5
        assert result.parts["context"] is True
        assert result.parts["solution"] is False

    async def test_no_parts_fulfilled(self, engine, mock_vertex_ai):
        """evaluate_structure() should return fulfillment=0.0 when no parts are true."""
        mock_vertex_ai.generate_json.return_value = {
            "context": False,
            "problem": False,
            "solution": False,
            "name": False,
        }

        result = await engine.evaluate_structure("タイトル", "本文", ["ログ1"])
        assert result.fulfillment == 0.0

    async def test_parse_error_fallback(self, engine, mock_vertex_ai):
        """evaluate_structure() should return all-false fallback on parse error."""
        mock_vertex_ai.generate_json.side_effect = Exception("parse error")

        result = await engine.evaluate_structure("タイトル", "本文", ["ログ1"])
        assert result.fulfillment == 0.0
        assert result.parts == {"context": False, "problem": False, "solution": False, "name": False}


class TestEvaluateMaturity:
    async def test_normal_scores(self, engine, mock_vertex_ai):
        """evaluate_maturity() should return correct 4-aspect scores."""
        mock_vertex_ai.generate_json.return_value = {
            "comprehensiveness": 0.8,
            "diversity": 0.7,
            "counterarguments": 0.6,
            "specificity": 0.9,
        }

        result = await engine.evaluate_maturity(
            "タイトル", "本文", ["User1: ログ1", "User2: ログ2"]
        )
        assert result.scores["comprehensiveness"] == 0.8
        assert result.scores["diversity"] == 0.7
        assert result.scores["counterarguments"] == 0.6
        assert result.scores["specificity"] == 0.9

    async def test_total_is_average(self, engine, mock_vertex_ai):
        """evaluate_maturity() total should be the average of 4 aspects."""
        mock_vertex_ai.generate_json.return_value = {
            "comprehensiveness": 0.8,
            "diversity": 0.6,
            "counterarguments": 0.4,
            "specificity": 1.0,
        }

        result = await engine.evaluate_maturity("タイトル", "本文", ["ログ1"])
        assert result.total == pytest.approx(0.7)

    async def test_parse_error_fallback(self, engine, mock_vertex_ai):
        """evaluate_maturity() should return all-zero fallback on parse error."""
        mock_vertex_ai.generate_json.side_effect = Exception("parse error")

        result = await engine.evaluate_maturity("タイトル", "本文", ["ログ1"])
        assert result.total == 0.0
        assert all(v == 0.0 for v in result.scores.values())
