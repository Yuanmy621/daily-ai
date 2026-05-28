from __future__ import annotations

import unittest

from src.pipeline import stage_5_insight


class InsightStageTest(unittest.TestCase):
    def test_rule_trend_insights_and_sample_size(self) -> None:
        clusters = [
            {
                'cluster_id': 'cluster_01',
                'topic': 'foundation model',
                'headline': 'OpenAI launches GPT-5',
                'news_ids': ['news_001', 'news_002'],
                'entities': ['OpenAI', 'GPT-5'],
                'heat_score': 8.7,
                'representative_points': ['OpenAI released GPT-5 with stronger multimodal reasoning.'],
            },
            {
                'cluster_id': 'cluster_02',
                'topic': 'ai policy',
                'headline': 'EU AI Act enforcement begins',
                'news_ids': ['news_003'],
                'entities': ['European Union'],
                'heat_score': 8.0,
                'representative_points': ['The European Union started enforcing the AI Act.'],
            },
        ]
        structured_articles = [
            {
                'id': 'news_001',
                'event_type': 'product_release',
                'risk_signals': ['competition intensifies'],
                'opportunity_signals': ['enterprise adoption'],
            },
            {
                'id': 'news_002',
                'event_type': 'product_release',
                'risk_signals': [],
                'opportunity_signals': ['open model adoption'],
            },
            {
                'id': 'news_003',
                'event_type': 'policy_regulation',
                'risk_signals': ['new compliance requirements'],
                'opportunity_signals': [],
            },
        ]
        cluster_articles = stage_5_insight._build_cluster_index(structured_articles, clusters)
        trend_insights = stage_5_insight._rule_trend_insights(clusters, cluster_articles)

        self.assertTrue(trend_insights['technology'])
        self.assertTrue(trend_insights['policy'])
        self.assertEqual(stage_5_insight._sample_size(clusters), 3)

        risk_alerts = stage_5_insight._signal_alerts(cluster_articles, 'risk_signals')
        opportunity_alerts = stage_5_insight._signal_alerts(cluster_articles, 'opportunity_signals')
        self.assertNotIn('sample risk alert', risk_alerts)
        self.assertNotIn('sample opportunity alert', opportunity_alerts)
        self.assertTrue(risk_alerts)
        self.assertTrue(opportunity_alerts)


if __name__ == '__main__':
    unittest.main()
