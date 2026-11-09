import json
import sys
from pathlib import Path
import httpx
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_api import API


def test_cache_reuses_response_without_new_spend_or_request(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={'data': [{'index': 0, 'embedding': [0.5]}], 'usage': {'prompt_tokens': 5, 'total_tokens': 5}})
    api = API(tmp_path, {'OPENAI_API_KEY': 'secret'}, transport=httpx.MockTransport(handler))
    body = {'model': 'text-embedding-3-small', 'input': ['test'], 'dimensions': 768}
    a = api.call('embedding', body)
    b = api.call('embedding', body)
    assert a == b
    assert len(calls) == 1
    assert len((tmp_path / 'budget.jsonl').read_text().splitlines()) == 2
    assert 'secret' not in ''.join(p.read_text() for p in tmp_path.rglob('*.json*'))


def test_auth_failure_is_redacted_and_never_automatically_retried(tmp_path):
    def handler(request):
        return httpx.Response(401, json={'error': {'message': 'Incorrect API key provided: sk-secret'}})
    api = API(tmp_path, {'OPENAI_API_KEY': 'sk-secret'}, transport=httpx.MockTransport(handler))
    body = {'model': 'text-embedding-3-small', 'input': ['test'], 'dimensions': 768}
    with pytest.raises(RuntimeError, match='HTTP_401'):
        api.call('embedding', body)
    with pytest.raises(ValueError, match='already reserved'):
        api.call('embedding', body)
    assert 'sk-secret' not in ''.join(p.read_text() for p in tmp_path.rglob('*.json*'))


def test_unpriced_model_and_oversized_output_are_blocked(tmp_path):
    api = API(tmp_path, {'OPENAI_API_KEY': 'secret'})
    with pytest.raises(ValueError):
        api.call('llm', {'model': 'unknown-expensive-model', 'max_tokens': 4096})
    with pytest.raises(ValueError):
        api.call('llm', {'model': 'gpt-4.1-mini-2025-04-14', 'max_tokens': 999999})
    assert not (tmp_path / 'budget.jsonl').exists()


def test_explicit_clinical_output_cap(tmp_path):
    import pytest
    from pilot_api import API
    with pytest.raises(ValueError):
        API(tmp_path, {}, max_output_tokens=8193)
    api = API(tmp_path, {}, max_output_tokens=8192)
    with pytest.raises(RuntimeError, match='Missing provider credential'):
        api.call('llm', {'model': 'gpt-4.1-mini-2025-04-14', 'max_tokens': 8192})


def test_4o_snapshot_usage_is_charged_at_its_own_rate(tmp_path):
    def handler(request):
        return httpx.Response(200, json={'usage': {'prompt_tokens': 1000, 'completion_tokens': 100}, 'choices': []})
    api = API(tmp_path, {'OPENAI_API_KEY': 'test'}, transport=httpx.MockTransport(handler))
    api.call('llm4o', {'model': 'gpt-4o-mini-2024-07-18', 'max_tokens': 100})
    events = [json.loads(line) for line in (tmp_path / 'budget.jsonl').read_text().splitlines()]
    assert events[-1]['estimated_microusd'] == 210
    with pytest.raises(ValueError):
        api.call('llm4o', {'model': 'gpt-4o-mini-2024-07-18', 'max_tokens': 0})
