"""E5: evidence extraction as a second call after a decision. Modes: free verbatim quote, or sentence selection."""
import json
import math
import sys
from pathlib import Path
import e45_lib as L

STUDY = L.STUDY
MODEL = 'gpt-4.1-mini-2025-04-14'
LANE_USD = 20  # owner raised the ceiling from 10 to 20 USD on 2026-10-09
MAX_TOKENS = 2048
SYSTEM_QUOTE = ('You are given a clinician watch entry, several papers (title and abstract), and the relevance grade already assigned to each paper. '
                'For each paper return ONE short, exact, contiguous excerpt of 8-160 characters copied VERBATIM from its title or abstract that best supports the assigned grade. '
                'Do not paraphrase, concatenate separate passages, insert ellipses, or add words. Do not change or comment on the grade. '
                'Return JSON {"evidence":[{"index":<paper index>,"quote":"<excerpt>"}]} with exactly one entry per paper.')
SYSTEM_SENTENCE = ('You are given a clinician watch entry, several papers split into numbered sentences, and the relevance grade already assigned to each paper. '
                   'For each paper choose the ONE sentence number that best supports the assigned grade. Do not change or comment on the grade. '
                   'Return JSON {"evidence":[{"index":<paper index>,"sentence":<sentence number>}]} with exactly one entry per paper.')
SCHEMA = {'quote': {'type': 'object', 'properties': {'evidence': {'type': 'array', 'items': {'type': 'object', 'properties': {'index': {'type': 'integer'}, 'quote': {'type': 'string'}}, 'required': ['index', 'quote'], 'additionalProperties': False}}}, 'required': ['evidence'], 'additionalProperties': False},
          'sentence': {'type': 'object', 'properties': {'evidence': {'type': 'array', 'items': {'type': 'object', 'properties': {'index': {'type': 'integer'}, 'sentence': {'type': 'integer'}}, 'required': ['index', 'sentence'], 'additionalProperties': False}}}, 'required': ['evidence'], 'additionalProperties': False}}


def select_items(source_run, only_failures):
    grades = L.load_stage_a(source_run)
    try:
        texts = L.candidate_text(source_run)
    except L.AbstractsMissing:
        # Public export without abstract text: items can still be listed and counted, not sent.
        texts = {k: '' for k in grades}
    items = []
    for (topic, pmid), g in grades.items():
        if g['model'] <= 0:
            continue
        if only_failures and g['qv']:
            continue
        items.append({'topic': topic, 'pmid': pmid, 'grade': g['model'], 'text': texts[(topic, pmid)]})
    return items


def load_watches():
    config = json.loads((STUDY / 'runs/clinical-v1/config.json').read_text())
    return {t['id']: {k: v for k, v in t['watch'].items() if k in ('condition', 'condition2', 'conditionJoin', 'treatment', 'population', 'outcome')} for t in config['topics']}


def build_requests(items, mode, watches, batch=20):
    requests = []
    by_topic = {}
    for it in items:
        by_topic.setdefault(it['topic'], []).append(it)
    for topic in sorted(by_topic):
        group = by_topic[topic]
        for start in range(0, len(group), batch):
            chunk = group[start:start + batch]
            papers = []
            for i, it in enumerate(chunk):
                title, _, abstract = it['text'].partition('\n')
                paper = {'index': i, 'assignedGrade': it['grade']}
                if mode == 'quote':
                    paper.update({'title': title, 'abstract': abstract})
                else:
                    paper['sentences'] = [[n, s] for n, s in enumerate(L.split_sentences(it['text']))]
                papers.append(paper)
            user = json.dumps({'watchEntry': watches[topic], 'papers': papers}, ensure_ascii=False)
            body = {'model': MODEL, 'temperature': 0, 'max_tokens': MAX_TOKENS,
                    'messages': [{'role': 'system', 'content': SYSTEM_QUOTE if mode == 'quote' else SYSTEM_SENTENCE}, {'role': 'user', 'content': user}],
                    'response_format': {'type': 'json_schema', 'json_schema': {'name': 'evidence', 'strict': False, 'schema': SCHEMA[mode]}}}
            requests.append({'topic': topic, 'indices': [it['pmid'] for it in chunk], 'body': body})
    return requests


def parse_response(mode, request, response_json, items_by_pmid):
    content = json.loads(response_json['choices'][0]['message']['content'])
    entries = content['evidence']
    idx = [e.get('index') for e in entries]
    n_papers = len(request['indices'])
    # Out-of-range, non-integer or duplicated indices could attach evidence to the wrong paper: refuse.
    if any(type(i) is not int or not 0 <= i < n_papers for i in idx) or len(set(idx)) != len(idx):
        raise ValueError('Response indices %s are invalid or duplicated for a request of %d papers' % (idx, n_papers))
    by_index = {e['index']: e for e in entries}
    out = []
    for position, pmid in enumerate(request['indices']):
        it = items_by_pmid[(request['topic'], pmid)]
        e = by_index.get(position)
        if e is None:
            # The model returned no entry for this paper. That is an outcome (no evidence offered), recorded
            # explicitly and counted as unverified; it cannot misalign the entries that were returned.
            out.append({'topic': request['topic'], 'pmid': pmid, 'grade': it['grade'], 'evidence': '', 'tier': 'none', 'omitted': True})
            continue
        if mode == 'quote':
            evidence = e.get('quote', '')
        else:
            sentences = L.split_sentences(it['text'])
            n = e.get('sentence')
            evidence = sentences[n] if isinstance(n, int) and 0 <= n < len(sentences) else ''
        out.append({'topic': request['topic'], 'pmid': pmid, 'grade': it['grade'], 'evidence': evidence, 'tier': L.match_tier(evidence, it['text']) if evidence else 'none', 'omitted': False})
    return out


def ceiling_usd(bodies):
    return sum(math.ceil(max(.01, ((4 * len(json.dumps(b, sort_keys=True, ensure_ascii=False).encode()) + 4096) * .4 + b['max_tokens'] * 1.6) / 1e6) * 1e6) for b in bodies) / 1e6


def write_results(mode, requests, responses, items, out_dir):
    by_pmid = {(it['topic'], it['pmid']): it for it in items}
    results = []
    for r, resp in zip(requests, responses):
        results.extend(parse_response(mode, r, resp, by_pmid))
    (out_dir / 'results.json').write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(json.dumps({'results': len(results), 'omitted': sum(x['omitted'] for x in results), 'tiers': {t: sum(x['tier'] == t for x in results) for t in ('exact', 'normalized', 'elided', 'none')}}))


def main(argv):
    mode, source, out_name = argv[0], argv[1], argv[2]
    only_failures = '--only-failures' in argv
    run = '--run' in argv
    out_dir = STUDY / 'runs' / out_name
    out_dir.mkdir(exist_ok=True)
    items = select_items(STUDY / 'runs' / source, only_failures)
    requests = build_requests(items, mode, load_watches())
    if '--parse-only' in argv:
        # Offline: rebuild results.json from responses already paid for. No ledger access, no network.
        if json.loads((out_dir / 'requests.json').read_text())['requests'] != requests:
            raise ValueError('Rebuilt requests differ from the saved requests; refusing to parse')
        responses = json.loads((out_dir / 'responses.json').read_text())
        if len(responses) != len(requests):
            raise ValueError('Saved responses (%d) differ in number from requests (%d)' % (len(responses), len(requests)))
        write_results(mode, requests, responses, items, out_dir)
        return
    (out_dir / 'requests.json').write_text(json.dumps({'mode': mode, 'source': source, 'only_failures': only_failures, 'n_items': len(items), 'requests': requests}, indent=1, ensure_ascii=False))
    rows = [json.loads(l) for l in (STUDY / 'budget.jsonl').read_text().splitlines() if l.strip()]
    prev = sum(r['ceiling_microusd'] for r in rows if r['event'] == 'reserved') / 1e6
    new = ceiling_usd([r['body'] for r in requests])
    print(json.dumps({'mode': mode, 'source': source, 'items': len(items), 'requests': len(requests), 'new_ceiling': new, 'previous_reserved': prev, 'combined': prev + new}), flush=True)
    if prev + new > LANE_USD:
        raise RuntimeError('Authorized $%d lane would be exceeded; stop' % LANE_USD)
    if not run:
        return
    if (out_dir / 'responses.json').exists():
        raise RuntimeError('Responses already exist; refusing to overwrite')
    from pilot import provider
    from pilot_api import API
    from pilot_core import Budget
    api = API(STUDY, provider().keys, max_output_tokens=MAX_TOKENS)
    api.budget = Budget(STUDY / 'budget.jsonl', limit_usd=LANE_USD, lane_limit_usd=LANE_USD)
    responses = []
    for i, r in enumerate(requests):
        responses.append(api.call('llm', r['body']))
        (out_dir / 'responses.json').write_text(json.dumps(responses))
        print('Completed %d/%d' % (i + 1, len(requests)), flush=True)
    write_results(mode, requests, responses, items, out_dir)


if __name__ == '__main__':
    main(sys.argv[1:])
