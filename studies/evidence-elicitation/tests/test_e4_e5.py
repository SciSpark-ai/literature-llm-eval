import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import e45_lib as L


def test_match_tier_exact_mirrors_production_normalisation():
    text = "Cognitive–behavioural therapy (CBT) reduced depression.\nRESULTS: Scores fell."
    assert L.match_tier("cognitive-behavioural therapy (CBT) reduced depression.", text) == 'exact'
    assert L.match_tier('"Scores fell"', text) == 'exact'
    assert L.match_tier("Scores", text) == 'none'  # shorter than 8 characters


def test_match_tier_normalized_and_elided_are_distinct_from_exact():
    text = "Patients with COPD and depression received psychotherapy. Symptoms improved at 8 weeks."
    assert L.match_tier("Patients with COPD & depression received psychotherapy", text) == 'none'
    assert L.match_tier("Patients with COPD, and depression received psychotherapy", text) == 'normalized'
    assert L.match_tier("Patients with COPD ... Symptoms improved at 8 weeks", text) == 'elided'
    assert L.match_tier("Symptoms improved at 8 weeks ... Patients with COPD", text) == 'none'  # out of order
    assert L.match_tier("Patients with COPD ... nothing like this here at all", text) == 'none'
    assert L.match_tier(None, text) == 'none'


def test_split_sentences_handles_structured_abstract():
    text = "OBJECTIVE: To test CBT. Secondary aims were safety.\nRESULTS: 12 of 20 improved (p=0.01). No harms."
    assert L.split_sentences(text) == [
        "OBJECTIVE: To test CBT.", "Secondary aims were safety.",
        "RESULTS: 12 of 20 improved (p=0.01).", "No harms."]


def test_flip_rate_raw_and_thresholded():
    a = {('t', '1'): 4, ('t', '2'): 1, ('t', '3'): 0, ('t', '4'): 3}
    b = {('t', '1'): 4, ('t', '2'): 0, ('t', '3'): 0, ('t', '4'): 1, ('t', '9'): 2}
    assert L.flip_rate(a, b) == (0.5, 4)
    assert L.flip_rate(a, b, threshold=1) == (0.25, 4)
    assert L.flip_rate(a, b, threshold=2) == (0.25, 4)


def test_paired_topic_bootstrap_is_deterministic_and_brackets_mean():
    r = L.paired_topic_bootstrap({'A': 0.10, 'B': 0.20, 'C': 0.30}, n=500, seed=1)
    assert r == L.paired_topic_bootstrap({'A': 0.10, 'B': 0.20, 'C': 0.30}, n=500, seed=1)
    assert abs(r['mean'] - 0.20) < 1e-9 and r['lo'] <= 0.20 <= r['hi']


def test_load_stage_a_reads_existing_decide_only_run():
    run = Path(__file__).resolve().parents[1] / 'runs' / 'clinical-decide-only-v1'
    g = L.load_stage_a(run)
    assert len(g) == 100 and all(v['quote'] == '' for v in g.values())
    labels = L.load_labels()
    assert sum(labels[k]['abstract_label'] for k in g) == 75
    import pytest as _pt
    redacted = L.REDACTED_MARK in (run / 'stage-a-requests.json').read_text()
    if redacted and not (Path(__file__).resolve().parents[1] / 'data/abstracts.json').exists():
        with _pt.raises(L.AbstractsMissing, match='fetch_abstracts'):
            L.candidate_text(run)
        return
    text = L.candidate_text(run)
    assert set(text) == set(g) and all(len(t) > 20 for t in text.values())


def test_verify_requests_accepts_reference_and_rejects_drift(tmp_path):
    import e4_verify_requests as V
    study = Path(__file__).resolve().parents[1]
    assert V.verify(study / 'runs' / 'clinical-decide-only-v1', 'decide') == 7
    assert V.verify(study / 'runs' / 'clinical-v1', 'joint') == 7
    drifted = tmp_path / 'drift'
    drifted.mkdir()
    reqs = json.loads((study / 'runs/clinical-v1/stage-a-requests.json').read_text())
    reqs[0]['req']['messages'][0]['content'] += ' '
    (drifted / 'stage-a-requests.json').write_text(json.dumps(reqs))
    with pytest.raises(ValueError, match='differs'):
        V.verify(drifted, 'joint')


def test_e4_paid_tag_changes_body_hash_and_dry_run_makes_no_call(tmp_path, monkeypatch):
    import e4_paid as P
    import hashlib
    reqs = [{'id': 'abc', 'topic': 'T', 'model': 'gpt-4.1-mini-2025-04-14',
             'req': {'maxTokens': 8192, 'temperature': 0, 'jsonSchema': {'type': 'object', 'minimum': 0}, 'messages': [{'role': 'system', 'content': 's'}, {'role': 'user', 'content': 'u'}]}}]
    b1 = P.build_bodies(reqs, 'joint-r2')
    b2 = P.build_bodies(reqs, 'joint-r3')
    assert b1[0]['user'] == 'joint-r2' and b2[0]['user'] == 'joint-r3'
    assert b1[0]['response_format']['json_schema']['schema'] == {'type': 'object'}
    h = lambda b: hashlib.sha256(json.dumps(b, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert h(b1[0]) != h(b2[0])
    calls = []
    monkeypatch.setattr(P, 'call_provider', lambda bodies, reqs, out: calls.append(1))
    ledger = tmp_path / 'budget.jsonl'
    ledger.write_text(json.dumps({'event': 'reserved', 'request_id': 'x', 'lane': 'ranking', 'ceiling_microusd': 19_990_000}) + '\n')
    with pytest.raises(RuntimeError, match='exceed'):
        P.main(reqs, 'joint-r2', run=True, ledger=ledger, out=tmp_path / 'resp.json')
    assert calls == []
    ledger.write_text(json.dumps({'event': 'reserved', 'request_id': 'x', 'lane': 'ranking', 'ceiling_microusd': 1_000_000}) + '\n')
    P.main(reqs, 'joint-r2', run=False, ledger=ledger, out=tmp_path / 'resp.json')
    assert calls == []
    P.main(reqs, 'joint-r2', run=True, ledger=ledger, out=tmp_path / 'resp.json')
    assert calls == [1]
    # Owner raised the ceiling to 20 USD on 2026-10-09: a ledger already past the old 10 USD cap must still be allowed.
    ledger.write_text(json.dumps({'event': 'reserved', 'request_id': 'x', 'lane': 'ranking', 'ceiling_microusd': 12_000_000}) + '\n')
    P.main(reqs, 'joint-r2', run=True, ledger=ledger, out=tmp_path / 'resp.json')
    assert calls == [1, 1]
    assert P.LANE_USD == 20


def test_e5_extract_lane_matches_e4_paid():
    import e4_paid as P
    import e5_extract as E
    assert E.LANE_USD == P.LANE_USD == 20


def test_e4_analysis_on_synthetic_runs_reports_noise_and_between_arm_gap():
    import e4_analysis as A
    labels = {('T', str(i)): {'abstract_label': 1 if i < 6 else 0, 'content_label': 0} for i in range(10)}
    base = {('T', str(i)): (4 if i < 5 else 0) for i in range(10)}
    j1 = dict(base); j2 = dict(base); j2[('T', '5')] = 1          # one flip within joint
    d1 = dict(base); d1[('T', '0')] = 1; d1[('T', '1')] = 1; d1[('T', '5')] = 1
    d2 = dict(d1)
    wrap = lambda g: {k: {'model': v, 'quote': '', 'qv': False, 'ungraded': False} for k, v in g.items()}
    out = A.analyze({'joint': [wrap(j1), wrap(j2)], 'decide': [wrap(d1), wrap(d2)]}, labels)
    assert out['within']['joint']['raw_mean'] == pytest.approx(0.1)
    assert out['within']['decide']['raw_mean'] == pytest.approx(0.0)
    assert out['between']['raw_mean'] > out['within']['joint']['raw_mean']
    assert out['recall']['joint']['T'][1]['values'] == [5, 6]
    assert out['recall']['decide']['T'][2]['values'] == [3, 3]
    assert set(out['hypotheses']) == {'H-A1', 'H-B1'}


def _items():
    return [{'topic': 'CD012347', 'pmid': '1', 'grade': 4, 'text': 'CBT for depression in COPD.\nRESULTS: Depression fell. Dyspnoea unchanged.'},
            {'topic': 'CD012347', 'pmid': '2', 'grade': 1, 'text': 'Lung transplant outcomes.\nMortality was 10%. Follow-up was 2 years.'}]


def test_e5_build_requests_quote_and_sentence_modes():
    import e5_extract as E
    watches = {'CD012347': {'condition': 'depression', 'condition2': 'chronic obstructive pulmonary disease', 'conditionJoin': 'and', 'treatment': 'psychotherapy'}}
    rq = E.build_requests(_items(), 'quote', watches)
    assert len(rq) == 1 and rq[0]['indices'] == ['1', '2'] and rq[0]['body']['max_tokens'] == 2048
    assert rq[0]['body']['model'] == 'gpt-4.1-mini-2025-04-14' and rq[0]['body']['temperature'] == 0
    user = json.loads(rq[0]['body']['messages'][1]['content'])
    assert user['papers'][0]['index'] == 0 and user['papers'][0]['assignedGrade'] == 4 and 'sentences' not in user['papers'][0]
    rs = E.build_requests(_items(), 'sentence', watches)
    user = json.loads(rs[0]['body']['messages'][1]['content'])
    assert user['papers'][0]['sentences'] == [[0, 'CBT for depression in COPD.'], [1, 'RESULTS: Depression fell.'], [2, 'Dyspnoea unchanged.']]


def test_e5_parse_response_verifies_tiers_and_rejects_bad_indices():
    import e5_extract as E
    items = _items()
    by_pmid = {(i['topic'], i['pmid']): i for i in items}
    req = {'topic': 'CD012347', 'indices': ['1', '2']}
    good = {'choices': [{'message': {'content': json.dumps({'evidence': [{'index': 0, 'quote': 'Depression fell'}, {'index': 1, 'quote': 'Mortality was 10% ... was 2 years'}]})}}]}
    out = E.parse_response('quote', req, good, by_pmid)
    assert [o['tier'] for o in out] == ['exact', 'elided'] and out[1]['pmid'] == '2'
    dup = {'choices': [{'message': {'content': json.dumps({'evidence': [{'index': 0, 'quote': 'x'}, {'index': 0, 'quote': 'y'}]})}}]}
    with pytest.raises(ValueError, match='indices'):
        E.parse_response('quote', req, dup, by_pmid)
    sent = {'choices': [{'message': {'content': json.dumps({'evidence': [{'index': 0, 'sentence': 1}, {'index': 1, 'sentence': 9}]})}}]}
    out = E.parse_response('sentence', req, sent, by_pmid)
    assert out[0]['evidence'] == 'RESULTS: Depression fell.' and out[0]['tier'] == 'exact'
    assert out[1]['evidence'] == '' and out[1]['tier'] == 'none'


def test_e5_select_items_only_failures_uses_joint_quote_outcome():
    import e5_extract as E
    study = Path(__file__).resolve().parents[1]
    all_items = E.select_items(study / 'runs/clinical-decide-only-v1', only_failures=False)
    assert len(all_items) == 72 + 10  # grade>0 positives and negatives in the decide-only run
    fails = E.select_items(study / 'runs/clinical-v1', only_failures=True)
    assert len(fails) == 39 and all(i['grade'] > 0 for i in fails)


def test_e5_policies_table_counts_verified_positives_by_tier():
    import e5_analysis as A
    labels = {('T', '1'): {'abstract_label': 1}, ('T', '2'): {'abstract_label': 1}, ('T', '3'): {'abstract_label': 0}}
    joint = {('T', '1'): {'model': 4, 'quote': 'a', 'qv': True, 'ungraded': False}, ('T', '2'): {'model': 3, 'quote': 'b', 'qv': False, 'ungraded': False}, ('T', '3'): {'model': 1, 'quote': 'c', 'qv': False, 'ungraded': False}}
    decide = {('T', '1'): {'model': 1, 'quote': '', 'qv': False, 'ungraded': False}, ('T', '2'): {'model': 4, 'quote': '', 'qv': False, 'ungraded': False}, ('T', '3'): {'model': 0, 'quote': '', 'qv': False, 'ungraded': False}}
    e5 = {'D+E': [{'topic': 'T', 'pmid': '1', 'grade': 1, 'evidence': 'x', 'tier': 'elided'}, {'topic': 'T', 'pmid': '2', 'grade': 4, 'evidence': 'y', 'tier': 'exact'}],
          'D+S': [{'topic': 'T', 'pmid': '1', 'grade': 1, 'evidence': 'x', 'tier': 'exact'}, {'topic': 'T', 'pmid': '2', 'grade': 4, 'evidence': '', 'tier': 'none'}],
          'J+R': [{'topic': 'T', 'pmid': '2', 'grade': 3, 'evidence': 'z', 'tier': 'normalized'}, {'topic': 'T', 'pmid': '3', 'grade': 1, 'evidence': '', 'tier': 'none'}]}
    out = A.policies(joint, decide, e5, labels)
    assert out['J']['T'] == {'admitted_positives': 2, 'verified_exact': 1, 'verified_any_tier': 1, 'negatives_admitted': 1, 'negatives_verified_any': 0}
    assert out['J+R']['T'] == {'admitted_positives': 2, 'verified_exact': 1, 'verified_any_tier': 2, 'negatives_admitted': 1, 'negatives_verified_any': 0}
    assert out['D+E']['T'] == {'admitted_positives': 2, 'verified_exact': 1, 'verified_any_tier': 2, 'negatives_admitted': 0, 'negatives_verified_any': 0}
    assert out['D+S']['T'] == {'admitted_positives': 2, 'verified_exact': 1, 'verified_any_tier': 1, 'negatives_admitted': 0, 'negatives_verified_any': 0}


def test_e4_arms_use_replacement_run_for_the_failed_joint_r3():
    # e4-joint-r3 stopped at request 4/7 (transport ReadError, 2026-10-09); the owner authorized a fresh
    # full repeat under a new tag, e4-joint-r5. The partial run must never enter the analysis.
    import e4_analysis as A
    assert A.ARMS['joint'] == ['clinical-v1', 'e4-joint-r2', 'e4-joint-r4', 'e4-joint-r5']
    assert A.ARMS['decide'] == ['clinical-decide-only-v1', 'e4-decide-r2', 'e4-decide-r3', 'e4-decide-r4']


def test_e5_parse_response_records_omitted_papers_as_unverified_but_still_rejects_bad_indices():
    # Observed 2026-10-09 (e5-decide-quote, CD012347): the model returned 13 of 20 entries, omitting seven
    # grade-1 papers. An omission is a result (no evidence offered), not a misalignment: record it explicitly.
    import e5_extract as E
    items = _items()
    by_pmid = {(i['topic'], i['pmid']): i for i in items}
    req = {'topic': 'CD012347', 'indices': ['1', '2']}
    partial = {'choices': [{'message': {'content': json.dumps({'evidence': [{'index': 1, 'quote': 'Mortality was 10%'}]})}}]}
    out = E.parse_response('quote', req, partial, by_pmid)
    assert [(o['pmid'], o['tier'], o['omitted']) for o in out] == [('1', 'none', True), ('2', 'exact', False)]
    assert out[0]['evidence'] == '' and out[0]['grade'] == 4
    for bad in ([{'index': 0, 'quote': 'x'}, {'index': 0, 'quote': 'y'}], [{'index': 0, 'quote': 'x'}, {'index': 2, 'quote': 'y'}],
                [{'index': -1, 'quote': 'x'}], [{'index': True, 'quote': 'x'}]):
        with pytest.raises(ValueError, match='indices'):
            E.parse_response('quote', req, {'choices': [{'message': {'content': json.dumps({'evidence': bad})}}]}, by_pmid)


def test_e5_parse_only_rebuilds_results_from_saved_responses_without_network(tmp_path, monkeypatch):
    import e5_extract as E
    monkeypatch.setattr(E, 'STUDY', tmp_path)
    (tmp_path / 'runs' / 'out').mkdir(parents=True)
    items = _items()
    monkeypatch.setattr(E, 'select_items', lambda source, only_failures: items)
    monkeypatch.setattr(E, 'load_watches', lambda: {'CD012347': {'condition': 'depression'}})
    requests = E.build_requests(items, 'quote', E.load_watches())
    out = tmp_path / 'runs' / 'out'
    (out / 'requests.json').write_text(json.dumps({'mode': 'quote', 'requests': requests}))
    (out / 'responses.json').write_text(json.dumps([{'choices': [{'message': {'content': json.dumps({'evidence': [{'index': 0, 'quote': 'Depression fell'}]})}}]}]))
    E.main(['quote', 'src', 'out', '--parse-only'])
    results = json.loads((out / 'results.json').read_text())
    assert [(r['pmid'], r['tier'], r['omitted']) for r in results] == [('1', 'exact', False), ('2', 'none', True)]
    assert not (tmp_path / 'budget.jsonl').exists()
    drift = json.loads((out / 'requests.json').read_text())
    drift['requests'][0]['body']['messages'][0]['content'] += ' '
    (out / 'requests.json').write_text(json.dumps(drift))
    with pytest.raises(ValueError, match='differ'):
        E.main(['quote', 'src', 'out', '--parse-only'])


def test_e5_policies_apply_tiered_matcher_to_joint_quotes_and_retry_keeps_the_better_tier():
    # The joint run's own quotes must be scored with the same three tiers as the extraction arms; otherwise
    # J is understated under "any tier". J+R keeps the better of the original and the retried evidence.
    import e5_analysis as A
    labels = {('T', str(i)): {'abstract_label': 1} for i in (1, 2, 3, 4)}
    g = lambda q, qv: {'model': 4, 'quote': q, 'qv': qv, 'ungraded': False}
    joint = {('T', '1'): g('a', True), ('T', '2'): g('b', False), ('T', '3'): g('c', False), ('T', '4'): g('d', False)}
    joint_tiers = {('T', '1'): 'exact', ('T', '2'): 'elided', ('T', '3'): 'elided', ('T', '4'): 'none'}
    e5 = {'J+R': [{'topic': 'T', 'pmid': '2', 'grade': 4, 'evidence': '', 'tier': 'none'},
                  {'topic': 'T', 'pmid': '3', 'grade': 4, 'evidence': 'x', 'tier': 'exact'},
                  {'topic': 'T', 'pmid': '4', 'grade': 4, 'evidence': 'y', 'tier': 'normalized'}]}
    out = A.policies(joint, {}, e5, labels, joint_tiers=joint_tiers)
    assert out['J']['T']['verified_exact'] == 1 and out['J']['T']['verified_any_tier'] == 3
    assert out['J+R']['T']['verified_exact'] == 2 and out['J+R']['T']['verified_any_tier'] == 4
    assert out['tier_counts']['J'] == {'exact': 1, 'normalized': 0, 'elided': 2, 'none': 1}
    assert out['tier_counts']['J+R'] == {'exact': 2, 'normalized': 1, 'elided': 1, 'none': 0}
    with pytest.raises(ValueError, match='production'):
        A.policies(joint, {}, e5, labels, joint_tiers={**joint_tiers, ('T', '2'): 'exact'})


def test_e4_render_reports_thresholded_flip_rates_within_and_between_arms():
    import e4_analysis as A
    labels = {('T', str(i)): {'abstract_label': 1, 'content_label': 0} for i in range(4)}
    wrap = lambda g: {('T', str(i)): {'model': v, 'quote': '', 'qv': False, 'ungraded': False} for i, v in enumerate(g)}
    out = A.analyze({'joint': [wrap([4, 4, 0, 0]), wrap([4, 1, 0, 0])], 'decide': [wrap([1, 1, 1, 0]), wrap([1, 1, 1, 0])]}, labels)
    text = A.render(out)
    assert '| within-joint flip rate at grade>=2 | 0.250 |' in text
    assert '| between-arm flip rate at grade>=1 (mean of 4 pairs) | 0.250 |' in text
    assert '| between-arm flip rate at grade>=2 (mean of 4 pairs) | 0.375 |' in text


def test_e4_gated_recall_counts_joint_positives_only_when_their_quote_passes_a_tier():
    # Go/no-go criterion 2 compares decide-only recall with joint recall AFTER an elision-tolerant matcher:
    # a joint positive counts only if its grade is above 0 and its own quote verifies at some tier.
    import e4_analysis as A
    labels = {('T', '1'): {'abstract_label': 1}, ('T', '2'): {'abstract_label': 1}, ('T', '3'): {'abstract_label': 1}, ('T', '4'): {'abstract_label': 0}}
    text = "Patients with COPD and depression received psychotherapy. Symptoms improved at 8 weeks."
    texts = {k: text for k in labels}
    g = lambda m, q: {'model': m, 'quote': q, 'qv': False, 'ungraded': False}
    run1 = {('T', '1'): g(4, 'Symptoms improved at 8 weeks'), ('T', '2'): g(1, 'Patients with COPD ... Symptoms improved at 8 weeks'),
            ('T', '3'): g(4, 'not in the abstract at all'), ('T', '4'): g(4, 'Symptoms improved at 8 weeks')}
    run2 = {('T', '1'): g(0, 'Symptoms improved at 8 weeks'), ('T', '2'): g(4, ''), ('T', '3'): g(4, 'received psychotherapy'), ('T', '4'): g(0, '')}
    out = A.gated_recall([run1, run2], [texts, texts], labels)
    assert out == {'T': {'positives': 3, 'exact': [1, 1], 'any_tier': [2, 1], 'any_tier_mean': 1.5}}
