from __future__ import annotations

import subprocess
from pathlib import Path

from src.utils import load_json

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    input_path = BASE_DIR / 'data' / 'structured' / config['naming']['structured'].format(date=date)
    payload = load_json(input_path)
    min_count = max(1, int(config.get('pipeline', {}).get('min_news_count', 1)))
    result = subprocess.run(
        ['python3', str(BASE_DIR / 'check.py'), str(input_path), '--schema', 'structured', '--min-count', str(min_count)],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout or result.stderr)
    return {'stage': 'validate_structure', 'validated': True, 'input': str(input_path), 'count': len(payload.get('articles', []))}
