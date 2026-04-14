import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_log_mock(log_id=None, user_id=None, body="Log body", is_ai_generated=False):
    log = MagicMock()
    log.id = log_id or uuid.uuid4()
    log.user_id = user_id or uuid.uuid4()
    log.body = body
    log.is_ai_generated = is_ai_generated
    return log


def _make_planter_mock(planter_id=None, user_id=None):
    p = MagicMock()
    p.id = planter_id or uuid.uuid4()
    p.user_id = user_id or uuid.uuid4()
    return p


class TestInsightScoreCalculatorCalculate:
    async def test_calculate_evaluates_each_log(self):
        """calculate() should evaluate each non-AI log via Vertex AI."""
        from app.services.insight_calculator import InsightScoreCalculator

        planter_id = uuid.uuid4()
        seed_author_id = uuid.uuid4()
        log1_user = uuid.uuid4()
        log2_user = uuid.uuid4()

        logs = [
            _make_log_mock(user_id=log1_user, body="Great insight"),
            _make_log_mock(user_id=log2_user, body="Another perspective"),
            _make_log_mock(user_id=None, body="AI facilitation", is_ai_generated=True),
        ]

        planter = _make_planter_mock(planter_id=planter_id, user_id=seed_author_id)

        vertex_response = {
            "evaluations": [
                {"log_id": str(logs[0].id), "score": 0.85, "reason": "Core solution"},
                {"log_id": str(logs[1].id), "score": 0.4, "reason": "Context"},
            ]
        }

        calculator = InsightScoreCalculator()
        with patch.object(calculator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(return_value=vertex_response)

            db = AsyncMock()
            calculator._get_planter = AsyncMock(return_value=planter)
            calculator._get_logs = AsyncMock(return_value=logs)

            events = await calculator.calculate(planter_id, "# Article", db)

        # Should have events for 2 log contributors + 1 seed author bonus
        assert len(events) == 3
        log_events = [e for e in events if e.reason == "log_contribution"]
        seed_events = [e for e in events if e.reason == "seed_author"]
        assert len(log_events) == 2
        assert len(seed_events) == 1
        assert seed_events[0].score_delta == 1.0
        assert seed_events[0].user_id == seed_author_id

    async def test_calculate_excludes_ai_logs(self):
        """calculate() should not evaluate AI-generated logs."""
        from app.services.insight_calculator import InsightScoreCalculator

        planter_id = uuid.uuid4()
        ai_log = _make_log_mock(user_id=None, is_ai_generated=True)

        planter = _make_planter_mock(planter_id=planter_id)
        vertex_response = {"evaluations": []}

        calculator = InsightScoreCalculator()
        with patch.object(calculator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(return_value=vertex_response)

            db = AsyncMock()
            calculator._get_planter = AsyncMock(return_value=planter)
            calculator._get_logs = AsyncMock(return_value=[ai_log])

            events = await calculator.calculate(planter_id, "# Article", db)

        # Only seed author bonus (no log contributions)
        assert len(events) == 1
        assert events[0].reason == "seed_author"

    async def test_calculate_seed_author_bonus(self):
        """calculate() should give seed author a fixed bonus of 1.0."""
        from app.services.insight_calculator import InsightScoreCalculator

        seed_author_id = uuid.uuid4()
        planter = _make_planter_mock(user_id=seed_author_id)

        calculator = InsightScoreCalculator()
        with patch.object(calculator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(return_value={"evaluations": []})

            db = AsyncMock()
            calculator._get_planter = AsyncMock(return_value=planter)
            calculator._get_logs = AsyncMock(return_value=[])

            events = await calculator.calculate(planter.id, "# Article", db)

        assert len(events) == 1
        assert events[0].user_id == seed_author_id
        assert events[0].score_delta == 1.0
        assert events[0].reason == "seed_author"

    async def test_calculate_fallback_on_vertex_error(self):
        """calculate() should give uniform 0.5 score on Vertex AI failure."""
        from app.services.insight_calculator import InsightScoreCalculator

        planter_id = uuid.uuid4()
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        logs = [
            _make_log_mock(user_id=user1),
            _make_log_mock(user_id=user2),
        ]
        planter = _make_planter_mock(planter_id=planter_id)

        calculator = InsightScoreCalculator()
        with patch.object(calculator, "client") as mock_client:
            mock_client.generate_json = AsyncMock(side_effect=Exception("AI down"))

            db = AsyncMock()
            calculator._get_planter = AsyncMock(return_value=planter)
            calculator._get_logs = AsyncMock(return_value=logs)

            events = await calculator.calculate(planter_id, "# Article", db)

        log_events = [e for e in events if e.reason == "log_contribution"]
        assert len(log_events) == 2
        for e in log_events:
            assert e.score_delta == 0.5


class TestInsightScoreCalculatorApply:
    async def test_apply_saves_events_and_updates_users(self):
        """apply() should save events to DB and update user insight scores."""
        from app.models.score import InsightScoreEvent
        from app.services.insight_calculator import InsightScoreCalculator

        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        planter_id = uuid.uuid4()

        events = [
            InsightScoreEvent(
                user_id=user1,
                planter_id=planter_id,
                log_id=uuid.uuid4(),
                score_delta=0.85,
                reason="log_contribution",
            ),
            InsightScoreEvent(
                user_id=user2,
                planter_id=planter_id,
                log_id=None,
                score_delta=1.0,
                reason="seed_author",
            ),
        ]

        calculator = InsightScoreCalculator()
        db = AsyncMock()
        calculator._save_events = AsyncMock()
        calculator._update_user_scores = AsyncMock()

        await calculator.apply(events, db)

        calculator._save_events.assert_called_once_with(events, db)
        calculator._update_user_scores.assert_called_once()
