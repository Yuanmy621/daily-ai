from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.analysis.extractor import llm_enhance, rule_based_extract
from src.utils import build_llm_client, dump_json, load_json, load_llm_config

BASE_DIR = Path(__file__).resolve().parents[2]


def _should_enhance(item: dict, extracted: object, llm_config: dict) -> bool:
    importance = float(getattr(extracted, 'importance_score', 0.0))
    evidence = getattr(extracted, 'evidence', []) or []
    entities = getattr(extracted, 'entities', []) or []
    threshold = float(llm_config.get('enhance_min_importance', 7.0))
    # 只增强高重要度或规则信号偏弱的文章，控制调用成本并保留可回退路径。
    return importance >= threshold or len(evidence) <= 1 or not entities


def run(date: str, config: dict) -> dict:
    input_path = BASE_DIR / 'data' / 'normalized' / config['naming']['normalized'].format(date=date)
    normalized_payload = load_json(input_path)
    articles = normalized_payload.get('articles', [])
    llm_config = load_llm_config(config)
    llm_client = build_llm_client(config)
    structured = []
    enhanced_count = 0

    for item in articles:
        extracted = rule_based_extract(item)
        if llm_client is not None and _should_enhance(item, extracted, llm_config):
            enhanced = llm_enhance(extracted, item, llm_client=llm_client)
            if enhanced.to_dict() != extracted.to_dict():
                enhanced_count += 1
        else:
            enhanced = extracted
        structured.append(enhanced.to_dict())

    output_path = BASE_DIR / 'data' / 'structured' / config['naming']['structured'].format(date=date)
    payload = {
        'date': date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'llm_enabled': bool(llm_client),
        'llm_enhanced_count': enhanced_count,
        'articles': structured,
    }
    dump_json(output_path, payload)
    return {
        'stage': 'extract',
        'output': str(output_path),
        'count': len(structured),
        'llm_enabled': bool(llm_client),
        'llm_enhanced_count': enhanced_count,
    }
