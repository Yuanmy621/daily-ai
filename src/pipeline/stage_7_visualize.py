from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.utils import dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    insight_path = BASE_DIR / 'outputs' / 'insights' / config['naming']['insights'].format(date=date)
    insight = load_json(insight_path)
    output_path = BASE_DIR / 'outputs' / 'visualizations' / config['naming']['visualization'].format(date=date)
    payload = {
        'date': date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'charts': [
            {
                'type': 'bar',
                'title': 'Top Events Heat',
                'data': [
                    {'label': item['headline'], 'value': item['heat_score']}
                    for item in insight.get('top_events', [])
                ],
            }
        ],
    }
    dump_json(output_path, payload)
    return {'stage': 'visualize', 'output': str(output_path), 'count': len(payload['charts'])}
