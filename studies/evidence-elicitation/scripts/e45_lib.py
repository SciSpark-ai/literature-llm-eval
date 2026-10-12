"""Offline helpers for the E4/E5 experiments. No provider access here."""
import json
import random
import re
import unicodedata
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
MIN_QUOTE = 8


def squash(text):
    """Mirror of production quote.ts `squash`: case, curly quotes, dashes, whitespace."""
    s = text.lower()
    s = re.sub(r'[‘’ʼ]', "'", s)
    s = re.sub(r'[“”]', '"', s)
    s = re.sub(r'[‐-―−]', '-', s)
    s = re.sub(r'[\s ]+', ' ', s)
    return s.strip()


def quote_core(quote):
    """Mirror of production `quoteCore`: strip framing quotes, trailing ellipsis and punctuation."""
    s = squash(quote)
    s = re.sub(r'^["\']+|["\']+$', '', s)
    s = re.sub(r'(?:\.\.\.|…)$', '', s)
    s = re.sub(r'[.,;:!?]+$', '', s)
    return s.strip()


def normalized(text):
    s = unicodedata.normalize('NFKC', text).lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def match_tier(quote, text):
    """'exact' = production rule; 'normalized' = punctuation-insensitive; 'elided' = all
    ellipsis-separated fragments present in order; 'none' otherwise. Tiers are ordered."""
    if not isinstance(quote, str) or not isinstance(text, str):
        return 'none'
    core = quote_core(quote)
    if len(core) >= MIN_QUOTE and core in squash(text):
        return 'exact'
    nq, nt = normalized(quote), normalized(text)
    if len(nq) >= MIN_QUOTE and nq in nt:
        return 'normalized'
    frags = [normalized(f) for f in re.split(r'\.\.\.|…', quote)]
    frags = [f for f in frags if len(f) >= MIN_QUOTE]
    if len(frags) >= 2:
        positions = [nt.find(f) for f in frags]
        if all(p >= 0 for p in positions) and positions == sorted(positions):
            return 'elided'
    return 'none'


def split_sentences(text):
    out = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        out.extend(p.strip() for p in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9(])', line) if p.strip())
    return out


def flip_rate(a, b, threshold=None):
    keys = sorted(set(a) & set(b))
    if threshold is None:
        flips = sum(a[k] != b[k] for k in keys)
    else:
        flips = sum((a[k] >= threshold) != (b[k] >= threshold) for k in keys)
    return (flips / len(keys) if keys else 0.0), len(keys)


def paired_topic_bootstrap(values_by_topic, n=2000, seed=0):
    topics = sorted(values_by_topic)
    vals = [values_by_topic[t] for t in topics]
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        sample = [vals[rng.randrange(len(vals))] for _ in vals]
        means.append(sum(sample) / len(sample))
    means.sort()
    return {'mean': sum(vals) / len(vals), 'lo': means[int(0.025 * n)], 'hi': means[min(n - 1, int(0.975 * n))], 'n_topics': len(vals)}


def load_labels():
    config = json.loads((STUDY / 'runs/clinical-v1/config.json').read_text())
    return {(t['id'], r['pmid']): r for t in config['topics'] for r in t['records']}


def load_stage_a(run_dir):
    out = {}
    for t in json.loads((Path(run_dir) / 'stage-a-results.json').read_text()):
        for rec in t['records']:
            g = rec['grade']
            out[(t['topic'], rec['pmid'])] = {'model': g.get('modelGrade') or 0, 'quote': g.get('quote') or '', 'qv': bool(g.get('quoteVerified')), 'ungraded': bool(g.get('ungraded'))}
    return out


REDACTED_MARK = '[ABSTRACT REDACTED'
VISIBLE_ABSTRACT_CHARS = 1800
# Set to True by candidate_text when the public export's placeholders were filled from refetched PubMed
# abstracts. Callers that compare quotes against text should report their results as approximate then.
APPROXIMATE_TEXT = False


class AbstractsMissing(RuntimeError):
    pass


def _refetched_abstracts():
    p = STUDY / 'data/abstracts.json'
    if not p.exists():
        raise AbstractsMissing('Abstract text was removed from this export. Run `python3 scripts/fetch_abstracts.py` '
                               'to refetch it from PubMed into data/abstracts.json, then rerun.')
    return json.loads(p.read_text())


def candidate_text(run_dir):
    """Title and abstract as sent to the model, keyed like load_stage_a (order within topic).

    In the public export the abstract part is a placeholder. If data/abstracts.json exists (written by
    fetch_abstracts.py) the placeholder is replaced by the raw PubMed abstract cut to the same 1800-character
    window the production cleaner used; this is an approximation of the cleaned text the model saw, and
    APPROXIMATE_TEXT is set so callers can label their outputs. Without that file the function raises
    AbstractsMissing with instructions."""
    global APPROXIMATE_TEXT
    run_dir = Path(run_dir)
    requests = json.loads((run_dir / 'stage-a-requests.json').read_text())
    per_topic = {}
    for r in requests:
        user = json.loads(r['req']['messages'][1]['content'])
        for c in user['candidates']:
            per_topic.setdefault(r['topic'], []).append(((c.get('title') or ''), (c.get('abstract') or '')))
    results = json.loads((run_dir / 'stage-a-results.json').read_text())
    out = {}
    refetched = None
    for t in results:
        texts = per_topic[t['topic']]
        if len(texts) != len(t['records']):
            raise ValueError('Request/result length mismatch for ' + t['topic'])
        for rec, (title, abstract) in zip(t['records'], texts):
            if abstract.startswith(REDACTED_MARK):
                if refetched is None:
                    refetched = _refetched_abstracts()
                raw = refetched.get(rec['pmid'], {}).get('abstract', '')
                abstract = raw[:VISIBLE_ABSTRACT_CHARS]
                APPROXIMATE_TEXT = True
            out[(t['topic'], rec['pmid'])] = title + '\n' + abstract
    return out
