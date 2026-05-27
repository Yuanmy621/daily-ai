from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class StructuredNews:
    id: str
    title: str
    source: str
    published_at: str
    language: str
    summary: str
    entities: list[str] = field(default_factory=list)
    topic: str = ''
    event_type: str = ''
    region: str = ''
    importance_score: float = 0.0
    sentiment: str = ''
    risk_signals: list[str] = field(default_factory=list)
    opportunity_signals: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
