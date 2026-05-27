from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CHECK = BASE_DIR / 'check.py'


class CheckScriptTest(unittest.TestCase):
    def test_normalized_sample_passes(self) -> None:
        sample = [
            {
                'id': 'news_001',
                'title': 'OpenAI releases a new AI model for enterprise automation',
                'source': 'Example',
                'published_at': '2026-05-27T08:00:00Z',
                'url': 'https://example.com/news/1',
                'language': 'en',
                'content': 'OpenAI released a new AI model with enterprise automation features and stronger reasoning performance.',
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / 'sample.json'
            sample_path.write_text(json.dumps(sample), encoding='utf-8')
            result = subprocess.run(
                ['python3', str(CHECK), str(sample_path), '--schema', 'normalized', '--min-count', '1'],
                capture_output=True,
                text=True,
                cwd=BASE_DIR,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS', result.stdout)


if __name__ == '__main__':
    unittest.main()
