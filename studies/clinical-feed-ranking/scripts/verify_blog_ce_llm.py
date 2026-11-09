"""Check the blog's saved score evidence without API calls or experiment writes."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'runs/expanded-clinical-pointwise-v1'
SOURCES = [MAIN / 'analysis.json', MAIN / 'metrics.json',
           MAIN / 'cascade-metrics.json',
           ROOT / 'runs/clinical-expanded-v1/ce-results-complete.json']
rows, standalone, cascades, ce_records = [json.loads(p.read_text()) for p in SOURCES]
ce = {r['topic']: r['scores'] for r in ce_records}
assert len(rows) == len({(r['topic'], r['pmid']) for r in rows}) == 682
assert sum(r['abstract_label'] for r in rows) == 82
assert sum(r['content_label'] for r in rows) == 41


def check_metrics(candidates, key, label, denominator):
    """For each positive, average its contribution over all possible tied ranks."""
    keys = [key(r) for r in candidates]
    dcg = precision = recall50 = recall100 = 0.0
    for row, score in zip(candidates, keys):
        if not row[label]:
            continue
        first = 1 + sum(other > score for other in keys)
        tied = sum(other == score for other in keys)
        positions = range(first, first + tied)
        dcg += sum(1 / math.log2(pos + 1) for pos in positions if pos <= 10) / tied
        precision += sum(pos <= 10 for pos in positions) / tied / 10
        recall50 += sum(pos <= 50 for pos in positions) / tied / denominator
        recall100 += sum(pos <= 100 for pos in positions) / tied / denominator
    ideal = sum(1 / math.log2(pos + 1) for pos in range(1, min(10, denominator) + 1))
    return dict(ndcg10=dcg / ideal, precision10=precision,
                recall50=recall50, recall100=recall100)


checked = 0
for result in cascades:
    topic, variant, label = result['topic'], result['variant'], result['label']
    pool = [r for r in rows if r['topic'] == topic]
    scores = ce[topic]
    assert set(scores) == {r['pmid'] for r in pool}
    denominator = sum(r[label] for r in pool)
    candidates = pool
    if variant.startswith(('CE50_', 'CE100_')):
        limit = int(variant.split('_')[0][2:])
        candidates = sorted(pool, key=lambda r: (
            -scores[r['pmid']], hashlib.sha256(('cascade-v1:' + r['pmid']).encode()).hexdigest()
        ))[:limit]
    if variant == 'CE':
        key = lambda r: (scores[r['pmid']],)
    elif variant.endswith('_CE'):
        key = lambda r: (r['grade'], scores[r['pmid']])
    else:
        key = lambda r: (r['grade'],)
    values = check_metrics(candidates, key, label, denominator)
    values['candidate_recall'] = sum(r[label] for r in candidates) / denominator
    for name, value in values.items():
        assert abs(result[name] - value) < 1e-9, (topic, variant, label, name)
    if variant in ('CE', 'LLM'):
        arm = 'cross-encoder' if variant == 'CE' else 'clinical-original-pointwise'
        old = next(r for r in standalone['ranking']
                   if r['topic'] == topic and r['label'] == label and r['arm'] == arm)
        for name in ('ndcg10', 'precision10', 'recall50', 'recall100'):
            assert abs(old[name] - values[name]) < 1e-9
    checked += 1

positives = [r for r in rows if r['abstract_label']]
assert sum(bool(r['entryPositive']) for r in positives) == 77
assert sum(bool(r['entryAfterQuote']) for r in positives) == 72
assert sum(bool(r['entryAfterQuote']) for r in rows if not r['abstract_label']) == 179
assert sorted(sum(r['grade'] == 4 for r in rows if r['topic'] == t) for t in ce) == [10, 37, 43]

reports = ROOT / 'reports'
documents = [reports / 'blog-ce-vs-llm-clinical-feed.md',
             reports / 'blog-ce-vs-llm-clinical-feed-methods.md']
output = reports / 'blog-ce-vs-llm-verification.json'
link_count = 0
for document in documents:
    for target in re.findall(r'\]\(([^)]+)\)', document.read_text()):
        if target.startswith(('https://', 'http://', '#')):
            continue
        resolved = (document.parent / target).resolve()
        assert resolved.exists() or resolved == output, (document.name, target)
        link_count += 1

record = {
    'status': 'passed',
    'method': 'Independent per-positive expected-rank contribution calculation',
    'cascade_rows_verified': checked,
    'standalone_rows_verified': len(standalone['ranking']),
    'records': len(rows),
    'abstract_positives': len(positives),
    'local_links_verified': link_count,
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in SOURCES + documents},
    'limitations': 'Verifies saved-score arithmetic and local links, not clinical labels or model validity.'
}
output.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'source_sha256'}, indent=2))
