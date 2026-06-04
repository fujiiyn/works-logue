import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.score_engine import MaturityResult, StructureResult


def _make_planter_mock(
    planter_id=None,
    user_id=None,
    title="Test Seed",
    body="Test body",
    status="seed",
    logue_content=None,
):
    p = MagicMock()
    p.id = planter_id or uuid.uuid4()
    p.user_id = user_id or uuid.uuid4()
    p.title = title
    p.body = body
    p.status = status
    p.logue_content = logue_content
    return p


def _make_log_mock(body="Log body", user_id=None, is_ai_generated=False):
    log = MagicMock()
    log.id = uuid.uuid4()
    log.body = body
    log.user_id = user_id or uuid.uuid4()
    log.is_ai_generated = is_ai_generated
    return log


def _make_user_mock(user_id=None, display_name="Test User"):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.display_name = display_name
    return user


class TestLogueGeneratorGenerate:
    async def test_generate_returns_markdown(self):
        """generate() should call Vertex AI and return content + pattern_name."""
        from app.services.logue_generator import GeneratedLogue, LogueGenerator

        vertex_response = {
            "pattern_name": "0→1営業責任者の泥臭さ要件",
            "context": "新規事業立ち上げ時、予算ゼロの環境で...",
            "problem": "大手の看板が通じず、営業責任者の心が折れる...",
            "solution": "スタートアップ経験者を優先し...",
            "counterarguments": "ただし、大企業出身者が適する場合もある...",
            "references": [
                {"log_index": 1, "user_name": "@田中", "excerpt": "うちは3ヶ月の業務委託期間を..."},
                {"log_index": 2, "user_name": "@佐藤", "excerpt": "同様のアプローチで..."},
            ],
        }

        generator = LogueGenerator()

        with patch.object(generator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(return_value=vertex_response)

            planter = _make_planter_mock()
            logs = [_make_log_mock(body=f"Log {i}") for i in range(5)]
            users_map = {log.user_id: _make_user_mock(user_id=log.user_id) for log in logs}

            result = await generator.generate(planter, logs, users_map)

        assert isinstance(result, GeneratedLogue)
        assert result.pattern_name == "0→1営業責任者の泥臭さ要件"
        # Pattern name is now a first-class column, not an h1 inside the body.
        assert "# 0→1営業責任者の泥臭さ要件" not in result.content
        assert result.content.lstrip().startswith("## ")
        assert "## 状況（Context）" in result.content
        assert "## 問題（Problem）" in result.content
        assert "## 解決策（Solution）" in result.content
        assert "## 反論・例外（Counterarguments）" in result.content
        assert "## 出典" in result.content
        assert "@田中" in result.content
        assert "@佐藤" in result.content

    async def test_generate_footnote_format(self):
        """generate() should use footnote format for references."""
        from app.services.logue_generator import LogueGenerator

        vertex_response = {
            "pattern_name": "テストパターン",
            "context": "テスト状況[1]",
            "problem": "テスト問題",
            "solution": "テスト解決策[2]",
            "counterarguments": "テスト反論",
            "references": [
                {"log_index": 1, "user_name": "@田中", "excerpt": "引用1"},
                {"log_index": 2, "user_name": "@佐藤", "excerpt": "引用2"},
            ],
        }

        generator = LogueGenerator()
        with patch.object(generator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(return_value=vertex_response)

            result = await generator.generate(
                _make_planter_mock(),
                [_make_log_mock()],
                {},
            )

        assert result is not None
        assert "[1] @田中" in result.content
        assert "[2] @佐藤" in result.content

    async def test_generate_falls_back_when_pattern_name_missing(self):
        """generate() should fall back to a default name if AI omits pattern_name."""
        from app.services.logue_generator import DEFAULT_PATTERN_NAME, LogueGenerator

        vertex_response = {
            "pattern_name": "",
            "context": "x",
            "problem": "y",
            "solution": "z",
            "counterarguments": "w",
            "references": [],
        }
        generator = LogueGenerator()
        with patch.object(generator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(return_value=vertex_response)

            result = await generator.generate(
                _make_planter_mock(),
                [_make_log_mock()],
                {},
            )

        assert result is not None
        assert result.pattern_name == DEFAULT_PATTERN_NAME

    async def test_generate_returns_none_on_vertex_error(self):
        """generate() should return None when Vertex AI fails."""
        from app.services.logue_generator import LogueGenerator

        generator = LogueGenerator()
        with patch.object(generator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(side_effect=Exception("Vertex AI down"))

            result = await generator.generate(
                _make_planter_mock(),
                [_make_log_mock()],
                {},
            )

        assert result is None


class TestLogueGeneratorBloom:
    async def test_bloom_full_flow(self):
        """bloom() should generate article, update planter, calculate insight scores, and create notification."""
        from app.services.logue_generator import GeneratedLogue, LogueGenerator

        planter_id = uuid.uuid4()
        user_id = uuid.uuid4()
        planter = _make_planter_mock(planter_id=planter_id, user_id=user_id)
        logs = [_make_log_mock(user_id=uuid.uuid4()) for _ in range(5)]
        users_map = {log.user_id: _make_user_mock(user_id=log.user_id) for log in logs}
        users_map[user_id] = _make_user_mock(user_id=user_id, display_name="Seed Author")

        db = AsyncMock()

        generator = LogueGenerator()
        generated = GeneratedLogue(
            content="## 状況（Context）\nContent here",
            pattern_name="開花パターン",
        )
        generator.generate = AsyncMock(return_value=generated)
        generator._get_planter = AsyncMock(return_value=planter)
        generator._get_logs_with_users = AsyncMock(return_value=(logs, users_map))
        generator._update_logue_content = AsyncMock()
        generator._create_notifications = AsyncMock()

        mock_calculator = AsyncMock()
        mock_calculator.calculate = AsyncMock(return_value=[])
        mock_calculator.apply = AsyncMock()

        with patch("app.services.logue_generator.InsightScoreCalculator", return_value=mock_calculator):
            await generator.bloom(planter_id, db)

        generator.generate.assert_called_once()
        generator._update_logue_content.assert_called_once_with(
            planter_id, generated.content, generated.pattern_name, db
        )
        mock_calculator.calculate.assert_called_once()
        mock_calculator.apply.assert_called_once()
        generator._create_notifications.assert_called_once()

    async def test_bloom_keeps_status_on_generate_failure(self):
        """bloom() should not update logue_content when generate() fails."""
        from app.services.logue_generator import LogueGenerator

        planter_id = uuid.uuid4()
        planter = _make_planter_mock(planter_id=planter_id)
        db = AsyncMock()

        generator = LogueGenerator()
        generator.generate = AsyncMock(return_value=None)
        generator._get_planter = AsyncMock(return_value=planter)
        generator._get_logs_with_users = AsyncMock(return_value=([], {}))
        generator._update_logue_content = AsyncMock()

        await generator.bloom(planter_id, db)

        generator._update_logue_content.assert_not_called()
