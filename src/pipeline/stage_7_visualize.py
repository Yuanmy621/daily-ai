from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.visualize.dashboard import build_visualization_payload, render_dashboard_html
from src.utils import dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]



def run(date: str, config: dict) -> dict:
    insight_path = BASE_DIR / 'outputs' / 'insights' / config['naming']['insights'].format(date=date)
    clusters_path = BASE_DIR / 'data' / 'clusters' / config['naming']['clusters'].format(date=date)
    structured_path = BASE_DIR / 'data' / 'structured' / config['naming']['structured'].format(date=date)
    json_output_path = BASE_DIR / 'outputs' / 'visualizations' / config['naming']['visualization'].format(date=date)
    html_output_path = BASE_DIR / 'outputs' / 'visualizations' / f'visualization_{date}.html'

    insight = load_json(insight_path)
    clusters = load_json(clusters_path).get('clusters', [])
    structured_articles = load_json(structured_path).get('articles', [])

    payload = build_visualization_payload(date, insight, clusters, structured_articles)
    payload['generated_at'] = datetime.now(timezone.utc).isoformat()

    dump_json(json_output_path, payload)
    html_output_path.write_text(render_dashboard_html(config['report']['title'], payload), encoding='utf-8')
    return {
        'stage': 'visualize',
        'output': str(json_output_path),
        'html_output': str(html_output_path),
        'count': len(payload['charts']),
    }
