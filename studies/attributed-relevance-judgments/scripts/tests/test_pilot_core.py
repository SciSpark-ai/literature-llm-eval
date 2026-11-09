"""Guard against overspend, omitted failed topics and corrupted ranking outputs."""
import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_core import Budget, metrics, evaluate_runs, parse_grades, select_topics


def test_budget_persists_reservations_and_blocks_excess(tmp_path):
    path = tmp_path / 'budget.jsonl'
    b = Budget(path, limit_usd=1, lane_limit_usd=1)
    b.reserve('first', .7)
    with pytest.raises(ValueError):
        Budget(path, limit_usd=1, lane_limit_usd=1).reserve('second', .31)
    assert len(path.read_text().splitlines()) == 1


def test_pending_or_failed_request_cannot_silently_retry(tmp_path):
    b = Budget(tmp_path / 'budget.jsonl')
    b.reserve('same', .1)
    with pytest.raises(ValueError):
        b.reserve('same', .1)


def test_lane_budget_and_invalid_amounts_are_rejected(tmp_path):
    b = Budget(tmp_path / 'budget.jsonl', limit_usd=10, lane_limit_usd=.5)
    b.reserve('first', .4)
    for value in [.2, -1, float('nan'), float('inf')]:
        with pytest.raises(ValueError):
            b.reserve(str(value), value)


def test_cost_above_reservation_is_detected(tmp_path):
    b = Budget(tmp_path / 'budget.jsonl')
    b.reserve('one', .01)
    with pytest.raises(ValueError):
        b.finish('one', .02, 'success')


def test_empty_topic_stays_in_metric_denominator():
    report = evaluate_runs({'1': ['a']}, {'1': {'a': 2}, '2': {'b': 2}}, ['1', '2'])
    assert report['mean']['ndcg_at_10'] == .5
    assert report['per_topic']['2']['ndcg_at_10'] == 0
    assert report['per_topic']['1']['precision_at_10'] == .1


def test_missing_corpus_relevance_and_unjudged_are_not_erased():
    result = metrics(['a', 'unknown', 'negative'], {'a': 2, 'missing': 2, 'negative': -1})
    assert result['recall_at_pool'] == .5
    assert result['judged_at_10'] == .1
    assert result['ndcg_at_10'] < 1
    with pytest.raises(ValueError):
        metrics(['a', 'a'], {'a': 2})


def test_metric_agrees_with_trec_eval_linear_gain():
    import pytrec_eval
    labels = {'a': 2, 'b': 1, 'c': 0, 'd': 2}
    order = ['b', 'c', 'a']
    reference = pytrec_eval.RelevanceEvaluator({'q': labels}, {'ndcg_cut_10','P_10'}).evaluate({'q': {'b': 3., 'c': 2., 'a': 1.}})['q']
    actual = metrics(order, labels)
    assert actual['ndcg_at_10'] == pytest.approx(reference['ndcg_cut_10'])
    assert actual['precision_at_10'] == pytest.approx(reference['P_10'])


def test_model_must_return_every_candidate_once_and_ground_positive_grades():
    papers = [{'doc_id': 'a', 'text': 'A randomized trial of a treatment.'}, {'doc_id': 'b', 'text': 'An unrelated study.'}]
    good = {'assessments': [{'index': 0, 'grade': 4, 'evidence': 'randomized trial'}, {'index': 1, 'grade': 0, 'evidence': ''}]}
    assert parse_grades(good, papers) == {'a': 4, 'b': 0}
    for bad in [
        {'assessments': good['assessments'][:1]},
        {'assessments': [good['assessments'][0], good['assessments'][0]]},
        {'assessments': [{'index': 0, 'grade': 4, 'evidence': 'imaginary evidence'}, good['assessments'][1]]},
        {'assessments': [{'index': 0, 'grade': True, 'evidence': 'randomized trial'}, good['assessments'][1]]},
    ]:
        with pytest.raises(ValueError):
            parse_grades(bad, papers)


def test_topic_selection_is_order_independent_and_does_not_read_labels():
    topics = [{'topic_id': str(i), 'query_text': str(i)} for i in range(1,51)]
    selected = select_topics(topics)
    assert selected == select_topics(list(reversed(topics)))
    assert len({x['topic_id'] for x in selected}) == 5


def test_budget_ceiling_can_be_raised_to_20_but_not_beyond_and_defaults_to_10(tmp_path):
    # Owner raised the study ceiling from 10 to 20 USD on 2026-10-09.
    raised = Budget(tmp_path / 'a.jsonl', limit_usd=20, lane_limit_usd=20)
    raised.reserve('first', 9.5)
    raised.reserve('second', 9.5)
    with pytest.raises(ValueError, match='exceeded'):
        raised.reserve('third', 1.5)
    clamped = Budget(tmp_path / 'b.jsonl', limit_usd=50, lane_limit_usd=50)
    clamped.reserve('first', 19.5)
    with pytest.raises(ValueError, match='exceeded'):
        clamped.reserve('second', 1)
    default = Budget(tmp_path / 'c.jsonl', lane_limit_usd=10)
    default.reserve('first', 9.5)
    with pytest.raises(ValueError, match='exceeded'):
        default.reserve('second', 1)
