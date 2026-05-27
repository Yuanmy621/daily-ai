#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STAGE_PATHS = [
    ('raw', BASE_DIR / 'data' / 'raw'),
    ('normalized', BASE_DIR / 'data' / 'normalized'),
    ('structured', BASE_DIR / 'data' / 'structured'),
    ('clusters', BASE_DIR / 'data' / 'clusters'),
    ('insights', BASE_DIR / 'outputs' / 'insights'),
    ('reports', BASE_DIR / 'outputs' / 'reports'),
    ('visualizations', BASE_DIR / 'outputs' / 'visualizations'),
]


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return len([p for p in path.iterdir() if p.is_file() and not p.name.startswith('.')])


def main() -> int:
    status = {name: count_files(path) for name, path in STAGE_PATHS}
    print('[check-stage-output] pipeline status:', json.dumps(status, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
