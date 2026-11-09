"""Verify the public score package without network access or private dependencies."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text())


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    manifest = read('data/artifact-manifest.json')
    actual = {
        str(p.relative_to(ROOT)) for p in ROOT.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts
        and '.pytest_cache' not in p.parts
        and p.name != 'artifact-manifest.json'
    }
    check(actual == set(manifest), 'Public file inventory differs from the manifest')
    for name, expected in manifest.items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected,
              'Artifact hash mismatch: ' + name)

    rows = read('runs/expanded-clinical-pointwise-v1/analysis.json')
    pool = read('data/pool-config.json')
    ce = read('runs/clinical-expanded-v1/ce-results-complete.json')
    inputs = read('data/input-manifest.json')
    fields = {'topic', 'pmid', 'abstract_label', 'content_label', 'grade',
              'entryPositive', 'validQuote', 'entryAfterQuote'}
    ids = {(r['topic'], r['pmid']) for r in rows}
    check(len(ids) == len(rows) == 682, 'Unexpected or duplicate candidate identities')
    check(sum(r['abstract_label'] for r in rows) == 82, 'Abstract-label count changed')
    check(sum(r['content_label'] for r in rows) == 41, 'Final-inclusion count changed')
    labels = {(t['id'], r['pmid']): r for t in pool['topics'] for r in t['records']}
    check(set(labels) == ids, 'Label pool and scored pool differ')
    check({(r['topic'], r['pmid']) for r in inputs} == ids and len(inputs) == 682,
          'Input manifest and scored pool differ')
    check({(t['topic'], pmid) for t in ce for pmid in t['scores']} == ids,
          'CE and LLM pools differ')
    for r in rows:
        check(set(r) == fields, 'Unexpected field in public score projection')
        check(re.fullmatch(r'\d+', r['pmid']) is not None, 'Invalid PMID')
        check(type(r['grade']) is int and 0 <= r['grade'] <= 4, 'Invalid grade')
        for field in ('abstract_label', 'content_label'):
            check(r[field] in (0, 1), 'Invalid binary label')
            check(r[field] == labels[r['topic'], r['pmid']][field], 'Label mismatch')
        for field in ('entryPositive', 'validQuote', 'entryAfterQuote'):
            check(type(r[field]) is bool, 'Invalid validation flag')
        check(not r['entryAfterQuote'] or (r['entryPositive'] and r['validQuote']),
              'Quote-gate flag inconsistent with entry and quote flags')
    for t in ce:
        check(all(math.isfinite(v) for v in t['scores'].values()), 'Nonfinite CE score')
    for r in inputs:
        for field in ('submitted_text_sha256', 'request_body_sha256'):
            check(re.fullmatch(r'[a-f0-9]{64}', r[field]) is not None, 'Invalid input hash')

    template = read('data/llm-request-template.json')
    payload = json.loads(template['messages'][1]['content'])
    check(payload['examplePapers'] == [], 'Unexpected paper examples')
    check(payload['candidates'] == [{
        'index': 0, 'title': '<paper title>',
        'abstract': '<first 1800 characters of cleaned abstract>',
    }], 'Paper text has not been replaced by placeholders')

    links = 0
    for p in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            check((p.parent / target.split('#', 1)[0]).resolve().exists(),
                  'Missing local link in ' + str(p.relative_to(ROOT)) + ': ' + target)
            links += 1
    for name in actual:
        text = (ROOT / name).read_text()
        check(not re.search(r'/(?:Users|home)/[A-Za-z0-9_.-]+/|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----', text),
              'Potential private path or credential in ' + name)
    print(json.dumps({'status': 'passed', 'files': len(actual), 'records': len(rows),
                      'local_links': links, 'scope': 'Artifact integrity, schemas, identities, labels, and link checks'}, indent=2))


if __name__ == '__main__':
    main()
