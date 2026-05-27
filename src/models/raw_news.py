from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class RawNews:
    id: str
    title: str
    source: str
    published_at: str
    url: str = ''
    language: str = ''
    raw_content: str = ''

    def to_dict(self) -> dict:
        return asdict(self)
