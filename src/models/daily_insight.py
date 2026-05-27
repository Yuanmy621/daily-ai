from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class DailyInsight:
    date: str
    sample_size: int
    top_events: list[dict] = field(default_factory=list)
    trend_insights: dict = field(default_factory=lambda: {
        'technology': [],
        'application': [],
        'policy': [],
        'capital': [],
    })
    risk_alerts: list[str] = field(default_factory=list)
    opportunity_alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
