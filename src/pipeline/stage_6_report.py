from __future__ import annotations

from pathlib import Path

from src.report.template import build_report_context, render_markdown_report
from src.utils import load_json

BASE_DIR = Path(__file__).resolve().parents[2]



def run(date: str, config: dict) -> dict:
    insights_path = BASE_DIR / 'outputs' / 'insights' / config['naming']['insights'].format(date=date)
    clusters_path = BASE_DIR / 'data' / 'clusters' / config['naming']['clusters'].format(date=date)
    template_path = BASE_DIR / 'templates' / 'report_template.md'
    report_path = BASE_DIR / 'outputs' / 'reports' / config['naming']['report'].format(date=date)
    html_path = BASE_DIR / 'outputs' / 'visualizations' / f'visualization_{date}.html'

    insight = load_json(insights_path)
    clusters = load_json(clusters_path).get('clusters', [])
    template_text = template_path.read_text(encoding='utf-8')
    context = build_report_context(
        date=date,
        title=config['report']['title'],
        insight=insight,
        clusters=clusters,
        visualization_link=html_path.relative_to(BASE_DIR).as_posix(),
    )
    report_path.write_text(render_markdown_report(template_text, context), encoding='utf-8')
    return {'stage': 'report', 'output': str(report_path), 'sections': 7}
