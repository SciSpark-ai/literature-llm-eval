"""Why the joint prompt's quotes fail: taxonomy of positive-paper quote failures in the baseline and
short-span runs, under the production exact rule, the three-tier matcher, and a finer descriptive split.

Needs the visible text of each candidate (title + cleaned abstract). In the public export that text is
redacted; run `scripts/fetch_abstracts.py` first and the counts will be recomputed on refetched text and
labelled approximate. The committed results/matcher-taxonomy.json holds the exact values.
"""
import collections
import json
import re
import unicodedata
from pathlib import Path
import e45_lib as L

STUDY = L.STUDY
RUNS = {'joint_baseline': 'clinical-v1', 'short_span_variant': 'clinical-quote-v2'}


def norm(s):
    s = unicodedata.normalize('NFKC', s).lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def describe(quote, text):
    """Finer descriptive category for a quote that fails the production exact rule."""
    if not quote or not quote.strip():
        return 'empty'
    has_ellipsis = ('...' in quote) or ('…' in quote)
    nt = norm(text)
    if not has_ellipsis:
        if norm(quote) in nt:
            return 'normalized_match'
        words = norm(quote).split()
        grams = [' '.join(words[i:i + 5]) for i in range(max(1, len(words) - 4))]
        hit = sum(g in nt for g in grams) / len(grams)
        if hit >= 0.8:
            return 'near_verbatim_minor_edit'
        if hit >= 0.3:
            return 'partial_paraphrase'
        return 'paraphrase_or_unsupported'
    frags = [f.strip() for f in re.split(r'\.\.\.|…', quote) if len(f.strip()) >= 8]
    if frags and all(norm(f) in nt for f in frags):
        pos = [nt.find(norm(f)) for f in frags]
        return 'elided_fragments_in_order' if pos == sorted(pos) else 'elided_fragments_unordered'
    return 'elided_with_paraphrase'


def taxonomy():
    labels = L.load_labels()
    out = {}
    for name, run in RUNS.items():
        g = L.load_stage_a(STUDY / 'runs' / run)
        texts = L.candidate_text(STUDY / 'runs' / run)
        admitted_pos = [k for k, v in g.items() if v['model'] > 0 and labels[k]['abstract_label'] == 1]
        failed = [k for k in admitted_pos if not g[k]['qv']]
        tiers = collections.Counter(L.match_tier(g[k]['quote'], texts[k]) for k in failed)
        fine = collections.Counter(describe(g[k]['quote'], texts[k]) for k in failed)
        recoverable_tiers = tiers.get('normalized', 0) + tiers.get('elided', 0)
        recoverable_fine = fine.get('normalized_match', 0) + fine.get('elided_fragments_in_order', 0) + fine.get('near_verbatim_minor_edit', 0)
        out[name] = {
            'run': run, 'admitted_positives': len(admitted_pos), 'production_exact_failures': len(failed),
            'three_tier_of_failures': dict(tiers),
            'recoverable_by_three_tier_matcher': recoverable_tiers,
            'descriptive_split_of_failures': dict(fine),
            'recoverable_by_lenient_reading': recoverable_fine,
            'recoverable_including_unordered_fragments': recoverable_fine + fine.get('elided_fragments_unordered', 0),
        }
    out['definitions'] = {
        'production_exact': 'quote found in title+abstract after case, whitespace, dash and curly-quote normalisation (production rule)',
        'normalized': 'found after additionally dropping punctuation',
        'elided': 'all ellipsis-separated fragments of at least 8 characters found, in order',
        'descriptive_split': 'finer categories for reading, not a verification rule',
    }
    out['approximate_text'] = bool(L.APPROXIMATE_TEXT)
    return out


if __name__ == '__main__':
    result = taxonomy()
    (STUDY / 'results').mkdir(exist_ok=True)
    (STUDY / 'results/matcher-taxonomy.json').write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
