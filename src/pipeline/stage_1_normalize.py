from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.analysis.extractor import KNOWN_ENTITIES, clean_text, normalize_language
from src.models import NormalizedNews
from src.utils import dump_json, load_json

BASE_DIR = Path(__file__).resolve().parents[2]

STRONG_AI_TERMS = {
    'ai', 'aigc', 'llm', 'gpt', 'claude', 'gemini', 'deepseek', 'kimi', 'agent', 'agents',
    'artificial intelligence', 'foundation model', 'multimodal', 'token', 'inference',
    '人工智能', '生成式ai', '生成式', '大模型', '大语言模型', '模型', '智能体', '多模态',
    '具身智能', '机器人', '人形机器人', '自动驾驶', '推理模型', 'ai芯片', 'ai制药', '机器学习',
}

WEAK_AI_TERMS = {
    '训练', '算力', '芯片', 'gpu', 'npu', '云服务', 'api', 'automation', 'productivity',
    '语音', '视觉', 'vision', 'audio', 'robotics', 'humanoid', 'drug discovery', 'copilot',
    'inference cost', 'enterprise ai', 'model training', 'machine learning', 'deep learning',
    '推理', '算子', '算法', '医疗ai', '自动化', '企业服务', '数据中心',
}

LOW_INFORMATION_PATTERNS = {'点击查看', '敬请期待', 'to be continued'}



def _parse_datetime(value: str, fallback_date: str) -> str:
    if not value:
        return f'{fallback_date}T00:00:00Z'
    normalized = value.strip()
    if normalized.endswith('Z'):
        normalized = normalized[:-1] + '+00:00'
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return f'{fallback_date}T00:00:00Z'
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')



def _keyword_list(config: dict, language: str) -> list[str]:
    keyword_groups = config.get('keywords', {})
    return keyword_groups.get('zh' if language == 'zh' else 'en', [])



def _is_low_information(title: str, content: str) -> bool:
    normalized_content = content.strip()
    if not normalized_content:
        return True
    if len(normalized_content) >= 30:
        return False
    content_lower = normalized_content.lower()
    if any(pattern in content_lower for pattern in LOW_INFORMATION_PATTERNS):
        return True
    return normalized_content == title.strip()



def _ai_relevance_score(title: str, content: str, language: str, config: dict) -> int:
    text = f'{title} {content}'.lower()
    title_lower = title.lower()
    score = 0

    dynamic_keywords = {keyword.lower() for keyword in _keyword_list(config, language)}
    entity_terms = {entity.lower() for entity in KNOWN_ENTITIES}

    strong_terms = STRONG_AI_TERMS | dynamic_keywords | entity_terms
    weak_terms = WEAK_AI_TERMS

    for term in strong_terms:
        if term and term in title_lower:
            score += 3
        elif term and term in text:
            score += 2

    for term in weak_terms:
        if term and term in title_lower:
            score += 2
        elif term and term in text:
            score += 1

    return score



def _is_ai_related(title: str, content: str, language: str, config: dict) -> bool:
    score = _ai_relevance_score(title, content, language, config)
    if score >= 3:
        return True
    if score >= 2 and len(content.strip()) >= 80:
        return True
    return False



def run(date: str, config: dict) -> dict:
    input_path = BASE_DIR / 'data' / 'raw' / config['naming']['raw'].format(date=date)
    raw_payload = load_json(input_path)
    articles = raw_payload.get('articles', [])
    max_content_length = int(config.get('validation', {}).get('max_content_length', 50000))
    min_news_count = int(config.get('pipeline', {}).get('min_news_count', 10))
    normalized = []
    filtered_out = 0
    ai_candidates = []
    low_information_candidates = []

    for item in articles:
        title = clean_text(item.get('title', ''))
        content = clean_text(item.get('raw_content', ''))[:max_content_length]
        language = normalize_language(f'{title} {content}', item.get('language', 'en'))
        normalized_item = NormalizedNews(
            id=item['id'].replace('raw_', 'news_', 1),
            title=title,
            source=item.get('source', ''),
            published_at=_parse_datetime(item.get('published_at', ''), date),
            url=item.get('url', ''),
            language=language,
            content=content,
        ).to_dict()

        if _is_low_information(title, content):
            low_information_candidates.append(normalized_item)
            filtered_out += 1
            continue
        if _is_ai_related(title, content, language, config):
            normalized.append(normalized_item)
        else:
            ai_candidates.append(normalized_item)
            filtered_out += 1

    if len(normalized) < min_news_count:
        needed = min_news_count - len(normalized)
        rescued = ai_candidates[:needed]
        normalized.extend(rescued)
        filtered_out -= len(rescued)

    if len(normalized) < min_news_count:
        needed = min_news_count - len(normalized)
        rescued = low_information_candidates[:needed]
        normalized.extend(rescued)
        filtered_out -= len(rescued)

    output_path = BASE_DIR / 'data' / 'normalized' / config['naming']['normalized'].format(date=date)
    payload = {
        'date': date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'filtered_out': max(filtered_out, 0),
        'articles': normalized,
    }
    dump_json(output_path, payload)
    return {'stage': 'normalize', 'output': str(output_path), 'count': len(normalized), 'filtered_out': max(filtered_out, 0)}
