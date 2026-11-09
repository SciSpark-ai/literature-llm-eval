"""Single-attempt paid transport for E4 repeat runs. The `user` tag makes each repeat a distinct
request body so the persistent cache cannot return an earlier run's response. Authorized lane: $20."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE_USD = 20  # owner raised the ceiling from 10 to 20 USD on 2026-10-09
SKIP = {'$schema', 'minItems', 'maxItems', 'minLength', 'maxLength', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'pattern', 'minProperties', 'maxProperties', 'format'}


def clean(x):
    if isinstance(x, list):
        return [clean(v) for v in x]
    if not isinstance(x, dict):
        return x
    return {k: ({n: clean(s) for n, s in v.items()} if k in {'properties', '$defs', 'definitions', 'patternProperties'} else clean(v)) for k, v in x.items() if k not in SKIP}


def build_bodies(requests, tag):
    bodies = []
    for r in requests:
        q = r['req']
        bodies.append({'model': r['model'], 'messages': q['messages'], 'max_tokens': q['maxTokens'], 'temperature': q['temperature'], 'user': tag,
                       'response_format': {'type': 'json_schema', 'json_schema': {'name': 'result', 'strict': False, 'schema': clean(q['jsonSchema'])}}})
    return bodies


def ceiling_usd(bodies):
    return sum(math.ceil(max(.01, ((4 * len(json.dumps(b, sort_keys=True, ensure_ascii=False).encode()) + 4096) * .4 + b['max_tokens'] * 1.6) / 1e6) * 1e6) for b in bodies) / 1e6


def reserved_usd(ledger):
    rows = [json.loads(l) for l in Path(ledger).read_text().splitlines() if l.strip()] if Path(ledger).exists() else []
    return sum(r['ceiling_microusd'] for r in rows if r['event'] == 'reserved') / 1e6


def call_provider(bodies, requests, out):
    from pilot import provider
    from pilot_api import API
    from pilot_core import Budget
    api = API(ROOT, provider().keys, max_output_tokens=8192)
    api.budget = Budget(ROOT / 'budget.jsonl', limit_usd=LANE_USD, lane_limit_usd=LANE_USD)
    output = {}
    for request, body in zip(requests, bodies):
        output[request['id']] = api.call('llm', body)
        Path(out).write_text(json.dumps(output))
        print('Completed %d/%d' % (len(output), len(bodies)), flush=True)


def main(requests, tag, run, ledger, out):
    bodies = build_bodies(requests, tag)
    new = ceiling_usd(bodies)
    prev = reserved_usd(ledger)
    print(json.dumps({'requests': len(bodies), 'tag': tag, 'new_ceiling': new, 'previous_reserved': prev, 'combined': prev + new}), flush=True)
    if prev + new > LANE_USD:
        raise RuntimeError('Authorized $%d lane would be exceeded; stop' % LANE_USD)
    if run:
        call_provider(bodies, requests, out)


if __name__ == '__main__':
    name, tag = sys.argv[1], sys.argv[2]
    d = ROOT / 'runs' / name
    reqs = json.loads((d / 'stage-a-requests.json').read_text())
    if (d / 'stage-a-responses.json').exists():
        raise RuntimeError('Responses already exist for ' + name + '; refusing to overwrite')
    main(reqs, tag, run='--run' in sys.argv, ledger=ROOT / 'budget.jsonl', out=d / 'stage-a-responses.json')
