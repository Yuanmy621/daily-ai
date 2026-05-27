from __future__ import annotations

from typing import Any


def get_sources(config: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for lang_group in ('chinese', 'english'):
        for source in config.get('sources', {}).get(lang_group, []):
            sources.append({**source, 'lang_group': lang_group})
    return sources
