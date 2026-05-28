from __future__ import annotations

import unittest

from src.analysis.extractor import StructuredNews, llm_enhance


class BrokenClient:
    def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise RuntimeError('boom')


class ExtractLLMFallbackTest(unittest.TestCase):
    def test_llm_enhance_falls_back_to_rule_result(self) -> None:
        base = StructuredNews(
            id='news_001',
            title='OpenAI launches GPT-5',
            source='Example',
            published_at='2026-05-27T08:00:00Z',
            language='en',
            summary='OpenAI launched GPT-5.',
            entities=['OpenAI'],
            topic='foundation model',
            event_type='product_release',
            region='global',
            importance_score=8.0,
            sentiment='positive',
            risk_signals=['competition intensifies'],
            opportunity_signals=['enterprise adoption'],
            evidence=['OpenAI launched GPT-5.'],
        )
        item = {
            'title': 'OpenAI launches GPT-5',
            'source': 'Example',
            'language': 'en',
            'content': 'OpenAI launched GPT-5 with stronger multimodal reasoning.',
        }
        enhanced = llm_enhance(base, item, llm_client=BrokenClient())
        self.assertEqual(enhanced.to_dict(), base.to_dict())


if __name__ == '__main__':
    unittest.main()
