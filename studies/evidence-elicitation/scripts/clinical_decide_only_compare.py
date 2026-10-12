"""E3 paired analysis: decide-only (no quote requirement) versus the joint baseline and the contiguous-quote variant.

Development topics only; descriptive, no inference. Run after:
  python3 scripts/clinical_decide_only_paid.py --run
  node scripts/clinical_decide_only.mjs replay
"""
import json, collections
from pathlib import Path
R = Path(__file__).resolve().parents[1] / 'runs'
config = json.loads((R / 'clinical-v1/config.json').read_text())
labels = {(t['id'], r['pmid']): r for t in config['topics'] for r in t['records']}

def load(name):
    out = {}
    for t in json.loads((R / name / 'stage-a-results.json').read_text()):
        for rec in t['records']:
            g = rec['grade']
            out[(t['topic'], rec['pmid'])] = {'model': g.get('modelGrade') or 0, 'quote': g.get('quote') or '', 'qv': g['quoteVerified'], 'ungraded': g['ungraded']}
    return out

runs = {n: load(n) for n in ['clinical-v1', 'clinical-quote-v2', 'clinical-decide-only-v1']}
D = runs['clinical-decide-only-v1']
print('decide-only: ungraded', sum(v['ungraded'] for v in D.values()), '| non-empty quote fields', sum(bool(v['quote'].strip()) for v in D.values()), 'of', len(D))
responses = json.loads((R / 'clinical-decide-only-v1/stage-a-responses.json').read_text())
print('decide-only estimated_usd', sum((r['usage']['prompt_tokens'] * .4 + r['usage']['completion_tokens'] * 1.6) / 1e6 for r in responses.values()))

for topic in sorted({k[0] for k in D}):
    keys = [k for k in D if k[0] == topic]
    pos = [k for k in keys if labels[k]['abstract_label'] == 1]
    neg = [k for k in keys if labels[k]['abstract_label'] == 0]
    row = {'topic': topic, 'pos': len(pos), 'neg': len(neg)}
    for n, run in runs.items():
        row[n] = {'pos_grade>0': sum(run[k]['model'] > 0 for k in pos), 'neg_grade>0': sum(run[k]['model'] > 0 for k in neg)}
    print(json.dumps(row))

print('\n== self-gating check: abstract-positives with joint modelGrade 0 (v1) and their decide-only grade')
for n in ['clinical-v1', 'clinical-quote-v2']:
    zero = [k for k in D if labels[k]['abstract_label'] == 1 and runs[n][k]['model'] == 0]
    rescued = [k for k in zero if D[k]['model'] > 0]
    print(n, 'grade-0 positives', len(zero), '-> decide-only grade>0', len(rescued), collections.Counter(D[k]['model'] for k in rescued))

print('\n== paired flips (model grade) decide-only vs each joint run, by label')
for n in ['clinical-v1', 'clinical-quote-v2']:
    c = collections.Counter()
    for k in D:
        a, b = runs[n][k]['model'], D[k]['model']
        c[('pos' if labels[k]['abstract_label'] == 1 else 'neg', 'same' if a == b else ('decide_higher' if b > a else 'decide_lower'))] += 1
    print(n, dict(c))
print('\nflips between the two joint runs (v1 vs v2), for scale:')
c = collections.Counter()
for k in D:
    a, b = runs['clinical-v1'][k]['model'], runs['clinical-quote-v2'][k]['model']
    c[('pos' if labels[k]['abstract_label'] == 1 else 'neg', 'same' if a == b else 'diff')] += 1
print(dict(c))
print('\nCaveat: one run per condition; differences include run-to-run variance. E4 (repeats) is required before attributing flips to the quote requirement.')
