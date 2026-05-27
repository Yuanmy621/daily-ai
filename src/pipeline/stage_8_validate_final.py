from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    report_path = BASE_DIR / 'outputs' / 'reports' / config['naming']['report'].format(date=date)
    visualization_path = BASE_DIR / 'outputs' / 'visualizations' / config['naming']['visualization'].format(date=date)
    if not report_path.exists() or not report_path.read_text(encoding='utf-8').strip():
        raise RuntimeError(f'missing or empty report: {report_path}')
    if not visualization_path.exists() or not visualization_path.read_text(encoding='utf-8').strip():
        raise RuntimeError(f'missing or empty visualization: {visualization_path}')
    return {'stage': 'validate_final', 'validated': True}
