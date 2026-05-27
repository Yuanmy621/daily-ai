from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class NormalizedNews:
    id: str
    title: str
    source: str
    published_at: str
    url: str = ''
    language: str = ''
    content: str = ''

    def to_dict(self) -> dict:
        return asdict(self)
