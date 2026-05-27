#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
TARGET_DIRS = [
    BASE_DIR / 'data' / 'structured',
    BASE_DIR / 'outputs' / 'insights',
]


def iter_candidate_files() -> list[Path]:
    files: list[Path] = []
    for directory in TARGET_DIRS:
        if not directory.exists():
            continue
        files.extend(sorted(p for p in directory.rglob('*') if p.is_file() and p.suffix in {'.json', '.jsonl'}))
    return files


def main() -> int:
    files = iter_candidate_files()
    if not files:
        print('[validate-schema] no structured or insight files found')
        return 0

    for file_path in files:
        if 'structured' in file_path.parts:
            schema = 'structured'
        else:
            continue
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'check.py'), str(file_path), '--schema', schema, '--min-count', '1'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print('[validate-schema] validation failed for', file_path)
            print(result.stdout.strip())
            print(result.stderr.strip())
            return result.returncode
    print('[validate-schema] validation passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
