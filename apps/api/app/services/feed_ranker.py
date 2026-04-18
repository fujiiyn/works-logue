import uuid
from dataclasses import dataclass
from datetime import datetime

from app.models.planter import Planter


@dataclass
class RankedPlanter:
    planter: Planter
    trending_score: float


class FeedRanker:
    W_VIEWS = 0.3
    W_VELOCITY = 0.5
    W_STRUCTURE = 0.2

    def rank_trending(
        self,
        planters: list[Planter],
        view_counts: dict[uuid.UUID, int],
        log_velocities: dict[uuid.UUID, float],
        window_hours: int = 72,
    ) -> list[RankedPlanter]:
        if not planters:
            return []

        views_values = [view_counts.get(p.id, 0) for p in planters]
        velocity_values = [log_velocities.get(p.id, 0.0) for p in planters]

        norm_views = self._min_max_normalize(views_values)
        norm_velocities = self._min_max_normalize(velocity_values)

        ranked: list[RankedPlanter] = []
        for i, planter in enumerate(planters):
            score = (
                self.W_VIEWS * norm_views[i]
                + self.W_VELOCITY * norm_velocities[i]
                + self.W_STRUCTURE * planter.structure_fulfillment
            )
            ranked.append(RankedPlanter(planter=planter, trending_score=score))

        ranked.sort(key=lambda r: (-r.trending_score, -r.planter.created_at.timestamp()))
        return ranked

    @staticmethod
    def _min_max_normalize(values: list[float | int]) -> list[float]:
        if not values:
            return []
        min_val = min(values)
        max_val = max(values)
        span = max_val - min_val
        if span == 0:
            return [0.0] * len(values)
        return [(v - min_val) / span for v in values]
