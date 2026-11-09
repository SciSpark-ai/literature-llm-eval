"""E4: noise floor and coupling. Offline; reads run directories only."""
import itertools
import json
import statistics
from collections import Counter
from pathlib import Path
import e45_lib as L

STUDY = L.STUDY
# e4-joint-r3 stopped at request 4/7 (transport ReadError); it is excluded and replaced by the
# owner-authorized fresh repeat e4-joint-r5 (new tag, new request bodies, not a retry).
ARMS = {'joint': ['clinical-v1', 'e4-joint-r2', 'e4-joint-r4', 'e4-joint-r5'],
        'decide': ['clinical-decide-only-v1', 'e4-decide-r2', 'e4-decide-r3', 'e4-decide-r4']}
THRESHOLDS = [1, 2]


def grades(run):
    return {k: v['model'] for k, v in run.items()}


def pair_stats(pairs):
    raw = [L.flip_rate(a, b)[0] for a, b in pairs]
    thr = {t: [L.flip_rate(a, b, threshold=t)[0] for a, b in pairs] for t in THRESHOLDS}
    return {'n_pairs': len(pairs), 'raw': raw, 'raw_mean': statistics.mean(raw) if raw else None,
            'thresholded': {str(t): {'values': v, 'mean': statistics.mean(v) if v else None} for t, v in thr.items()}}


def topic_flip(a, b, topic):
    sub_a = {k: v for k, v in a.items() if k[0] == topic}
    sub_b = {k: v for k, v in b.items() if k[0] == topic}
    return L.flip_rate(sub_a, sub_b)[0]


def analyze(runs_by_arm, labels):
    g = {arm: [grades(r) for r in runs] for arm, runs in runs_by_arm.items()}
    topics = sorted({k[0] for k in labels})
    within = {arm: pair_stats(list(itertools.combinations(gs, 2))) for arm, gs in g.items()}
    between = pair_stats([(a, b) for a in g['joint'] for b in g['decide']])
    per_item = {}
    for arm, gs in g.items():
        by_modal = {}
        for k in gs[0]:
            vals = [x[k] for x in gs]
            modal = Counter(vals).most_common(1)[0][0]
            by_modal.setdefault(modal, []).append(sum(v != modal for v in vals) / len(vals))
        per_item[arm] = {str(m): {'n_items': len(v), 'mean_disagreement': statistics.mean(v)} for m, v in sorted(by_modal.items())}
    recall = {}
    for arm, gs in g.items():
        recall[arm] = {}
        for t in topics:
            pos = [k for k in gs[0] if k[0] == t and labels[k]['abstract_label'] == 1]
            neg = [k for k in gs[0] if k[0] == t and labels[k]['abstract_label'] == 0]
            recall[arm][t] = {}
            for thr in THRESHOLDS:
                vals = [sum(x[k] >= thr for k in pos) for x in gs]
                negs = [sum(x[k] >= thr for k in neg) for x in gs]
                recall[arm][t][thr] = {'positives': len(pos), 'values': vals, 'mean': statistics.mean(vals), 'negatives_admitted': negs}
    dist = {arm: [dict(sorted(Counter(x.values()).items())) for x in gs] for arm, gs in g.items()}
    diff_by_topic = {}
    for t in topics:
        w = [topic_flip(a, b, t) for arm in g for a, b in itertools.combinations(g[arm], 2)]
        bt = [topic_flip(a, b, t) for a in g['joint'] for b in g['decide']]
        diff_by_topic[t] = statistics.mean(bt) - statistics.mean(w)
    boot = L.paired_topic_bootstrap(diff_by_topic)
    within_all = [v for arm in within for v in within[arm]['raw']]
    within_thr1 = [v for arm in within for v in within[arm]['thresholded']['1']['values']]
    h_a1 = (statistics.mean(within_all) < 0.10) and (statistics.mean(within_thr1) < 0.05)
    h_b1 = (between['raw_mean'] > 2 * statistics.mean(within_all)) and (boot['lo'] > 0)
    return {'arms': {arm: ARMS.get(arm) for arm in g}, 'within': within, 'between': between, 'per_item_flip_prob': per_item,
            'recall': recall, 'grade_distribution': dist, 'diff_by_topic': diff_by_topic, 'bootstrap': boot,
            'hypotheses': {'H-A1': {'supported': h_a1, 'within_raw_mean': statistics.mean(within_all), 'within_thr1_mean': statistics.mean(within_thr1)},
                           'H-B1': {'supported': h_b1, 'between_raw_mean': between['raw_mean'], 'ratio': between['raw_mean'] / statistics.mean(within_all) if statistics.mean(within_all) else None}}}


def gated_recall(runs, texts_per_run, labels):
    """Abstract-positives a joint run keeps once its own quote must verify: grade above 0 and the quote
    passes the production exact tier ('exact') or any of the three tiers ('any_tier'). Per topic, per run."""
    out = {}
    for t in sorted({k[0] for k in labels}):
        pos = [k for k in runs[0] if k[0] == t and labels[k]['abstract_label'] == 1]
        exact, any_tier = [], []
        for run, texts in zip(runs, texts_per_run):
            tiers = [L.match_tier(run[k]['quote'], texts[k]) if run[k]['model'] > 0 and run[k]['quote'] else 'none' for k in pos]
            exact.append(sum(x == 'exact' for x in tiers))
            any_tier.append(sum(x != 'none' for x in tiers))
        out[t] = {'positives': len(pos), 'exact': exact, 'any_tier': any_tier, 'any_tier_mean': statistics.mean(any_tier)}
    return out


def render(out):
    lines = ['# E4 analysis (development topics; descriptive)', '',
             '| Quantity | Value |', '|---|---:|']
    for arm in out['within']:
        lines.append('| within-%s raw flip rate (mean of %d pairs) | %.3f |' % (arm, out['within'][arm]['n_pairs'], out['within'][arm]['raw_mean']))
        lines.append('| within-%s flip rate at grade>=1 | %.3f |' % (arm, out['within'][arm]['thresholded']['1']['mean']))
        lines.append('| within-%s flip rate at grade>=2 | %.3f |' % (arm, out['within'][arm]['thresholded']['2']['mean']))
    lines.append('| between-arm raw flip rate (mean of %d pairs) | %.3f |' % (out['between']['n_pairs'], out['between']['raw_mean']))
    for t in ('1', '2'):
        lines.append('| between-arm flip rate at grade>=%s (mean of %d pairs) | %.3f |' % (t, out['between']['n_pairs'], out['between']['thresholded'][t]['mean']))
    b = out['bootstrap']
    lines.append('| topic-level between minus within, mean [95%% bootstrap] | %.3f [%.3f, %.3f] |' % (b['mean'], b['lo'], b['hi']))
    lines += ['', '| Arm | Topic | Threshold | Positives retained per repeat | Mean |', '|---|---|---:|---|---:|']
    for arm, per in out['recall'].items():
        for t, d in per.items():
            for thr, r in d.items():
                lines.append('| %s | %s | %s | %s | %.1f |' % (arm, t, thr, r['values'], r['mean']))
    gated = out.get('joint_gated_recall') or {}
    if 'skipped' in gated:
        lines += ['', 'Joint gated-recall table skipped: ' + gated['skipped']]
    elif gated:
        if 'approximate_text' in gated:
            lines += ['', 'Note: ' + gated['approximate_text']]
        lines += ['', '| Topic | Positives | Joint, quote exact, per repeat | Joint, quote any tier, per repeat | Joint any-tier mean | Decide-only grade>=1 mean | Gain (points of recall) |', '|---|---:|---|---|---:|---:|---:|']
        for t, r in ((k, v) for k, v in gated.items() if isinstance(v, dict)):
            d = out['recall']['decide'][t][1]['mean'] if 1 in out['recall']['decide'][t] else out['recall']['decide'][t]['1']['mean']
            lines.append('| %s | %d | %s | %s | %.2f | %.2f | %.1f |' % (t, r['positives'], r['exact'], r['any_tier'], r['any_tier_mean'], d, 100 * (d - r['any_tier_mean']) / r['positives']))
    lines += ['', 'Hypotheses: ' + json.dumps(out['hypotheses'])]
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    labels = L.load_labels()
    runs = {arm: [L.load_stage_a(STUDY / 'runs' / n) for n in names if (STUDY / 'runs' / n / 'stage-a-results.json').exists()] for arm, names in ARMS.items()}
    if any(len(v) < 2 for v in runs.values()):
        raise SystemExit('Need at least two completed runs per arm; found ' + json.dumps({k: len(v) for k, v in runs.items()}))
    out = analyze(runs, labels)
    joint_names = [n for n in ARMS['joint'] if (STUDY / 'runs' / n / 'stage-a-results.json').exists()]
    try:
        texts = [L.candidate_text(STUDY / 'runs' / n) for n in joint_names]
        out['joint_gated_recall'] = gated_recall(runs['joint'], texts, labels)
        if L.APPROXIMATE_TEXT:
            out['joint_gated_recall']['approximate_text'] = ('quotes were matched against refetched PubMed abstracts, not the cleaned text the model saw; '
                                                             'the committed analysis.json in the repository holds the exact values')
    except L.AbstractsMissing as e:
        out['joint_gated_recall'] = {'skipped': str(e), 'note': 'the committed analysis.json in the repository holds the exact values computed before redaction'}
        print('NOTE: joint_gated_recall skipped;', e)
    out['runs_used'] = {arm: [n for n in names if (STUDY / 'runs' / n / 'stage-a-results.json').exists()] for arm, names in ARMS.items()}
    (STUDY / 'results/e4').mkdir(exist_ok=True)
    (STUDY / 'results/e4/analysis.json').write_text(json.dumps(out, indent=1))
    (STUDY / 'results/e4/analysis.md').write_text(render(out))
    print(render(out))
