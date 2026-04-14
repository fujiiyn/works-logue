import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.score_engine import MaturityResult, StructureResult


@pytest.fixture
def mock_score_engine():
    with patch("app.pipelines.score_pipeline.ScoreEngine") as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ai_facilitator():
    with patch("app.pipelines.score_pipeline.AIFacilitator") as mock_cls:
        mock_instance = AsyncMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_session_factory(mock_db_session):
    """Mock async session factory (async context manager)."""
    factory = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_db_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    factory.return_value = ctx
    return factory


def _make_planter_mock(
    planter_id=None,
    title="Test Seed",
    body="Test body",
    status="sprout",
    log_count=5,
    contributor_count=3,
    structure_fulfillment=0.0,
    maturity_score=None,
    progress=0.0,
):
    p = MagicMock()
    p.id = planter_id or uuid.uuid4()
    p.title = title
    p.body = body
    p.status = status
    p.log_count = log_count
    p.contributor_count = contributor_count
    p.structure_fulfillment = structure_fulfillment
    p.maturity_score = maturity_score
    p.progress = progress
    return p


def _make_log_mock(body="Log body", user_id=None, display_name="User"):
    log = MagicMock()
    log.body = body
    log.user_id = user_id or uuid.uuid4()
    log.is_ai_generated = False
    user_mock = MagicMock()
    user_mock.display_name = display_name
    return log, user_mock


class TestScorePipelineExecute:
    async def test_condition_a_only(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """execute() should run only condition A when minimum participation not met."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=2, contributor_count=1)
        logs = [MagicMock(body="Log 1", user_id=uuid.uuid4(), is_ai_generated=False)]

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": False, "solution": False, "name": False},
            fulfillment=0.25,
        )

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        mock_score_engine.evaluate_structure.assert_called_once()
        mock_score_engine.evaluate_maturity.assert_not_called()

    async def test_condition_a_and_b(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """execute() should run both conditions when participation thresholds are met."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=5, contributor_count=3)
        logs = [MagicMock(body=f"Log {i}", user_id=uuid.uuid4(), is_ai_generated=False) for i in range(5)]

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores={"comprehensiveness": 0.8, "diversity": 0.7, "counterarguments": 0.6, "specificity": 0.9},
            total=0.75,
        )

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        mock_score_engine.evaluate_structure.assert_called_once()
        mock_score_engine.evaluate_maturity.assert_called_once()

    async def test_condition_b_passed_maturity(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """execute() should set passed_maturity=true when maturity_total >= bloom_threshold."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=5, contributor_count=3)
        logs = [MagicMock(body=f"Log {i}", user_id=uuid.uuid4(), is_ai_generated=False) for i in range(5)]

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores={"comprehensiveness": 0.8, "diversity": 0.8, "counterarguments": 0.7, "specificity": 0.9},
            total=0.8,
        )

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        # Verify snapshot was saved with passed_maturity=True
        call_args = pipeline._save_snapshot.call_args
        snapshot = call_args[0][1]  # second positional arg
        assert snapshot.passed_maturity is True

    async def test_facilitation_when_maturity_below_threshold(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """execute() should trigger AI facilitation when maturity < bloom_threshold and should_facilitate."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=5, contributor_count=3)
        logs = [MagicMock(body=f"Log {i}", user_id=uuid.uuid4(), is_ai_generated=False) for i in range(5)]

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores={"comprehensiveness": 0.5, "diversity": 0.4, "counterarguments": 0.3, "specificity": 0.6},
            total=0.45,
        )

        mock_ai_facilitator.should_facilitate.return_value = True
        mock_ai_facilitator.generate_facilitation.return_value = "具体的な経験をお聞かせください"

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()
        pipeline._create_ai_log = AsyncMock()

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        mock_ai_facilitator.should_facilitate.assert_called_once()
        mock_ai_facilitator.generate_facilitation.assert_called_once()
        pipeline._create_ai_log.assert_called_once()

    async def test_error_does_not_propagate(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """execute() should catch and log errors without propagating."""
        from app.pipelines.score_pipeline import ScorePipeline

        mock_score_engine.evaluate_structure.side_effect = Exception("Vertex AI down")

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=_make_planter_mock())
        pipeline._get_logs_with_users = AsyncMock(return_value=([], {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )

        # Should not raise
        await pipeline.execute(uuid.uuid4(), uuid.uuid4(), mock_db_session)
