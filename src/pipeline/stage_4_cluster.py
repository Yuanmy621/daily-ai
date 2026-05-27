from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.models import EventCluster
from src.utils import dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    input_path = BASE_DIR / 'data' / 'structured' / config['naming']['structured'].format(date=date)
    structured_payload = load_json(input_path)
    articles = structured_payload.get('articles', [])
    clusters = [
        EventCluster(
            cluster_id=f'cluster_{date}_01',
            topic='foundation model',
            headline='Sample AI hotspot cluster',
            news_ids=[item['id'] for item in articles],
            entities=['Sample AI Company'],
            heat_score=5.0,
            representative_points=['sample point 1', 'sample point 2'],
        ).to_dict()
    ]
    output_path = BASE_DIR / 'data' / 'clusters' / config['naming']['clusters'].format(date=date)
    payload = {
        'date': date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'clusters': clusters,
    }
    dump_json(output_path, payload)
    return {'stage': 'cluster', 'output': str(output_path), 'count': len(clusters)}
