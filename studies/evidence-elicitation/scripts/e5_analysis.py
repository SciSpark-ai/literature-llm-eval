"""E5: joint versus decoupled evidence under tiered verification, with cost per verified admitted positive."""
import json
from pathlib import Path
import e45_lib as L

STUDY = L.STUDY
E5_RUNS = {'D+E': 'e5-decide-quote', 'D+S': 'e5-decide-sentence', 'J+R': 'e5-joint-retry'}
ANY = ('exact', 'normalized', 'elided')


def _row():
    return {'admitted_positives': 0, 'verified_exact': 0, 'verified_any_tier': 0, 'negatives_admitted': 0, 'negatives_verified_any': 0}


RANK = {'exact': 3, 'normalized': 2, 'elided': 1, 'none': 0}


def joint_quote_tiers(joint, texts):
    """Three-tier verdict for the joint run's own quotes, so J is scored like the extraction arms."""
    return {k: (L.match_tier(v['quote'], texts[k]) if v['quote'] else 'none') for k, v in joint.items() if v['model'] > 0}


def policies(joint, decide, e5, labels, joint_tiers=None):
    out = {}
    topics = sorted({k[0] for k in labels})
    if joint_tiers is None:
        tiers_j = {k: ('exact' if v['qv'] else 'none') for k, v in joint.items() if v['model'] > 0}
    else:
        tiers_j = {k: joint_tiers[k] for k, v in joint.items() if v['model'] > 0}
        # The exact tier must reproduce the production verdict; a disagreement means the mirror has drifted.
        bad = [k for k, v in joint.items() if v['model'] > 0 and (tiers_j[k] == 'exact') != v['qv']]
        if bad and not L.APPROXIMATE_TEXT:
            raise ValueError('Exact tier disagrees with production quoteVerified for %d records' % len(bad))
        if bad:
            print('NOTE: exact tier disagrees with the production verdict for %d records because quotes were matched against '
                  'refetched abstracts rather than the cleaned text the model saw; J rows are approximate.' % len(bad))
    tiers_jr = dict(tiers_j)
    for r in e5.get('J+R', []):
        k = (r['topic'], r['pmid'])
        # A retry never discards valid original evidence: keep the better tier.
        if RANK[r['tier']] > RANK[tiers_jr.get(k, 'none')]:
            tiers_jr[k] = r['tier']
    tiers_de = {(r['topic'], r['pmid']): r['tier'] for r in e5.get('D+E', [])}
    tiers_ds = {(r['topic'], r['pmid']): r['tier'] for r in e5.get('D+S', [])}
    admitted = {'J': {k for k, v in joint.items() if v['model'] > 0}, 'J+R': {k for k, v in joint.items() if v['model'] > 0},
                'D+E': {k for k, v in decide.items() if v['model'] > 0}, 'D+S': {k for k, v in decide.items() if v['model'] > 0}}
    tiers = {'J': tiers_j, 'J+R': tiers_jr, 'D+E': tiers_de, 'D+S': tiers_ds}
    for name in ('J', 'J+R', 'D+E', 'D+S'):
        out[name] = {t: _row() for t in topics}
        for k in admitted[name]:
            row = out[name][k[0]]
            tier = tiers[name].get(k, 'none')
            if labels[k]['abstract_label'] == 1:
                row['admitted_positives'] += 1
                row['verified_exact'] += tier == 'exact'
                row['verified_any_tier'] += tier in ANY
            else:
                row['negatives_admitted'] += 1
                row['negatives_verified_any'] += tier in ANY
    out['tier_counts'] = {name: {t: sum(v == t for v in tiers[name].values()) for t in ANY + ('none',)} for name in tiers}
    return out


def tokens(path):
    r = json.loads(Path(path).read_text())
    vals = r.values() if isinstance(r, dict) else r
    return {'in': sum(v['usage']['prompt_tokens'] for v in vals), 'out': sum(v['usage']['completion_tokens'] for v in vals)}


def cost(out):
    base_j = tokens(STUDY / 'runs/clinical-v1/stage-a-responses.json')
    base_d = tokens(STUDY / 'runs/clinical-decide-only-v1/stage-a-responses.json')
    extra = {name: tokens(STUDY / 'runs' / run / 'responses.json') for name, run in E5_RUNS.items() if (STUDY / 'runs' / run / 'responses.json').exists()}
    totals = {'J': base_j, 'J+R': {k: base_j[k] + extra.get('J+R', {'in': 0, 'out': 0})[k] for k in ('in', 'out')},
              'D+E': {k: base_d[k] + extra.get('D+E', {'in': 0, 'out': 0})[k] for k in ('in', 'out')},
              'D+S': {k: base_d[k] + extra.get('D+S', {'in': 0, 'out': 0})[k] for k in ('in', 'out')}}
    result = {}
    for name, tk in totals.items():
        usd = (tk['in'] * .4 + tk['out'] * 1.6) / 1e6
        verified = sum(out[name][t]['verified_any_tier'] for t in out[name])
        result[name] = {'tokens': tk, 'usd': usd, 'verified_positives': verified, 'usd_per_verified_positive': usd / verified if verified else None, 'tokens_ratio_vs_J': (tk['in'] + tk['out']) / (base_j['in'] + base_j['out'])}
    return result


def render(out, costs):
    lines = ['# E5 analysis (development topics; descriptive)', '', '| Policy | Topic | Admitted positives | Verified exact | Verified any tier | Negatives admitted | Negatives verified |', '|---|---|---:|---:|---:|---:|---:|']
    for name in ('J', 'J+R', 'D+E', 'D+S'):
        for t, r in out[name].items():
            lines.append('| %s | %s | %d | %d | %d | %d | %d |' % (name, t, r['admitted_positives'], r['verified_exact'], r['verified_any_tier'], r['negatives_admitted'], r['negatives_verified_any']))
    lines += ['', '| Policy | Tokens in | Tokens out | USD | Verified positives | USD per verified positive | Token ratio vs J |', '|---|---:|---:|---:|---:|---:|---:|']
    for name, c in costs.items():
        lines.append('| %s | %d | %d | %.4f | %d | %s | %.2f |' % (name, c['tokens']['in'], c['tokens']['out'], c['usd'], c['verified_positives'], ('%.5f' % c['usd_per_verified_positive']) if c['usd_per_verified_positive'] else 'n/a', c['tokens_ratio_vs_J']))
    lines += ['', 'Tier counts: ' + json.dumps(out['tier_counts'])]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    labels = L.load_labels()
    joint = L.load_stage_a(STUDY / 'runs/clinical-v1')
    decide = L.load_stage_a(STUDY / 'runs/clinical-decide-only-v1')
    e5 = {name: json.loads((STUDY / 'runs' / run / 'results.json').read_text()) for name, run in E5_RUNS.items() if (STUDY / 'runs' / run / 'results.json').exists()}
    note = None
    try:
        out = policies(joint, decide, e5, labels, joint_tiers=joint_quote_tiers(joint, L.candidate_text(STUDY / 'runs/clinical-v1')))
        if L.APPROXIMATE_TEXT:
            note = 'J tiers computed against refetched PubMed abstracts (approximate); the committed analysis.json holds the exact values'
    except L.AbstractsMissing as e:
        print('NOTE: abstract text not available;', e)
        print('NOTE: scoring J with the production exact verdict only (no normalized/elided tiers); the committed analysis.json holds the exact three-tier values')
        out = policies(joint, decide, e5, labels, joint_tiers=None)
        note = 'J scored by production quoteVerified only because abstract text is not available in this export'
    costs = cost(out)
    (STUDY / 'runs/e5').mkdir(exist_ok=True)
    (STUDY / 'runs/e5/analysis.json').write_text(json.dumps({'policies': out, 'costs': costs, 'arms_present': sorted(e5), 'note': note}, indent=1))
    (STUDY / 'runs/e5/analysis.md').write_text(render(out, costs))
    print(render(out, costs))
