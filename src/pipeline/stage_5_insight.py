from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.models import DailyInsight
from src.utils import dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    clusters_path = BASE_DIR / 'data' / 'clusters' / config['naming']['clusters'].format(date=date)
    clusters_payload = load_json(clusters_path)
    clusters = clusters_payload.get('clusters', [])
    insight = DailyInsight(
        date=date,
        sample_size=len(clusters[0].get('news_ids', [])) if clusters else 0,
        top_events=[
            {
                'cluster_id': cluster['cluster_id'],
                'headline': cluster['headline'],
                'heat_score': cluster['heat_score'],
            }
            for cluster in clusters
        ],
        trend_insights={
            'technology': ['sample technology trend'],
            'application': ['sample application trend'],
            'policy': [],
            'capital': [],
        },
        risk_alerts=['sample risk alert'],
        opportunity_alerts=['sample opportunity alert'],
    )
    output_path = BASE_DIR / 'outputs' / 'insights' / config['naming']['insights'].format(date=date)
    payload = insight.to_dict()
    payload['generated_at'] = datetime.now(timezone.utc).isoformat()
    dump_json(output_path, payload)
    return {'stage': 'insight', 'output': str(output_path), 'count': len(insight.top_events)}
