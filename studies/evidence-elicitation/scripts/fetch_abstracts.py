"""Refetch the PubMed abstracts that `redact_abstracts.py` removed, for local analysis only.

Usage:
  python3 scripts/fetch_abstracts.py            # fetch all PMIDs in runs/redaction-manifest.json
  python3 scripts/fetch_abstracts.py --verify   # also report how many raw abstracts match the recorded hashes

Writes data/abstracts.json: {pmid: {"title": ..., "abstract": ...}} from NCBI E-utilities (efetch, XML),
200 PMIDs per request, one request per second. Set NCBI_EMAIL to identify yourself to NCBI (recommended).

Two kinds of removed text are recorded in the manifest. `raw_abstract` entries are the PubMed abstract as
parsed at capture time and should hash-match the refetched text unless NCBI has since revised the record.
`cleaned_visible_text` entries are what the model actually saw: the production cleaner's output, truncated
to 1800 characters. That cleaner is private, so those strings cannot be rebuilt exactly here; analyses that
need the visible text use title plus the first 1800 characters of the raw abstract as an approximation
and say so (see e45_lib.candidate_text).
"""
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EFETCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'


def fetch_batch(pmids):
    params = {'db': 'pubmed', 'id': ','.join(pmids), 'retmode': 'xml', 'rettype': 'abstract'}
    if os.environ.get('NCBI_EMAIL'):
        params['email'] = os.environ['NCBI_EMAIL']
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(EFETCH, data=data), timeout=60) as r:
        return r.read()


def parse(xml_bytes):
    out = {}
    root = ET.fromstring(xml_bytes)
    for art in root.iter('PubmedArticle'):
        pmid = art.findtext('.//PMID')
        title = ''.join(art.find('.//ArticleTitle').itertext()) if art.find('.//ArticleTitle') is not None else ''
        parts = []
        for node in art.findall('.//Abstract/AbstractText'):
            label = node.get('Label')
            text = ''.join(node.itertext()).strip()
            parts.append((label + ': ' + text) if label else text)
        out[pmid] = {'title': title.strip(), 'abstract': '\n'.join(parts)}
    return out


def main(argv):
    manifest = json.loads((ROOT / 'runs/redaction-manifest.json').read_text())
    pmids = manifest['pmids']
    out_path = ROOT / 'data/abstracts.json'
    have = json.loads(out_path.read_text()) if out_path.exists() else {}
    todo = [p for p in pmids if p not in have]
    print('pmids total %d, already fetched %d, to fetch %d' % (len(pmids), len(have), len(todo)))
    for i in range(0, len(todo), 200):
        batch = todo[i:i + 200]
        have.update(parse(fetch_batch(batch)))
        out_path.write_text(json.dumps(have, indent=1, ensure_ascii=False))
        print('fetched %d/%d' % (min(i + 200, len(todo)), len(todo)), flush=True)
        time.sleep(1)
    missing = [p for p in pmids if p not in have]
    print('missing after fetch:', missing)
    if '--verify' in argv:
        ok = tried = 0
        for key, e in manifest['entries'].items():
            if e['kind'] != 'raw_abstract' or e['pmid'] not in have:
                continue
            tried += 1
            ok += hashlib.sha256(have[e['pmid']]['abstract'].encode()).hexdigest()[:12] == key
        print('raw abstracts hash-matching the capture-time text: %d of %d (mismatches usually mean NCBI revised the record or the capture parser joined sections differently)' % (ok, tried))


if __name__ == '__main__':
    main(sys.argv[1:])
