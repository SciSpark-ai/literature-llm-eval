"""Frozen expanded development pool; no paid models, no score-based selection."""
import hashlib,json,time,urllib.request,urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parents[1]; RUN=BASE/'runs/clinical-expanded-v1'
RUN.mkdir(exist_ok=True)
audit=json.loads((BASE/'data_manifest/clinical-reference-audit.json').read_text())
old=json.loads((BASE/'runs/clinical-v1/config.json').read_text())
topics=[]
for t in audit['topics']:
 pos=[r for r in t['labels'] if r['abstract_label']==1]
 neg=sorted([r for r in t['labels'] if r['abstract_label']==0],key=lambda r:hashlib.sha256(('clinical-v1:'+t['topic_id']+':'+r['pmid']).encode()).hexdigest())[:200]
 records=sorted(pos+neg,key=lambda r:hashlib.sha256(('clinical-order-v1:'+t['topic_id']+':'+r['pmid']).encode()).hexdigest())
 assert len(records)==len({r['pmid'] for r in records})
 prior=next(x for x in old['topics'] if x['id']==t['topic_id'])
 assert {r['pmid'] for r in prior['records']}<={r['pmid'] for r in records}
 topics.append({'id':t['topic_id'],'watch':prior['watch'],'records':records,'full_reference_pool_size':t['candidate_count']})
config={'status':'expanded exposed development topics, not held-out','selection':'all abstract positives plus first 200 abstract negatives by original clinical-v1 SHA order; includes prior ten controls; no score-based mining','topics':topics,'scope':'common pre-domain-filter candidate pool; rankers must not inherit psychiatry prefilter exclusions','labels':'abstract labels primary, full-text labels secondary; review exclusions are not necessarily irrelevant clinical feed items','budget_total_usd':10}
p=RUN/'config.json'
if p.exists():assert json.loads(p.read_text())==config
else:p.write_text(json.dumps(config,indent=2))
known={a.findtext('./MedlineCitation/PMID'):a for a in ET.parse(BASE/'runs/clinical-v1/pubmed.xml').getroot().findall('PubmedArticle')}
ids=sorted({r['pmid'] for t in topics for r in t['records']})
missing=[p for p in ids if p not in known]; batches=[]
for offset in range(0,len(missing),100):
 batch=missing[offset:offset+100];file=RUN/('pubmed-batch-%03d.xml'%(offset//100))
 url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urllib.parse.urlencode({'db':'pubmed','id':','.join(batch),'retmode':'xml'})
 if not file.exists():
  raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SciSpark-evaluation/1.0'}),timeout=60).read()
  root=ET.fromstring(raw); returned={a.findtext('./MedlineCitation/PMID') for a in root.findall('PubmedArticle')}
  assert returned==set(batch),(set(batch)-returned)
  file.write_bytes(raw);time.sleep(.4)
 root=ET.parse(file).getroot();returned={a.findtext('./MedlineCitation/PMID') for a in root.findall('PubmedArticle')};assert returned==set(batch)
 known.update({a.findtext('./MedlineCitation/PMID'):a for a in root.findall('PubmedArticle')})
 batches.append({'file':file.name,'url':url,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 print('Metadata batch',offset//100+1,'completed',flush=True)
root=ET.Element('PubmedArticleSet')
for pmid in ids:root.append(known[pmid])
ET.ElementTree(root).write(RUN/'pubmed.xml',encoding='utf-8',xml_declaration=True)
manifest={'created_at':datetime.now(timezone.utc).isoformat(),'topic_pairs':sum(len(t['records']) for t in topics),'unique_pmids':len(ids),'positive_pairs':sum(r['abstract_label'] for t in topics for r in t['records']),'new_public_records':len(missing),'missing_pmids':[],'reused_snapshot':'clinical-v1/pubmed.xml','batches':batches,'combined_sha256':hashlib.sha256((RUN/'pubmed.xml').read_bytes()).hexdigest()}
(RUN/'metadata-manifest.json').write_text(json.dumps(manifest,indent=2));print({k:v for k,v in manifest.items() if k not in ['batches']},flush=True)
