from __future__ import annotations

import unittest
from pathlib import Path

from src.pipeline import stage_4_cluster


class ClusterStageTest(unittest.TestCase):
    def test_cluster_groups_articles_by_signals(self) -> None:
        articles = [
            {
                'id': 'news_001',
                'title': 'OpenAI launches GPT-5 for enterprise agents',
                'summary': 'OpenAI released GPT-5 with stronger multimodal reasoning for enterprise agent workflows.',
                'language': 'en',
                'topic': 'foundation model',
                'event_type': 'product_release',
                'entities': ['OpenAI', 'GPT-5'],
                'importance_score': 8.5,
                'risk_signals': ['competition intensifies'],
                'opportunity_signals': ['enterprise adoption'],
                'evidence': ['OpenAI released GPT-5 with stronger multimodal reasoning.'],
            },
            {
                'id': 'news_002',
                'title': 'Meta releases Llama 4 open source model',
                'summary': 'Meta released Llama 4 and expanded open model adoption.',
                'language': 'en',
                'topic': 'foundation model',
                'event_type': 'product_release',
                'entities': ['Meta', 'Llama 4'],
                'importance_score': 7.5,
                'risk_signals': [],
                'opportunity_signals': ['open model adoption'],
                'evidence': ['Meta released Llama 4 for enterprise adoption.'],
            },
            {
                'id': 'news_003',
                'title': 'EU AI Act enforcement begins',
                'summary': 'The European Union started enforcing the AI Act for high-risk systems.',
                'language': 'en',
                'topic': 'ai policy',
                'event_type': 'policy_regulation',
                'entities': ['European Union'],
                'importance_score': 8.0,
                'risk_signals': ['new compliance requirements'],
                'opportunity_signals': [],
                'evidence': ['The European Union started enforcing the AI Act.'],
            },
        ]

        clusters = stage_4_cluster.run('2026-05-27', {
            'naming': {'structured': 'structured_news_{date}.json', 'clusters': 'clusters_{date}.json'}
        })
        self.assertIn('count', clusters)

        payload = stage_4_cluster._build_cluster_payload('2026-05-27', 1, articles[:2])
        self.assertNotEqual(payload['headline'], 'Sample AI hotspot cluster')
        self.assertGreater(payload['heat_score'], 0)
        self.assertTrue(payload['representative_points'])

        score_same_topic = stage_4_cluster._cluster_match_score(articles[1], {
            'topic': 'foundation model',
            'event_type': 'product_release',
            'entity_set': {'OpenAI'},
            'keyword_set': {'model', 'release'},
        })
        score_other_topic = stage_4_cluster._cluster_match_score(articles[2], {
            'topic': 'foundation model',
            'event_type': 'product_release',
            'entity_set': {'OpenAI'},
            'keyword_set': {'model', 'release'},
        })
        self.assertGreater(score_same_topic, score_other_topic)


if __name__ == '__main__':
    unittest.main()
