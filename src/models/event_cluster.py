from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class EventCluster:
    cluster_id: str
    topic: str
    headline: str
    news_ids: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    heat_score: float = 0.0
    representative_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
