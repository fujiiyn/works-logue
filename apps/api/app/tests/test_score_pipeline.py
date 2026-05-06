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
def mock_louge_generator():
    with patch("app.pipelines.score_pipeline.LougeGenerator") as mock_cls:
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
        """execute() should run only condition A when structure is not fully fulfilled."""
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
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)

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
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)

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
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)

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
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)
        pipeline._create_ai_log = AsyncMock()

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        # should_facilitate is called twice: once before generate, once
        # right before insert as a race-protection re-check.
        assert mock_ai_facilitator.should_facilitate.call_count == 2
        mock_ai_facilitator.generate_facilitation.assert_called_once()
        pipeline._create_ai_log.assert_called_once()

    async def test_facilitation_skipped_when_recheck_false(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """If a concurrent pipeline posted Wisp during generate, the post-Vertex re-check should suppress the duplicate."""
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

        # First call: greenlight generate. Second call (post-Vertex): rival
        # pipeline already posted, so suppress.
        mock_ai_facilitator.should_facilitate.side_effect = [True, False]
        mock_ai_facilitator.generate_facilitation.return_value = "具体的な経験をお聞かせください"

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)
        pipeline._create_ai_log = AsyncMock()

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        assert mock_ai_facilitator.should_facilitate.call_count == 2
        mock_ai_facilitator.generate_facilitation.assert_called_once()
        pipeline._create_ai_log.assert_not_called()

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
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)

        # Should not raise
        await pipeline.execute(uuid.uuid4(), uuid.uuid4(), mock_db_session)

    async def test_bloom_triggered_when_maturity_passed(
        self, mock_score_engine, mock_ai_facilitator, mock_louge_generator, mock_session_factory, mock_db_session
    ):
        """execute() should trigger LougeGenerator.bloom() when passed_maturity=True."""
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
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        mock_louge_generator.bloom.assert_called_once_with(planter.id, mock_db_session)

        # Verify planter was updated with status="louge" and progress=1.0
        update_call = pipeline._update_planter.call_args
        assert update_call[1]["status"] == "louge"
        assert update_call[1]["progress"] == 1.0

    async def test_bloom_error_does_not_propagate(
        self, mock_score_engine, mock_ai_facilitator, mock_louge_generator, mock_session_factory, mock_db_session
    ):
        """execute() should catch bloom errors without propagating."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=5, contributor_count=3)
        logs = [MagicMock(body=f"Log {i}", user_id=uuid.uuid4(), is_ai_generated=False) for i in range(5)]

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores={"comprehensiveness": 0.9, "diversity": 0.9, "counterarguments": 0.9, "specificity": 0.9},
            total=0.9,
        )
        mock_louge_generator.bloom.side_effect = Exception("Vertex AI down during bloom")

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)

        # Should not raise
        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        # Status should still be set to louge (committed before bloom attempt)
        update_call = pipeline._update_planter.call_args
        assert update_call[1]["status"] == "louge"


class TestWispExclusion:
    """Wisp (is_ai_generated=True) logs must not influence score evaluation."""

    async def test_get_logs_with_users_excludes_ai_generated(self):
        """_get_logs_with_users() must drop AI-generated logs at the source.

        After this filter, every downstream consumer (evaluate_structure /
        evaluate_maturity / AIFacilitator) sees only human contributions.
        """
        from app.pipelines.score_pipeline import ScorePipeline

        user_id = uuid.uuid4()
        human_log = MagicMock()
        human_log.body = "Human knowledge"
        human_log.user_id = user_id
        human_log.is_ai_generated = False

        wisp_log = MagicMock()
        wisp_log.body = "Wisp facilitation"
        wisp_log.user_id = None
        wisp_log.is_ai_generated = True

        # Mock the database call inside _get_logs_with_users for users_map lookup
        users_result = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        users_result.scalars.return_value = scalars_mock

        db = AsyncMock()
        db.execute = AsyncMock(return_value=users_result)

        with patch("app.pipelines.score_pipeline.LogRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_all_by_planter = AsyncMock(return_value=[human_log, wisp_log])
            mock_repo_cls.return_value = mock_repo

            pipeline = ScorePipeline()
            logs, _users_map = await pipeline._get_logs_with_users(uuid.uuid4(), db)

        assert logs == [human_log], (
            "AI-generated (Wisp) logs must be filtered out of pipeline inputs"
        )

    async def test_pipeline_drops_wisp_before_llm_eval(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """End-to-end: with a Wisp log returned by LogRepository, the real
        _get_logs_with_users filter must keep Wisp out of both LLM calls.

        This is the regression guard for Bug #1 — if the filter is removed,
        evaluate_structure / evaluate_maturity will see "Wisp facilitation"
        in their inputs and this test fails.
        """
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=2, contributor_count=1)
        user_id = uuid.uuid4()
        user_obj = MagicMock()
        user_obj.id = user_id
        user_obj.display_name = "Tanaka"

        human_log = MagicMock()
        human_log.body = "Human knowledge"
        human_log.user_id = user_id
        human_log.is_ai_generated = False

        wisp_log = MagicMock()
        wisp_log.body = "Wisp facilitation question"
        wisp_log.user_id = None
        wisp_log.is_ai_generated = True

        # Real _get_logs_with_users issues a SELECT against User; return
        # the matching user so users_map is populated.
        users_result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = [user_obj]
        users_result.scalars.return_value = scalars
        mock_db_session.execute = AsyncMock(return_value=users_result)

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores={"comprehensiveness": 0.5, "diversity": 0.5, "counterarguments": 0.5, "specificity": 0.5},
            total=0.5,
        )

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)
        pipeline._create_ai_log = AsyncMock()
        # Block facilitator from posting another Wisp during this test.
        mock_ai_facilitator.should_facilitate.return_value = False

        with patch("app.pipelines.score_pipeline.LogRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_all_by_planter = AsyncMock(return_value=[human_log, wisp_log])
            mock_repo_cls.return_value = mock_repo

            await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        # evaluate_structure receives raw bodies — must contain only the human one.
        structure_bodies = mock_score_engine.evaluate_structure.call_args[0][2]
        assert structure_bodies == ["Human knowledge"]

        # evaluate_maturity receives "Name: body" formatted entries — must not
        # mention the Wisp text or the "Wisp" speaker label.
        maturity_entries = mock_score_engine.evaluate_maturity.call_args[0][2]
        assert all("Wisp" not in entry for entry in maturity_entries)
        assert all("Wisp facilitation question" not in entry for entry in maturity_entries)
        assert any("Human knowledge" in entry for entry in maturity_entries)


class TestMaturityMonotonicity:
    """Maturity scores must never decrease across pipeline runs (per-key max merge)."""

    async def test_per_key_max_merge_with_prev_snapshot(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """Each maturity key keeps its highest historical value."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=5, contributor_count=3)
        logs = [MagicMock(body=f"Log {i}", user_id=uuid.uuid4(), is_ai_generated=False) for i in range(5)]

        # Previous snapshot had high diversity and counterarguments
        prev_snapshot = MagicMock()
        prev_snapshot.structure_parts = {
            "context": True, "problem": True, "solution": True, "name": True
        }
        prev_snapshot.maturity_scores = {
            "comprehensiveness": 0.5,
            "diversity": 0.9,
            "counterarguments": 0.8,
            "specificity": 0.4,
        }
        prev_snapshot.maturity_total = 0.65

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        # Current LLM run is noisier — diversity dropped, but specificity rose
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores={
                "comprehensiveness": 0.7,
                "diversity": 0.4,
                "counterarguments": 0.5,
                "specificity": 0.9,
            },
            total=0.625,
        )

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()
        pipeline._get_latest_snapshot = AsyncMock(return_value=prev_snapshot)

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        snapshot = pipeline._save_snapshot.call_args[0][1]
        assert snapshot.maturity_scores == {
            "comprehensiveness": 0.7,  # new is higher
            "diversity": 0.9,           # prev is higher → preserved
            "counterarguments": 0.8,    # prev is higher → preserved
            "specificity": 0.9,         # new is higher
        }
        # total = (0.7 + 0.9 + 0.8 + 0.9) / 4 = 0.825
        assert snapshot.maturity_total == pytest.approx(0.825)

    async def test_maturity_total_does_not_decrease(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """Snapshot total maturity must be >= previous snapshot total."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=5, contributor_count=3)
        logs = [MagicMock(body=f"Log {i}", user_id=uuid.uuid4(), is_ai_generated=False) for i in range(5)]

        prev_snapshot = MagicMock()
        prev_snapshot.structure_parts = {
            "context": True, "problem": True, "solution": True, "name": True
        }
        prev_snapshot.maturity_scores = {
            "comprehensiveness": 0.7,
            "diversity": 0.7,
            "counterarguments": 0.7,
            "specificity": 0.7,
        }
        prev_snapshot.maturity_total = 0.7

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        # Whole new run is uniformly worse
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores={
                "comprehensiveness": 0.4,
                "diversity": 0.4,
                "counterarguments": 0.4,
                "specificity": 0.4,
            },
            total=0.4,
        )

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()
        pipeline._get_latest_snapshot = AsyncMock(return_value=prev_snapshot)

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        snapshot = pipeline._save_snapshot.call_args[0][1]
        assert snapshot.maturity_total >= prev_snapshot.maturity_total

    async def test_no_prev_snapshot_uses_raw_maturity(
        self, mock_score_engine, mock_ai_facilitator, mock_session_factory, mock_db_session
    ):
        """First run (no prev snapshot) must use the LLM result as-is."""
        from app.pipelines.score_pipeline import ScorePipeline

        planter = _make_planter_mock(log_count=5, contributor_count=3)
        logs = [MagicMock(body=f"Log {i}", user_id=uuid.uuid4(), is_ai_generated=False) for i in range(5)]

        mock_score_engine.evaluate_structure.return_value = StructureResult(
            parts={"context": True, "problem": True, "solution": True, "name": True},
            fulfillment=1.0,
        )
        raw_scores = {
            "comprehensiveness": 0.6,
            "diversity": 0.5,
            "counterarguments": 0.4,
            "specificity": 0.7,
        }
        mock_score_engine.evaluate_maturity.return_value = MaturityResult(
            scores=raw_scores,
            total=0.55,
        )

        pipeline = ScorePipeline(mock_session_factory)
        pipeline._get_planter = AsyncMock(return_value=planter)
        pipeline._get_logs_with_users = AsyncMock(return_value=(logs, {}))
        pipeline._get_settings = AsyncMock(
            return_value={"min_contributors": 3, "min_logs": 5, "bloom_threshold": 0.7, "bud_threshold": 0.8}
        )
        pipeline._save_snapshot = AsyncMock()
        pipeline._update_planter = AsyncMock()
        pipeline._get_latest_snapshot = AsyncMock(return_value=None)

        await pipeline.execute(planter.id, uuid.uuid4(), mock_db_session)

        snapshot = pipeline._save_snapshot.call_args[0][1]
        assert snapshot.maturity_scores == raw_scores
        assert snapshot.maturity_total == pytest.approx(0.55)
