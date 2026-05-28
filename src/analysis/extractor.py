from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.analysis.nlp_utils import extract_keywords
from src.models import StructuredNews
from src.utils import LLMCallError

KNOWN_ENTITIES = [
    'OpenAI', 'Google', 'DeepMind', 'Microsoft', 'Meta', 'Apple', 'Amazon', 'NVIDIA', 'Anthropic',
    'Tesla', 'DeepSeek', 'Hugging Face', '百度', '阿里巴巴', '腾讯', '字节跳动', '华为', '深度求索',
    '智谱AI', '月之暗面', 'Insilico Medicine', '特斯拉', '苹果', 'Meta', 'OpenAI', 'Claude', 'Gemini',
]

TOPIC_KEYWORDS = {
    'foundation model': ['gpt', 'llm', '大模型', 'foundation model', 'transformer', '模型'],
    'ai agent': ['agent', '智能体', 'agentic'],
    'multimodal': ['multimodal', '多模态', 'vision', 'audio'],
    'robotics': ['robot', '机器人', 'humanoid', '人形机器人'],
    'ai chip': ['chip', 'gpu', 'npu', '芯片'],
    'ai policy': ['regulation', 'policy', '法案', '监管', 'compliance'],
    'ai healthcare': ['drug', 'pharma', '医疗', '制药', '抗体'],
}

EVENT_TYPE_KEYWORDS = {
    'product_release': ['发布', '推出', 'release', 'launch', 'open-source', '开源'],
    'funding': ['融资', 'funding', 'raise', 'investment', '估值'],
    'research': ['论文', 'research', 'paper', 'benchmark', 'study', 'neurips'],
    'policy_regulation': ['法案', '监管', 'regulation', 'policy', 'compliance'],
    'deployment': ['部署', 'deploy', '上线', 'production', 'factory'],
    'partnership': ['合作', 'partnership', 'collaboration'],
}

POSITIVE_KEYWORDS = ['突破', '增长', '发布', '开源', '融资', '获批', 'breakthrough', 'launch', 'approval', 'growth', 'funding']
NEGATIVE_KEYWORDS = ['风险', '罚款', '裁员', '争议', '监管', 'ban', 'risk', 'lawsuit', 'layoff', 'warning']
RISK_KEYWORDS = ['风险', '罚款', '裁员', '争议', '监管', 'ban', 'warning', 'threat', 'compliance']
OPPORTUNITY_KEYWORDS = ['开源', '融资', '合作', 'enterprise', 'adoption', 'integration', '增长', '获批']
HIGH_IMPACT_KEYWORDS = ['突破', '里程碑', '首次', 'GPT-5', '融资', '法案', 'breakthrough', 'landmark', 'first', 'approval']
VALID_TOPICS = set(TOPIC_KEYWORDS) | {'general ai'}
VALID_EVENT_TYPES = set(EVENT_TYPE_KEYWORDS) | {'news'}
PROMPTS_DIR = Path(__file__).resolve().parents[2] / 'prompts'
ENHANCE_PROMPT_PATH = PROMPTS_DIR / 'extract' / 'enhance_article.txt'

SENTENCE_SPLIT_RE = re.compile(r'(?<=[。！？.!?])\s+|\n+')
ZH_CHAR_RE = re.compile(r'[一-鿿]')
HTML_TAG_RE = re.compile(r'<[^>]+>')
CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F]')
MULTISPACE_RE = re.compile(r'\s+')


def clean_text(text: str) -> str:
    text = HTML_TAG_RE.sub(' ', text or '')
    text = CONTROL_CHAR_RE.sub(' ', text)
    text = MULTISPACE_RE.sub(' ', text)
    return text.strip()


def normalize_language(text: str, fallback: str = 'en') -> str:
    if ZH_CHAR_RE.search(text):
        return 'zh'
    return fallback or 'en'


def summarize_text(text: str, language: str) -> str:
    text = clean_text(text)
    if not text:
        return ''
    limit = 200 if language == 'zh' else 240
    if len(text) <= limit:
        return text
    if language == 'zh':
        return text[:limit].rstrip('，,；; ') + '。'
    truncated = text[:limit]
    if ' ' in truncated:
        truncated = truncated.rsplit(' ', 1)[0]
    return truncated.rstrip(' ,;') + '.'


def infer_entities(text: str) -> list[str]:
    found = []
    text_lower = text.lower()
    for entity in KNOWN_ENTITIES:
        if entity.lower() in text_lower and entity not in found:
            found.append(entity)
    return found[:5]


def infer_topic(text: str) -> str:
    text_lower = text.lower()
    best_topic = 'general ai'
    best_score = 0
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_topic = topic
            best_score = score
    return best_topic


def infer_event_type(text: str) -> str:
    text_lower = text.lower()
    best_type = 'news'
    best_score = 0
    for event_type, keywords in EVENT_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_type = event_type
            best_score = score
    return best_type


def infer_region(source: str, language: str, text: str) -> str:
    source_text = f'{source} {text}'.lower()
    if language == 'zh' or any(token in source_text for token in ['机器之心', '36氪', '量子位', '虎嗅', '中国', '国内']):
        return 'China'
    if any(token in source_text for token in ['eu', 'europe', '欧盟']):
        return 'Europe'
    if any(token in source_text for token in ['us', 'u.s.', 'america', '美国']):
        return 'US'
    return 'global'


def infer_sentiment(text: str) -> str:
    text_lower = text.lower()
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw.lower() in text_lower)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw.lower() in text_lower)
    if pos > neg + 1:
        return 'positive'
    if neg > pos + 1:
        return 'negative'
    if pos > 0 and neg > 0:
        return 'mixed'
    return 'neutral'


def infer_importance_score(text: str) -> float:
    text_lower = text.lower()
    score = 4.0 + sum(1.5 for kw in HIGH_IMPACT_KEYWORDS if kw.lower() in text_lower)
    return round(min(score, 9.5), 1)


def split_sentences(text: str) -> list[str]:
    sentences = [segment.strip() for segment in SENTENCE_SPLIT_RE.split(clean_text(text)) if segment.strip()]
    return sentences


def extract_signals(sentences: list[str], keywords: list[str], limit: int = 3) -> list[str]:
    results = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword.lower() in sentence_lower for keyword in keywords):
            results.append(sentence)
        if len(results) >= limit:
            break
    return results


def extract_evidence(sentences: list[str], entities: list[str], topic: str, limit: int = 3) -> list[str]:
    topic_terms = topic.split()
    evidence = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(entity.lower() in sentence_lower for entity in entities) or any(term.lower() in sentence_lower for term in topic_terms):
            evidence.append(sentence)
        if len(evidence) >= limit:
            break
    if evidence:
        return evidence[:limit]
    return sentences[: min(limit, len(sentences))]


def _unique_non_blank(values: list[Any], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for value in values:
        text = clean_text(str(value))
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(text)
        if limit is not None and len(results) >= limit:
            break
    return results


def _coerce_llm_payload(payload: dict[str, Any], base: StructuredNews, raw_item: dict[str, Any]) -> StructuredNews:
    text = f"{raw_item.get('title', '')}\n{raw_item.get('content', '')}".strip()
    summary = clean_text(str(payload.get('summary', base.summary))) or base.summary
    entities = _unique_non_blank(payload.get('entities', base.entities), limit=5) or base.entities
    topic = str(payload.get('topic', base.topic)).strip()
    if topic not in VALID_TOPICS:
        topic = base.topic if base.topic in VALID_TOPICS else infer_topic(text)
    event_type = str(payload.get('event_type', base.event_type)).strip()
    if event_type not in VALID_EVENT_TYPES:
        event_type = base.event_type if base.event_type in VALID_EVENT_TYPES else infer_event_type(text)
    risk_signals = _unique_non_blank(payload.get('risk_signals', base.risk_signals), limit=3)
    opportunity_signals = _unique_non_blank(payload.get('opportunity_signals', base.opportunity_signals), limit=3)
    evidence = _unique_non_blank(payload.get('evidence', base.evidence), limit=3) or base.evidence

    return StructuredNews(
        id=base.id,
        title=base.title,
        source=base.source,
        published_at=base.published_at,
        language=base.language,
        summary=summary,
        entities=entities,
        topic=topic,
        event_type=event_type,
        region=base.region,
        importance_score=base.importance_score,
        sentiment=base.sentiment,
        risk_signals=risk_signals,
        opportunity_signals=opportunity_signals,
        evidence=evidence,
    )


def rule_based_extract(item: dict[str, Any]) -> StructuredNews:
    title = item.get('title', '')
    content = clean_text(item.get('content', ''))
    source = item.get('source', '')
    language = normalize_language(f'{title} {content}', item.get('language', 'en'))
    text = f'{title}\n{content}'.strip()
    entities = infer_entities(text)
    topic = infer_topic(text)
    event_type = infer_event_type(text)
    region = infer_region(source, language, text)
    sentiment = infer_sentiment(text)
    importance_score = infer_importance_score(text)
    sentences = split_sentences(content or title)
    risk_signals = extract_signals(sentences, RISK_KEYWORDS)
    opportunity_signals = extract_signals(sentences, OPPORTUNITY_KEYWORDS)
    evidence = extract_evidence(sentences, entities, topic)
    summary = summarize_text(content or title, language)
    keywords = extract_keywords(text, language, top_k=8)
    if not entities and keywords:
        entities = keywords[:2]
    if not evidence:
        evidence = [summary or title]

    return StructuredNews(
        id=item['id'],
        title=title,
        source=source,
        published_at=item['published_at'],
        language=language,
        summary=summary or title,
        entities=entities,
        topic=topic,
        event_type=event_type,
        region=region,
        importance_score=importance_score,
        sentiment=sentiment,
        risk_signals=risk_signals,
        opportunity_signals=opportunity_signals,
        evidence=evidence,
    )


def llm_enhance(structured: StructuredNews, raw_item: dict[str, Any], llm_client: Any = None) -> StructuredNews:
    # LLM 仅做增强，任何失败都必须退回规则结果，避免破坏流水线可运行性。
    if llm_client is None:
        return structured

    prompt_template = ENHANCE_PROMPT_PATH.read_text(encoding='utf-8')
    system_prompt = prompt_template
    user_prompt = json.dumps(
        {
            'title': raw_item.get('title', ''),
            'source': raw_item.get('source', ''),
            'language': raw_item.get('language', structured.language),
            'content': raw_item.get('content', ''),
            'rule_based': structured.to_dict(),
        },
        ensure_ascii=False,
        indent=2,
    )
    try:
        payload = llm_client.chat_json(system_prompt, user_prompt)
    except Exception:
        return structured

    try:
        return _coerce_llm_payload(payload, structured, raw_item)
    except (TypeError, ValueError):
        return structured
