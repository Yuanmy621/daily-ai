from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from src.utils.llm_client import LLMCallError, build_llm_client


class LLMClientTest(unittest.TestCase):
    def test_build_client_returns_none_when_disabled(self) -> None:
        self.assertIsNone(build_llm_client({'llm': {'enabled': False}}))

    @patch('src.utils.llm_client.requests.post')
    def test_chat_json_parses_openai_compatible_response(self, mock_post: Mock) -> None:
        from src.utils.llm_client import LLMClient

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'bad anthropic route'

        mock_response_ok = Mock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {
            'choices': [{'message': {'content': '{"summary":"ok"}'}}]
        }
        mock_post.side_effect = [mock_response, mock_response_ok]

        client = LLMClient(
            base_url='https://example.com/llm',
            auth_token='token',
            model='demo-model',
        )
        payload = client.chat_json('system', 'user')
        self.assertEqual(payload['summary'], 'ok')

    @patch('src.utils.llm_client.requests.post')
    def test_chat_json_raises_on_total_failure(self, mock_post: Mock) -> None:
        from src.utils.llm_client import LLMClient

        mock_post.side_effect = requests.Timeout('timeout')
        client = LLMClient(
            base_url='https://example.com/llm',
            auth_token='token',
            model='demo-model',
        )
        with self.assertRaises(LLMCallError):
            client.chat_json('system', 'user')


if __name__ == '__main__':
    unittest.main()
