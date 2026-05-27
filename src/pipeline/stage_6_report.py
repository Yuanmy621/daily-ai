from __future__ import annotations

from pathlib import Path

from src.utils import load_json

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    insights_path = BASE_DIR / 'outputs' / 'insights' / config['naming']['insights'].format(date=date)
    insight = load_json(insights_path)
    report_path = BASE_DIR / 'outputs' / 'reports' / config['naming']['report'].format(date=date)
    lines = [
        f"# {config['report']['title']}",
        '',
        '## 今日热点',
        *(f"- {item['headline']} (heat={item['heat_score']})" for item in insight.get('top_events', [])),
        '',
        '## 趋势观察',
        *(f"- {item}" for item in insight.get('trend_insights', {}).get('technology', [])),
        *(f"- {item}" for item in insight.get('trend_insights', {}).get('application', [])),
        '',
        '## 风险与机会',
        *(f"- 风险: {item}" for item in insight.get('risk_alerts', [])),
        *(f"- 机会: {item}" for item in insight.get('opportunity_alerts', [])),
    ]
    report_path.write_text('\n'.join(lines).strip() + '\n', encoding='utf-8')
    return {'stage': 'report', 'output': str(report_path)}
