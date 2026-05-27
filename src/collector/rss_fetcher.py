from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

try:
    import feedparser  # type: ignore
except Exception:  # pragma: no cover
    feedparser = None

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None


def _clean_html(raw_html: str) -> str:
    if not raw_html:
        return ''
    if BeautifulSoup is None:
        return raw_html
    return BeautifulSoup(raw_html, 'html.parser').get_text(separator=' ', strip=True)


def _extract_summary(entry: Any, max_chars: int = 500) -> str:
    if hasattr(entry, 'summary') and entry.summary:
        return _clean_html(entry.summary)[:max_chars]
    if hasattr(entry, 'content') and entry.content:
        return _clean_html(entry.content[0].value)[:max_chars]
    if hasattr(entry, 'description') and entry.description:
        return _clean_html(entry.description)[:max_chars]
    return ''


def _parse_publish_time(entry: Any) -> str:
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        from time import mktime
        return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc).isoformat()
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        from time import mktime
        return datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc).isoformat()
    return datetime.now(tz=timezone.utc).isoformat()


def fetch_source(source: dict[str, Any], timeout: int = 30) -> list[dict[str, Any]]:
    if feedparser is None or requests is None:
        logger.warning('RSS dependencies are missing, skip source: %s', source.get('name'))
        return []

    try:
        response = requests.get(
            source['url'],
            timeout=timeout,
            headers={'User-Agent': 'ths-ai-insight/1.0 RSS Reader'},
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as exc:
        logger.warning('Failed to fetch %s: %s', source.get('name'), exc)
        return []

    articles: list[dict[str, Any]] = []
    for entry in getattr(feed, 'entries', []):
        title = getattr(entry, 'title', '').strip()
        link = getattr(entry, 'link', '').strip()
        summary = _extract_summary(entry)
        if not title or not (link or summary):
            continue
        articles.append(
            {
                'id': str(uuid.uuid4()),
                'source': source['name'],
                'url': link,
                'language': source.get('language', 'en'),
                'published_at': _parse_publish_time(entry),
                'fetch_time': datetime.now(tz=timezone.utc).isoformat(),
                'title': title,
                'raw_content': summary,
            }
        )
    return articles


def deduplicate(articles: list[dict[str, Any]], threshold: float = 0.85) -> list[dict[str, Any]]:
    from difflib import SequenceMatcher

    kept: list[dict[str, Any]] = []
    for article in articles:
        title = article.get('title', '')
        is_duplicate = False
        for existing in kept:
            if SequenceMatcher(None, title, existing.get('title', '')).ratio() >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(article)
    return kept
