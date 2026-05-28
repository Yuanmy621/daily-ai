from __future__ import annotations

from pathlib import Path

from src.utils import load_json

BASE_DIR = Path(__file__).resolve().parents[2]
REQUIRED_REPORT_SECTIONS = ['## 今日热点', '## 重点事件分析', '## 趋势观察', '## 风险与机会']



def run(date: str, config: dict) -> dict:
    report_path = BASE_DIR / 'outputs' / 'reports' / config['naming']['report'].format(date=date)
    visualization_json_path = BASE_DIR / 'outputs' / 'visualizations' / config['naming']['visualization'].format(date=date)
    visualization_html_path = BASE_DIR / 'outputs' / 'visualizations' / f'visualization_{date}.html'

    if not report_path.exists():
        raise RuntimeError(f'missing report: {report_path}')
    report_text = report_path.read_text(encoding='utf-8')
    if not report_text.strip():
        raise RuntimeError(f'empty report: {report_path}')
    for section in REQUIRED_REPORT_SECTIONS:
        if section not in report_text:
            raise RuntimeError(f'missing report section: {section}')

    if not visualization_json_path.exists():
        raise RuntimeError(f'missing visualization json: {visualization_json_path}')
    payload = load_json(visualization_json_path)
    charts = payload.get('charts', [])
    if not charts:
        raise RuntimeError(f'visualization json has no charts: {visualization_json_path}')

    if not visualization_html_path.exists():
        raise RuntimeError(f'missing visualization html: {visualization_html_path}')
    html_text = visualization_html_path.read_text(encoding='utf-8')
    if '<html' not in html_text.lower():
        raise RuntimeError(f'invalid visualization html: {visualization_html_path}')
    if config['report']['title'] not in html_text:
        raise RuntimeError(f'visualization html missing title: {visualization_html_path}')
    if 'chart-hot-events' not in html_text:
        raise RuntimeError(f'visualization html missing chart container: {visualization_html_path}')

    return {'stage': 'validate_final', 'validated': True, 'chart_count': len(charts)}
