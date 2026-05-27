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

        self.assertTrue(raw_path.exists())
        self.assertTrue(normalized_path.exists())
        self.assertTrue(structured_path.exists())
        self.assertTrue((BASE_DIR / 'data' / 'clusters' / f'clusters_{date}.json').exists())
        self.assertTrue((BASE_DIR / 'outputs' / 'insights' / f'daily_insight_{date}.json').exists())
        self.assertTrue((BASE_DIR / 'outputs' / 'reports' / f'daily_report_{date}.md').exists())
        self.assertTrue((BASE_DIR / 'outputs' / 'visualizations' / f'visualization_{date}.json').exists())

        raw_payload = json.loads(raw_path.read_text(encoding='utf-8'))
        normalized_payload = json.loads(normalized_path.read_text(encoding='utf-8'))
        structured_payload = json.loads(structured_path.read_text(encoding='utf-8'))

        self.assertGreaterEqual(len(raw_payload.get('articles', [])), 10)
        self.assertGreaterEqual(len(normalized_payload.get('articles', [])), 10)
        self.assertGreaterEqual(len(structured_payload.get('articles', [])), 10)

        structured_article = structured_payload['articles'][0]
        self.assertNotEqual(structured_article['entities'], ['Sample AI Company'])
        self.assertNotEqual(structured_article['topic'], 'foundation model' if structured_article['title'] == 'Sample AI news collected for scaffold pipeline' else 'sample_event')
        self.assertTrue(structured_article['evidence'])
        self.assertNotEqual(structured_article['summary'], '')


if __name__ == '__main__':
    unittest.main()
