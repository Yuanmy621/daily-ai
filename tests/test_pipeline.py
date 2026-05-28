from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RUNNER = BASE_DIR / 'scripts' / 'run_daily.py'


class PipelineTest(unittest.TestCase):
    def test_scaffold_pipeline_runs(self) -> None:
        date = '2026-05-27'
        result = subprocess.run(
            ['python3', str(RUNNER), '--date', date],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        raw_path = BASE_DIR / 'data' / 'raw' / f'raw_news_{date}.json'
        normalized_path = BASE_DIR / 'data' / 'normalized' / f'normalized_news_{date}.json'
        structured_path = BASE_DIR / 'data' / 'structured' / f'structured_news_{date}.json'
        insight_path = BASE_DIR / 'outputs' / 'insights' / f'daily_insight_{date}.json'
        report_path = BASE_DIR / 'outputs' / 'reports' / f'daily_report_{date}.md'
        visualization_json_path = BASE_DIR / 'outputs' / 'visualizations' / f'visualization_{date}.json'
        visualization_html_path = BASE_DIR / 'outputs' / 'visualizations' / f'visualization_{date}.html'

        self.assertTrue(raw_path.exists())
        self.assertTrue(normalized_path.exists())
        self.assertTrue(structured_path.exists())
        self.assertTrue((BASE_DIR / 'data' / 'clusters' / f'clusters_{date}.json').exists())
        self.assertTrue(insight_path.exists())
        self.assertTrue(report_path.exists())
        self.assertTrue(visualization_json_path.exists())
        self.assertTrue(visualization_html_path.exists())

        raw_payload = json.loads(raw_path.read_text(encoding='utf-8'))
        normalized_payload = json.loads(normalized_path.read_text(encoding='utf-8'))
        structured_payload = json.loads(structured_path.read_text(encoding='utf-8'))
        insight_payload = json.loads(insight_path.read_text(encoding='utf-8'))
        visualization_payload = json.loads(visualization_json_path.read_text(encoding='utf-8'))
        report_text = report_path.read_text(encoding='utf-8')
        html_text = visualization_html_path.read_text(encoding='utf-8')

        self.assertGreaterEqual(len(raw_payload.get('articles', [])), 10)
        self.assertGreaterEqual(len(normalized_payload.get('articles', [])), 10)
        self.assertGreaterEqual(len(structured_payload.get('articles', [])), 10)
        self.assertGreaterEqual(len(insight_payload.get('top_events', [])), 1)
        self.assertGreaterEqual(len(visualization_payload.get('charts', [])), 3)

        structured_article = structured_payload['articles'][0]
        self.assertNotEqual(structured_article['entities'], ['Sample AI Company'])
        self.assertNotEqual(structured_article['topic'], 'foundation model' if structured_article['title'] == 'Sample AI news collected for scaffold pipeline' else 'sample_event')
        self.assertTrue(structured_article['evidence'])
        self.assertNotEqual(structured_article['summary'], '')

        self.assertIn('## 今日热点', report_text)
        self.assertIn('## 重点事件分析', report_text)
        self.assertIn('## 趋势观察', report_text)
        self.assertIn('## 风险与机会', report_text)
        self.assertIn('交互式可视化', report_text)

        self.assertIn('<html', html_text.lower())
        self.assertIn('Daily AI Insight Report', html_text)
        self.assertIn('chart-hot-events', html_text)
        self.assertIn('echarts', html_text.lower())


if __name__ == '__main__':
    unittest.main()
