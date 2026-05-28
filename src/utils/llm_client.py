from __future__ import annotations

import json
import logging
import re
from typing import Any

import requests


logger = logging.getLogger(__name__)
JSON_FENCE_RE = re.compile(r'```(?:json)?\s*(.*?)```', re.DOTALL | re.IGNORECASE)


class LLMCallError(RuntimeError):
    pass


class LLMClient:
    # 兼容层把协议差异封装在这里，避免污染 pipeline stage。
    def __init__(self, *, base_url: str, auth_token: str, model: str, timeout: int = 30, max_tokens: int = 800, temperature: float = 0.2) -> None:
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        errors: list[str] = []
        for endpoint, payload, parser in self._request_variants(system_prompt, user_prompt):
            try:
                response = requests.post(endpoint, headers=self._headers(), json=payload, timeout=self.timeout)
            except requests.RequestException as exc:  # pragma: no cover - exercised via tests with mocks
                errors.append(f'{endpoint}: request failed: {exc}')
                continue

            if response.status_code >= 400:
                errors.append(f'{endpoint}: http {response.status_code} {response.text[:200]}')
                continue

            try:
                body = response.json()
                text = parser(body)
                parsed = self._extract_json_payload(text)
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                errors.append(f'{endpoint}: invalid response payload: {exc}')
                continue

            if isinstance(parsed, dict):
                return parsed
            raise LLMCallError(f'{endpoint}: expected JSON object response')

        raise LLMCallError(' | '.join(errors) or 'llm call failed')

    def _headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.auth_token}',
            'x-api-key': self.auth_token,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        }

    def _request_variants(self, system_prompt: str, user_prompt: str) -> list[tuple[str, dict[str, Any], Any]]:
        return [
            (self._anthropic_endpoint(), self._anthropic_payload(system_prompt, user_prompt), self._parse_anthropic_text),
            (self._openai_endpoint(), self._openai_payload(system_prompt, user_prompt), self._parse_openai_text),
        ]

    def _anthropic_endpoint(self) -> str:
        if self.base_url.endswith('/v1/messages'):
            return self.base_url
        if self.base_url.endswith('/v1'):
            return f'{self.base_url}/messages'
        return f'{self.base_url}/v1/messages'

    def _openai_endpoint(self) -> str:
        if self.base_url.endswith('/v1/chat/completions'):
            return self.base_url
        if self.base_url.endswith('/v1'):
            return f'{self.base_url}/chat/completions'
        return f'{self.base_url}/v1/chat/completions'

    def _anthropic_payload(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': user_prompt}],
        }

    def _openai_payload(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'response_format': {'type': 'json_object'},
        }

    def _parse_anthropic_text(self, payload: dict[str, Any]) -> str:
        content = payload['content']
        if not isinstance(content, list):
            raise ValueError('anthropic content must be a list')
        blocks = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                blocks.append(str(block.get('text', '')))
        if not blocks:
            raise ValueError('anthropic response has no text blocks')
        return '\n'.join(blocks)

    def _parse_openai_text(self, payload: dict[str, Any]) -> str:
        choices = payload['choices']
        if not isinstance(choices, list) or not choices:
            raise ValueError('openai response has no choices')
        message = choices[0].get('message', {})
        content = message.get('content')
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    parts.append(str(item.get('text', '')))
            if parts:
                return '\n'.join(parts)
        raise ValueError('openai response has no text content')

    def _extract_json_payload(self, text: str) -> Any:
        fenced = JSON_FENCE_RE.search(text)
        candidate = fenced.group(1).strip() if fenced else text.strip()
        if candidate.startswith('{') or candidate.startswith('['):
            return json.loads(candidate)

        start = candidate.find('{')
        end = candidate.rfind('}')
        if start != -1 and end != -1 and end > start:
            return json.loads(candidate[start:end + 1])
        raise json.JSONDecodeError('no json object found', candidate, 0)


def build_llm_client(config: dict[str, Any]) -> LLMClient | None:
    llm_config = config.get('llm', {}) if isinstance(config.get('llm'), dict) else {}
    if not llm_config.get('enabled'):
        return None

    return LLMClient(
        base_url=str(llm_config['base_url']),
        auth_token=str(llm_config['auth_token']),
        model=str(llm_config['model']),
        timeout=int(llm_config.get('timeout', 30)),
        max_tokens=int(llm_config.get('max_tokens', 800)),
        temperature=float(llm_config.get('temperature', 0.2)),
    )
