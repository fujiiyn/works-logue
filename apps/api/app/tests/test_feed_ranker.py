import uuid
from datetime import datetime, timezone

import pytest

from app.models.planter import Planter
from app.services.feed_ranker import FeedRanker, RankedPlanter


def _make_planter(
    *,
    structure_fulfillment: float = 0.0,
    created_at: datetime | None = None,
) -> Planter:
    p = Planter(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Test",
        body="Test body",
        seed_type_id=uuid.uuid4(),
        status="sprout",
        structure_fulfillment=structure_fulfillment,
        progress=0.0,
        log_count=0,
        contributor_count=0,
    )
    p.created_at = created_at or datetime.now(timezone.utc)
    return p


class TestFeedRanker:
    def setup_method(self) -> None:
        self.ranker = FeedRanker()

    def test_rank_trending_empty_list(self) -> None:
        result = self.ranker.rank_trending([], {}, {})
        assert result == []

    def test_rank_trending_single_planter(self) -> None:
        p = _make_planter(structure_fulfillment=0.5)
        views = {p.id: 10}
        velocities = {p.id: 2.0}

        result = self.ranker.rank_trending([p], views, velocities)

        assert len(result) == 1
        assert result[0].planter is p
        # Single item: norm(views)=0, norm(velocity)=0, structure=0.5
        # score = 0.3*0 + 0.5*0 + 0.2*0.5 = 0.1
        assert result[0].trending_score == pytest.approx(0.1)

    def test_rank_trending_multiple_planters_correct_order(self) -> None:
        p1 = _make_planter(structure_fulfillment=0.0)
        p2 = _make_planter(structure_fulfillment=0.5)
        p3 = _make_planter(structure_fulfillment=1.0)

        views = {p1.id: 100, p2.id: 50, p3.id: 0}
        velocities = {p1.id: 0.0, p2.id: 5.0, p3.id: 10.0}

        result = self.ranker.rank_trending([p1, p2, p3], views, velocities)

        assert len(result) == 3
        # p1: 0.3*1.0 + 0.5*0.0 + 0.2*0.0 = 0.3
        # p2: 0.3*0.5 + 0.5*0.5 + 0.2*0.5 = 0.5
        # p3: 0.3*0.0 + 0.5*1.0 + 0.2*1.0 = 0.7
        assert result[0].planter is p3
        assert result[0].trending_score == pytest.approx(0.7)
        assert result[1].planter is p2
        assert result[1].trending_score == pytest.approx(0.5)
        assert result[2].planter is p1
        assert result[2].trending_score == pytest.approx(0.3)

    def test_rank_trending_zero_views_and_velocity(self) -> None:
        p1 = _make_planter(structure_fulfillment=0.8)
        p2 = _make_planter(structure_fulfillment=0.2)

        views = {p1.id: 0, p2.id: 0}
        velocities = {p1.id: 0.0, p2.id: 0.0}

        result = self.ranker.rank_trending([p1, p2], views, velocities)

        # All views/velocity are 0 → norm = 0, only structure matters
        # p1: 0.2*0.8 = 0.16
        # p2: 0.2*0.2 = 0.04
        assert result[0].planter is p1
        assert result[0].trending_score == pytest.approx(0.16)
        assert result[1].planter is p2
        assert result[1].trending_score == pytest.approx(0.04)

    def test_rank_trending_same_score_tiebreak_by_created_at(self) -> None:
        older = datetime(2026, 1, 1, tzinfo=timezone.utc)
        newer = datetime(2026, 4, 1, tzinfo=timezone.utc)

        p1 = _make_planter(structure_fulfillment=0.5, created_at=older)
        p2 = _make_planter(structure_fulfillment=0.5, created_at=newer)

        views = {p1.id: 0, p2.id: 0}
        velocities = {p1.id: 0.0, p2.id: 0.0}

        result = self.ranker.rank_trending([p1, p2], views, velocities)

        # Same score → newer first
        assert result[0].planter is p2
        assert result[1].planter is p1

    def test_rank_trending_missing_view_and_velocity_data(self) -> None:
        p = _make_planter(structure_fulfillment=0.6)

        # No entries in views/velocities for this planter
        result = self.ranker.rank_trending([p], {}, {})

        assert len(result) == 1
        # score = 0.2 * 0.6 = 0.12
        assert result[0].trending_score == pytest.approx(0.12)
