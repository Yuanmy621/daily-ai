from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.analysis.nlp_utils import extract_keywords
from src.models import EventCluster
from src.utils import dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]


def _article_keywords(article: dict[str, Any]) -> set[str]:
    text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
    language = str(article.get('language', 'en'))
    return {keyword.lower() for keyword in extract_keywords(text, language, top_k=8) if keyword}


def _cluster_match_score(article: dict[str, Any], cluster: dict[str, Any]) -> float:
    score = 0.0
    if article.get('topic') == cluster['topic']:
        score += 2.0
    if article.get('event_type') == cluster['event_type']:
        score += 1.0
    entity_overlap = len(set(article.get('entities', [])) & cluster['entity_set'])
    score += entity_overlap * 1.5
    keyword_overlap = len(_article_keywords(article) & cluster['keyword_set'])
    score += min(keyword_overlap, 3) * 0.5
    return score


def _representative_points(articles: list[dict[str, Any]], limit: int = 4) -> list[str]:
    counter: Counter[str] = Counter()
    for article in articles:
        for evidence in article.get('evidence', []):
            text = str(evidence).strip()
            if text:
                counter[text] += 1
    return [text for text, _ in counter.most_common(limit)]


def _top_entities(articles: list[dict[str, Any]], limit: int = 5) -> list[str]:
    counter: Counter[str] = Counter()
    for article in articles:
        counter.update(entity for entity in article.get('entities', []) if entity)
    return [entity for entity, _ in counter.most_common(limit)]


def _cluster_heat_score(articles: list[dict[str, Any]]) -> float:
    avg_importance = sum(float(article.get('importance_score', 0.0)) for article in articles) / max(len(articles), 1)
    signal_bonus = sum(
        0.4 * len(article.get('risk_signals', [])) + 0.4 * len(article.get('opportunity_signals', []))
        for article in articles
    )
    volume_bonus = len(articles) * 1.2
    return round(min(avg_importance + volume_bonus + signal_bonus, 10.0), 1)


def _cluster_headline(articles: list[dict[str, Any]]) -> str:
    ranked = sorted(
        articles,
        key=lambda article: (float(article.get('importance_score', 0.0)), len(str(article.get('summary', '')))),
        reverse=True,
    )
    return str(ranked[0].get('title', '未命名热点')).strip() if ranked else '未命名热点'


def _build_cluster_payload(date: str, index: int, articles: list[dict[str, Any]]) -> dict[str, Any]:
    headline = _cluster_headline(articles)
    topic = str(articles[0].get('topic', 'general ai')) if articles else 'general ai'
    return EventCluster(
        cluster_id=f'cluster_{date}_{index:02d}',
        topic=topic,
        headline=headline,
        news_ids=[str(article['id']) for article in articles],
        entities=_top_entities(articles),
        heat_score=_cluster_heat_score(articles),
        representative_points=_representative_points(articles),
    ).to_dict()


def run(date: str, config: dict) -> dict:
    input_path = BASE_DIR / 'data' / 'structured' / config['naming']['structured'].format(date=date)
    structured_payload = load_json(input_path)
    articles = structured_payload.get('articles', [])
    working_clusters: list[dict[str, Any]] = []

    for article in sorted(articles, key=lambda item: float(item.get('importance_score', 0.0)), reverse=True):
        best_cluster: dict[str, Any] | None = None
        best_score = -1.0
        for cluster in working_clusters:
            score = _cluster_match_score(article, cluster)
            if score > best_score:
                best_score = score
                best_cluster = cluster

        if best_cluster is not None and best_score >= 2.5:
            best_cluster['articles'].append(article)
            best_cluster['entity_set'].update(entity for entity in article.get('entities', []) if entity)
            best_cluster['keyword_set'].update(_article_keywords(article))
        else:
            working_clusters.append(
                {
                    'topic': str(article.get('topic', 'general ai')),
                    'event_type': str(article.get('event_type', 'news')),
                    'articles': [article],
                    'entity_set': set(article.get('entities', [])),
                    'keyword_set': _article_keywords(article),
                }
            )

    clusters = [
        _build_cluster_payload(date, index, cluster['articles'])
        for index, cluster in enumerate(
            sorted(working_clusters, key=lambda item: _cluster_heat_score(item['articles']), reverse=True),
            start=1,
        )
    ]
    output_path = BASE_DIR / 'data' / 'clusters' / config['naming']['clusters'].format(date=date)
    payload = {
        'date': date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'clusters': clusters,
    }
    dump_json(output_path, payload)
    return {'stage': 'cluster', 'output': str(output_path), 'count': len(clusters)}
