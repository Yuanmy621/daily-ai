from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.analysis.extractor import llm_enhance, rule_based_extract
from src.utils import dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]


def run(date: str, config: dict) -> dict:
    input_path = BASE_DIR / 'data' / 'normalized' / config['naming']['normalized'].format(date=date)
    normalized_payload = load_json(input_path)
    articles = normalized_payload.get('articles', [])
    structured = []
    for item in articles:
        extracted = rule_based_extract(item)
        enhanced = llm_enhance(extracted, item)
        structured.append(enhanced.to_dict())
    output_path = BASE_DIR / 'data' / 'structured' / config['naming']['structured'].format(date=date)
    payload = {
        'date': date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'articles': structured,
    }
    dump_json(output_path, payload)
    return {'stage': 'extract', 'output': str(output_path), 'count': len(structured)}
