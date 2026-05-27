from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.collector.rss_fetcher import deduplicate, fetch_source
from src.collector.sample_data import get_sample_articles
from src.collector.sources import get_sources
from src.models import RawNews
from src.utils import dump_json

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    output_path = BASE_DIR / 'data' / 'raw' / config['naming']['raw'].format(date=date)
    pipeline = config.get('pipeline', {})
    timeout = int(pipeline.get('rss_fetch_timeout', 30))
    min_news_count = int(pipeline.get('min_news_count', 10))
    max_news_count = int(pipeline.get('max_news_count', 20))
    dedup_threshold = float(pipeline.get('dedup_threshold', 0.85))

    articles: list[dict] = []
    for source in get_sources(config):
        articles.extend(fetch_source(source, timeout=timeout))

    articles = deduplicate(articles, threshold=dedup_threshold)
    if len(articles) < min_news_count:
        articles.extend(get_sample_articles(date))
        articles = deduplicate(articles, threshold=dedup_threshold)

    articles = articles[:max_news_count]

    raw_articles = []
    for index, item in enumerate(articles, start=1):
        raw_articles.append(
            RawNews(
                id=f'raw_{date}_{index:03d}',
                title=item.get('title', '').strip(),
                source=item.get('source', '').strip(),
                published_at=item.get('published_at', datetime.now(timezone.utc).isoformat()),
                url=item.get('url', '').strip(),
                language=item.get('language', '').strip(),
                raw_content=item.get('raw_content', '').strip(),
            ).to_dict()
        )

    payload = {
        'date': date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'articles': raw_articles,
    }
    dump_json(output_path, payload)
    return {'stage': 'collect', 'output': str(output_path), 'count': len(raw_articles)}
