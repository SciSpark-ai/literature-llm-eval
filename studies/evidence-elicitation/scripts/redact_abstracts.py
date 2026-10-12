"""Remove PubMed abstract text from every frozen artifact, leaving PMIDs, titles, grades and quotes.

Why: abstracts are publisher-copyrighted; the public export ships paper IDs and `fetch_abstracts.py`
instead of the text. Titles, MeSH terms, model outputs and short quoted excerpts are kept.

What is removed:
- `paper.abstract` strings in rule-results.json, rule-ablation.json, common-candidates.json;
- the abstract part (after the first newline) of `candidates[].text` in inputs.json and
  wiki-results.json files;
- `candidates[].abstract` inside the JSON string carried by Stage A request messages (byte-level
  replacement of the escaped abstract so the rest of the request is untouched);
- `papers[].abstract` and `papers[].sentences` inside E5 extraction requests;
- the raw PubMed XML downloads.

Each removed string is replaced by `[ABSTRACT REDACTED sha256:<12 hex>]`. `runs/redaction-manifest.json`
maps every hash to the PMID, the kind of text (raw PubMed abstract, or the cleaned visible text the
model saw) and its length, so `fetch_abstracts.py` can refetch and verify.

Safe to run again on an already redacted tree: placeholders are left alone and the manifest is added
to, not replaced. Before finishing, every file under runs/ is searched for each text removed in this
run; if one is still present anywhere the script exits with an error and names the files.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = '[ABSTRACT REDACTED sha256:%s]'


def h12(s):
    return hashlib.sha256(s.encode()).hexdigest()[:12]


class Redactor:
    def __init__(self):
        self.manifest = {}  # hash -> {pmid, kind, length}
        self.replacements = 0
        self.removed = set()  # the texts themselves, for the final leak check; never written out

    def note(self, text, pmid, kind):
        key = h12(text)
        self.removed.add(text)
        self.manifest.setdefault(key, {'pmid': pmid, 'kind': kind, 'length': len(text)})
        return PLACEHOLDER % key

    # --- structured files -------------------------------------------------
    def redact_paper_dicts(self, obj, pmid_hint=None):
        """Recursively replace `abstract` strings in dicts that carry a paper id."""
        if isinstance(obj, dict):
            pmid = pmid_hint
            if isinstance(obj.get('ids'), dict) and obj['ids'].get('pmid'):
                pmid = str(obj['ids']['pmid'])
            if obj.get('pmid'):
                pmid = str(obj['pmid'])
            if isinstance(obj.get('abstract'), str) and obj['abstract'] and not obj['abstract'].startswith('[ABSTRACT REDACTED'):
                obj['abstract'] = self.note(obj['abstract'], pmid, 'raw_abstract')
                self.replacements += 1
            if isinstance(obj.get('text'), str) and '\n' in obj['text'] and obj.get('pmid') and not obj['text'].split('\n', 1)[1].startswith('[ABSTRACT REDACTED'):
                title, body = obj['text'].split('\n', 1)
                obj['text'] = title + '\n' + self.note(body, str(obj['pmid']), 'cleaned_visible_text')
                self.replacements += 1
            for v in obj.values():
                self.redact_paper_dicts(v, pmid)
        elif isinstance(obj, list):
            for v in obj:
                self.redact_paper_dicts(v, pmid_hint)

    # --- Stage A requests ---------------------------------------------------
    def redact_stage_a_requests(self, requests, results):
        """results gives the PMID order per topic (same order as candidates in the request stream)."""
        order = {t['topic']: [r['pmid'] for r in t['records']] for t in results}
        cursor = {t: 0 for t in order}
        for r in requests:
            msg = r['req']['messages'][1]
            content = msg['content']
            try:
                user = json.loads(content)
                cands = user['candidates']
            except (ValueError, KeyError, TypeError):
                continue
            for c in cands:
                pmid = order[r['topic']][cursor[r['topic']]]
                cursor[r['topic']] += 1
                a = c.get('abstract')
                if not a or a.startswith('[ABSTRACT REDACTED'):
                    continue
                token = self.note(a, pmid, 'cleaned_visible_text')
                done = False
                for enc in (json.dumps(a, ensure_ascii=False)[1:-1], json.dumps(a)[1:-1]):
                    if enc in content:
                        content = content.replace(enc, json.dumps(token)[1:-1])
                        done = True
                        break
                if not done:
                    raise ValueError('Could not locate abstract for PMID %s in request %s' % (pmid, r['id'][:8]))
                self.replacements += 1
            msg['content'] = content

    # --- Wiki requests (<<<PAPERS>>> block) --------------------------------
    def redact_wiki_requests(self, requests, inputs):
        texts = {c['pmid']: c['text'] for t in inputs for c in t['candidates']}
        for r in requests:
            msg = r['req']['messages'][1]
            content = msg['content']
            for pmid, text in texts.items():
                if '\n' not in text:
                    continue
                title, body = text.split('\n', 1)
                if body.startswith('[ABSTRACT REDACTED'):
                    continue
                token = self.note(body, pmid, 'cleaned_visible_text')
                for enc in (json.dumps(body, ensure_ascii=False)[1:-1], json.dumps(body)[1:-1]):
                    if enc in content:
                        content = content.replace(enc, json.dumps(token)[1:-1])
                        self.replacements += 1
                        break
            msg['content'] = content

    # --- E5 requests ----------------------------------------------------------
    def redact_e5_requests(self, doc):
        for r in doc['requests']:
            msg = r['body']['messages'][1]
            user = json.loads(msg['content'])
            for i, p in enumerate(user['papers']):
                pmid = r['indices'][i]
                if isinstance(p.get('abstract'), str) and p['abstract'] and not p['abstract'].startswith('[ABSTRACT REDACTED'):
                    p['abstract'] = self.note(p['abstract'], pmid, 'cleaned_visible_text')
                    self.replacements += 1
                if isinstance(p.get('sentences'), list) and p['sentences'] and not any(str(text).startswith('[ABSTRACT REDACTED') for _, text in p['sentences']):
                    joined = '\n'.join(s for _, s in p['sentences'])
                    token = self.note(joined, pmid, 'cleaned_sentences_joined_by_newline')
                    p['sentences'] = [[0, p['sentences'][0][1]], [1, token]] if p['sentences'] else []
                    self.replacements += 1
            msg['content'] = json.dumps(user, ensure_ascii=False)


def load(p):
    return json.loads(p.read_text())


def save(p, obj):
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + '\n')


def find_leaks(runs, texts, minimum=200):
    """Files under runs/ that still hold one of the removed texts, plain or JSON-escaped."""
    needles = set()
    for text in texts:
        if len(text) >= minimum and 'ABSTRACT REDACTED' not in text:
            # A stretch from the middle, longer than any quoted excerpt the artifacts keep on purpose
            # (a model's supporting quote is one sentence), recognises the text and survives re-wrapping of its ends.
            half = min(len(text), 360) // 2
            middle = text[len(text) // 2 - half:len(text) // 2 + half]
            needles.update({middle, json.dumps(middle, ensure_ascii=False)[1:-1], json.dumps(middle)[1:-1]})
    leaks = []
    for path in sorted(runs.rglob('*')):
        if path.is_file() and path.suffix in ('.json', '.jsonl', '.md', '.txt', '.csv', '.xml'):
            body = path.read_text(errors='replace')
            if any(needle in body for needle in needles):
                leaks.append(str(path.relative_to(runs.parent)))
    return leaks


def main(root):
    rd = Redactor()
    runs = root / 'runs'
    removed_files = []
    for run in sorted(d for d in runs.iterdir() if d.is_dir()):
        # Requests first: the Wiki request redaction needs the still-unredacted inputs.json texts.
        req, res = run / 'stage-a-requests.json', run / 'stage-a-results.json'
        if req.exists() and res.exists():
            requests = load(req)
            rd.redact_stage_a_requests(requests, load(res))
            save(req, requests)
        elif req.exists() and (run / 'inputs.json').exists():
            requests = load(req)
            rd.redact_wiki_requests(requests, load(run / 'inputs.json'))
            save(req, requests)
        e5 = run / 'requests.json'
        if e5.exists():
            doc = load(e5)
            if 'requests' in doc and doc['requests'] and 'indices' in doc['requests'][0]:
                rd.redact_e5_requests(doc)
                save(e5, doc)
        for name in ('rule-results.json', 'rule-ablation.json', 'common-candidates.json', 'inputs.json', 'wiki-results.json'):
            p = run / name
            if p.exists():
                obj = load(p)
                rd.redact_paper_dicts(obj)
                save(p, obj)
        for xml in run.glob('pubmed*.xml'):
            removed_files.append(str(xml.relative_to(root)))
            xml.unlink()
    leaks = find_leaks(runs, rd.removed)
    if leaks:
        sys.exit('Abstract text removed elsewhere is still present in: ' + ', '.join(leaks))
    previous = load(runs / 'redaction-manifest.json') if (runs / 'redaction-manifest.json').exists() else {}
    entries = {**previous.get('entries', {}), **rd.manifest}
    removed_files = sorted(set(previous.get('removed_files', [])) | set(removed_files))
    manifest = {'placeholder_format': PLACEHOLDER % '<12 hex of sha256 of the removed text>', 'replacements': previous.get('replacements', 0) + rd.replacements,
                'removed_files': removed_files, 'pmids': sorted({v['pmid'] for v in entries.values() if v['pmid']}),
                'entries': entries}
    save(runs / 'redaction-manifest.json', manifest)
    print(json.dumps({'replacements_this_run': rd.replacements, 'unique_texts': len(entries), 'pmids': len(manifest['pmids']), 'removed_files': len(removed_files)}))


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT)
