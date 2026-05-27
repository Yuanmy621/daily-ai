from __future__ import annotations

import re
from collections import Counter

try:
    import jieba.analyse  # type: ignore
except Exception:  # pragma: no cover
    jieba = None
else:  # pragma: no cover
    import jieba  # type: ignore


EN_STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'to', 'of', 'in',
    'for', 'on', 'with', 'at', 'by', 'from', 'as', 'and', 'or', 'that', 'this', 'these', 'those',
    'has', 'have', 'had', 'will', 'would', 'can', 'could', 'may', 'might', 'into', 'about', 'across',
}


def extract_keywords_en(text: str, top_k: int = 10) -> list[str]:
    words = re.findall(r'[a-zA-Z]{2,}', text.lower())
    counts = Counter(word for word in words if word not in EN_STOPWORDS)
    return [word for word, _ in counts.most_common(top_k)]


def extract_keywords_zh(text: str, top_k: int = 10) -> list[str]:
    if jieba is None:
        return []
    return jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)


def extract_keywords(text: str, language: str, top_k: int = 10) -> list[str]:
    if language == 'zh':
        return extract_keywords_zh(text, top_k)
    return extract_keywords_en(text, top_k)
