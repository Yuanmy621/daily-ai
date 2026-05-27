#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import load_config, setup_logging, stage_timer

STAGES = [
    ('collect', 'src.pipeline.stage_0_collect'),
    ('normalize', 'src.pipeline.stage_1_normalize'),
    ('extract', 'src.pipeline.stage_2_extract'),
    ('validate_structure', 'src.pipeline.stage_3_validate_structure'),
    ('cluster', 'src.pipeline.stage_4_cluster'),
    ('insight', 'src.pipeline.stage_5_insight'),
    ('report', 'src.pipeline.stage_6_report'),
    ('visualize', 'src.pipeline.stage_7_visualize'),
    ('validate_final', 'src.pipeline.stage_8_validate_final'),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run ths_ai_insight scaffold pipeline.')
    parser.add_argument('--date', required=True, help='Pipeline run date, e.g. 2026-05-27')
    parser.add_argument('--stage', type=int, default=0, help='Start from stage index')
    return parser.parse_args()


def run_stage(stage_name: str, module_path: str, date: str, config: dict) -> dict:
    module = importlib.import_module(module_path)
    with stage_timer(stage_name):
        return module.run(date, config)


def main() -> int:
    args = parse_args()
    setup_logging()
    config = load_config()

    for index, (stage_name, module_path) in enumerate(STAGES):
        if index < args.stage:
            continue
        result = run_stage(stage_name, module_path, args.date, config)
        print(f'[run_daily] stage={stage_name} result={result}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
