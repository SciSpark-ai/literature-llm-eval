"""Offline metrics and durable spending reservations; no provider access here."""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
from datetime import datetime, timezone


def _micros(amount):
    if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
        raise ValueError('Invalid cost')
    return math.ceil(amount * 1_000_000)


class Budget:
    """Reservations are never released, including after timeout or process failure.

    This intentionally overcounts spending. File locking protects concurrent
    reservations. A request with uncertain status requires manual review, not retry.
    """
    def __init__(self, path, limit_usd=10, lane_limit_usd=4, enforce_limit=True):
        self.path = Path(path)
        self.enforce_limit = enforce_limit
        # Hard study ceiling: raised from 10 to 20 USD by the owner on 2026-10-09. The default stays 10;
        # a script must pass limit_usd=20 explicitly to use the higher ceiling.
        self.limit = min(_micros(limit_usd), 20_000_000)
        self.lane_limit = min(_micros(lane_limit_usd), self.limit)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, event, validate):
        with self.path.open('a+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            rows = [json.loads(line) for line in f if line.strip()]
            validate(rows)
            event['at'] = datetime.now(timezone.utc).isoformat()
            f.seek(0, 2)
            f.write(json.dumps(event) + '\n')
            f.flush()
            os.fsync(f.fileno())

    def reserve(self, request_id, ceiling_usd):
        value = _micros(ceiling_usd)
        if value <= 0:
            raise ValueError('Reservation must be positive')
        def validate(rows):
            reservations = [r for r in rows if r['event'] == 'reserved']
            if any(r['request_id'] == request_id for r in reservations):
                raise ValueError('Request already reserved; inspect trace before retry')
            if any(r.get('status') == 'cost_overrun' for r in rows):
                raise ValueError('Earlier pricing overrun requires review')
            total = sum(r['ceiling_microusd'] for r in reservations)
            lane = sum(r['ceiling_microusd'] for r in reservations if r['lane'] == 'ranking')
            if self.enforce_limit and (total + value > self.limit or lane + value > self.lane_limit):
                raise ValueError('Budget would be exceeded')
        self._append({'event': 'reserved', 'request_id': request_id, 'lane': 'ranking', 'ceiling_microusd': value}, validate)

    def finish(self, request_id, estimated_usd, status):
        value = None if estimated_usd is None else _micros(estimated_usd)
        event = {'event': 'finished', 'request_id': request_id, 'estimated_microusd': value, 'status': status}
        def validate(rows):
            reservation = next((r for r in rows if r['event'] == 'reserved' and r['request_id'] == request_id), None)
            if reservation is None:
                raise ValueError('No reservation')
            if any(r['event'] == 'finished' and r['request_id'] == request_id for r in rows):
                raise ValueError('Already finished')
            if value is not None and value > reservation['ceiling_microusd']:
                event['status'] = 'cost_overrun'
        self._append(event, validate)
        if event['status'] == 'cost_overrun':
            raise ValueError('Reported cost exceeded reservation; stop all further calls')


def metrics(ranked_ids, labels, k=10):
    if len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError('Duplicate documents in run')
    known = {d: v for d, v in labels.items() if v >= 0}
    gains = [max(0, known.get(d, 0)) for d in ranked_ids[:k]]
    ideal = sorted(known.values(), reverse=True)[:k]
    dcg = lambda values: sum(v / math.log2(i + 2) for i, v in enumerate(values))
    idcg = dcg(ideal)
    relevant = {d for d, v in known.items() if v > 0}
    return {
        'ndcg_at_10': dcg(gains) / idcg if idcg else 0.,
        'precision_at_10': sum(v > 0 for v in gains) / k,
        'judged_at_10': sum(d in known for d in ranked_ids[:k]) / k,
        'recall_at_pool': len(set(ranked_ids) & relevant) / len(relevant) if relevant else 0.,
    }


def evaluate_runs(runs, qrels, topic_ids):
    if not topic_ids or len(topic_ids) != len(set(topic_ids)):
        raise ValueError('Expected unique nonempty topic list')
    per_topic = {q: metrics(runs.get(q, []), qrels[q]) for q in topic_ids}
    return {'per_topic': per_topic, 'mean': {name: sum(r[name] for r in per_topic.values()) / len(topic_ids) for name in next(iter(per_topic.values()))}}


def parse_grades(response, candidates):
    assessments = response.get('assessments', [])
    if len(assessments) != len(candidates):
        raise ValueError('Incomplete grading batch')
    grades = {}
    seen = set()
    for item in assessments:
        i, grade = item.get('index'), item.get('grade')
        if type(i) is not int or i not in range(len(candidates)) or i in seen:
            raise ValueError('Invalid or duplicate candidate index')
        if type(grade) is not int or not 0 <= grade <= 4:
            raise ValueError('Invalid relevance grade')
        evidence = item.get('evidence', '')
        fold = lambda x: ' '.join(x.split()).casefold()
        if not isinstance(evidence, str) or (grade > 0 and (len(evidence.strip()) < 8 or fold(evidence) not in fold(candidates[i]['text']))):
            raise ValueError('Positive grade lacks a matching source excerpt')
        seen.add(i)
        grades[candidates[i]['doc_id']] = grade
    return grades


def select_topics(topics, count=5):
    return sorted(topics, key=lambda t: hashlib.sha256(('scispark-pilot-v1:' + t['topic_id']).encode()).hexdigest())[:count]
