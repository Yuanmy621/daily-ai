from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.models import DailyInsight
from src.utils import LLMCallError, build_llm_client, dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]
PROMPT_PATH = BASE_DIR / 'prompts' / 'insight' / 'generate_daily_insight.txt'
TOP_EVENT_LIMIT = 5
TREND_BUCKETS = ('technology', 'application', 'policy', 'capital')
TOPIC_TO_TREND = {
    'foundation model': 'technology',
    'multimodal': 'technology',
    'ai chip': 'technology',
    'robotics': 'application',
    'ai agent': 'application',
    'ai healthcare': 'application',
    'ai policy': 'policy',
}


def _unique_non_blank(values: list[Any], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(text)
        if limit is not None and len(results) >= limit:
            break
    return results


def _sample_size(clusters: list[dict[str, Any]]) -> int:
    news_ids: set[str] = set()
    for cluster in clusters:
        news_ids.update(str(news_id) for news_id in cluster.get('news_ids', []))
    return len(news_ids)


def _build_cluster_index(structured_articles: list[dict[str, Any]], clusters: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    articles_by_id = {str(article['id']): article for article in structured_articles}
    return {
        str(cluster['cluster_id']): [articles_by_id[news_id] for news_id in cluster.get('news_ids', []) if news_id in articles_by_id]
        for cluster in clusters
    }


def _cluster_trend_bucket(cluster: dict[str, Any], articles: list[dict[str, Any]]) -> str:
    if any(str(article.get('event_type')) == 'funding' for article in articles):
        return 'capital'
    topic = str(cluster.get('topic', 'general ai'))
    return TOPIC_TO_TREND.get(topic, 'application')


def _rule_trend_insights(clusters: list[dict[str, Any]], cluster_articles: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    trend_insights = {bucket: [] for bucket in TREND_BUCKETS}
    for cluster in clusters:
        cluster_id = str(cluster.get('cluster_id', ''))
        articles = cluster_articles.get(cluster_id, [])
        bucket = _cluster_trend_bucket(cluster, articles)
        entities = '、'.join(cluster.get('entities', [])[:3]) or '多家机构'
        points = cluster.get('representative_points', [])
        point = str(points[0]).strip() if points else str(cluster.get('headline', '未命名热点')).strip()
        trend_insights[bucket].append(f"{entities}相关动态显示：{point}")
    return {bucket: _unique_non_blank(values, limit=3) for bucket, values in trend_insights.items()}


def _signal_alerts(cluster_articles: dict[str, list[dict[str, Any]]], field: str, limit: int = 5) -> list[str]:
    counter: Counter[str] = Counter()
    for articles in cluster_articles.values():
        for article in articles:
            counter.update(text.strip() for text in article.get(field, []) if str(text).strip())
    return [text for text, _ in counter.most_common(limit)]


def _refine_with_llm(rule_payload: dict[str, Any], clusters: list[dict[str, Any]], llm_client: Any) -> dict[str, Any]:
    system_prompt = PROMPT_PATH.read_text(encoding='utf-8')
    cluster_summary = [
        {
            'cluster_id': cluster.get('cluster_id'),
            'headline': cluster.get('headline'),
            'topic': cluster.get('topic'),
            'entities': cluster.get('entities', []),
            'heat_score': cluster.get('heat_score'),
            'representative_points': cluster.get('representative_points', []),
        }
        for cluster in clusters[:TOP_EVENT_LIMIT]
    ]
    payload = llm_client.chat_json(
        system_prompt,
        json.dumps({'clusters': cluster_summary, 'rule_based': rule_payload}, ensure_ascii=False, indent=2),
    )
    trend_payload = payload.get('trend_insights', {}) if isinstance(payload.get('trend_insights', {}), dict) else {}
    return {
        'trend_insights': {
            bucket: _unique_non_blank(trend_payload.get(bucket, rule_payload['trend_insights'].get(bucket, [])), limit=3)
            for bucket in TREND_BUCKETS
        },
        'risk_alerts': _unique_non_blank(payload.get('risk_alerts', rule_payload['risk_alerts']), limit=5),
        'opportunity_alerts': _unique_non_blank(payload.get('opportunity_alerts', rule_payload['opportunity_alerts']), limit=5),
    }


def run(date: str, config: dict) -> dict:
    clusters_path = BASE_DIR / 'data' / 'clusters' / config['naming']['clusters'].format(date=date)
    structured_path = BASE_DIR / 'data' / 'structured' / config['naming']['structured'].format(date=date)
    clusters_payload = load_json(clusters_path)
    clusters = sorted(clusters_payload.get('clusters', []), key=lambda item: float(item.get('heat_score', 0.0)), reverse=True)
    structured_articles = load_json(structured_path).get('articles', [])
    cluster_articles = _build_cluster_index(structured_articles, clusters)

    rule_payload = {
        'trend_insights': _rule_trend_insights(clusters, cluster_articles),
        'risk_alerts': _unique_non_blank(_signal_alerts(cluster_articles, 'risk_signals'), limit=5),
        'opportunity_alerts': _unique_non_blank(_signal_alerts(cluster_articles, 'opportunity_signals'), limit=5),
    }

    llm_client = build_llm_client(config)
    if llm_client is not None:
        try:
            refined_payload = _refine_with_llm(rule_payload, clusters, llm_client)
        except (LLMCallError, OSError, ValueError, TypeError, json.JSONDecodeError):
            refined_payload = rule_payload
    else:
        refined_payload = rule_payload

    top_events = [
        {
            'cluster_id': cluster['cluster_id'],
            'headline': cluster['headline'],
            'heat_score': cluster['heat_score'],
        }
        for cluster in clusters[:TOP_EVENT_LIMIT]
    ]
    insight = DailyInsight(
        date=date,
        sample_size=_sample_size(clusters),
        top_events=top_events,
        trend_insights=refined_payload['trend_insights'],
        risk_alerts=refined_payload['risk_alerts'],
        opportunity_alerts=refined_payload['opportunity_alerts'],
    )
    output_path = BASE_DIR / 'outputs' / 'insights' / config['naming']['insights'].format(date=date)
    payload = insight.to_dict()
    payload['generated_at'] = datetime.now(timezone.utc).isoformat()
    dump_json(output_path, payload)
    return {'stage': 'insight', 'output': str(output_path), 'count': len(insight.top_events)}
