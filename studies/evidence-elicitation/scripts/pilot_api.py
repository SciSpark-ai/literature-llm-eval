"""Explicit provider allowlist, no automatic retries, persistent request cache."""
import hashlib
import json
import os
import time
from pathlib import Path
import httpx
from pilot_core import Budget

MODELS = {
    'llm4o': ('gpt-4o-mini-2024-07-18', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', .15, .60),
    'embedding': ('text-embedding-3-small', 'https://api.openai.com/v1/embeddings', 'OPENAI_API_KEY', .02, 0.),
    'llm': ('gpt-4.1-mini-2025-04-14', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', .40, 1.60),
    'ce': ('jina-reranker-v2-base-multilingual', 'https://api.jina.ai/v1/rerank', 'JINA_API_KEY', .05, 0.),
}


class API:
    def __init__(self, directory, keys, transport=None, max_output_tokens=4096):
        if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 8192:
            raise ValueError("Invalid configured output cap")
        self.max_output_tokens = max_output_tokens
        self.directory = Path(directory)
        self.cache = self.directory / 'api-cache'
        self.cache.mkdir(parents=True, exist_ok=True)
        self.keys = keys
        self.budget = Budget(self.directory / 'budget.jsonl')
        self.transport = transport

    def call(self, provider, body):
        if provider not in MODELS:
            raise ValueError('Unknown provider')
        model, url, key_name, input_rate, output_rate = MODELS[provider]
        if body.get('model') != model:
            raise ValueError('Unpriced or unapproved model')
        max_output = body.get('max_tokens', 0)
        if type(max_output) is not int or max_output < 0 or max_output > self.max_output_tokens or (provider in ('llm', 'llm4o') and max_output == 0):
            raise ValueError('Invalid output cap')
        raw = json.dumps(body, sort_keys=True, ensure_ascii=False)
        if len(raw.encode()) > 150_000:
            raise ValueError('Pilot request exceeds input-size limit')
        identifier = hashlib.sha256((url + '\n' + raw).encode()).hexdigest()
        cache_path = self.cache / (identifier + '.json')
        if cache_path.exists():
            return json.loads(cache_path.read_text())['response']
        key = self.keys.get(key_name)
        if not key or key.startswith('${'):
            raise RuntimeError('Missing provider credential: ' + key_name)
        # Conservative byte-based allowance also covers framing and chunking.
        ceiling = max(.01, ((4 * len(raw.encode()) + 4096) * input_rate + max_output * output_rate) / 1_000_000)
        self.budget.reserve(identifier, ceiling)
        started = time.monotonic()
        try:
            with httpx.Client(timeout=90, transport=self.transport) as client:
                r = client.post(url, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, content=raw.encode())
        except httpx.HTTPError as error:
            self.budget.finish(identifier, None, type(error).__name__)
            raise RuntimeError('Provider transport failed: ' + type(error).__name__) from None
        if r.status_code != 200:
            # Error bodies may echo secrets. Do not persist or print them.
            self.budget.finish(identifier, None, 'HTTP_' + str(r.status_code))
            raise RuntimeError('Provider failed: HTTP_' + str(r.status_code))
        try:
            result = r.json()
        except ValueError:
            self.budget.finish(identifier, None, 'invalid_response_json')
            raise RuntimeError('Provider returned invalid JSON') from None
        usage = result.get('usage', {})
        if provider in ('llm', 'llm4o'):
            actual = (usage['prompt_tokens'] * input_rate + usage['completion_tokens'] * output_rate) / 1_000_000 if 'prompt_tokens' in usage and 'completion_tokens' in usage else None
        else:
            actual = usage['total_tokens'] * input_rate / 1_000_000 if 'total_tokens' in usage else None
        self.budget.finish(identifier, actual, 'success' if actual is not None else 'success_usage_unknown')
        payload = {'provider': provider, 'request': body, 'response': result, 'elapsed_seconds': time.monotonic() - started, 'estimated_usd_at_verified_list_rate': actual, 'reservation_usd': ceiling}
        temporary = cache_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(payload, ensure_ascii=False) + '\n')
        os.replace(temporary, cache_path)
        return result
