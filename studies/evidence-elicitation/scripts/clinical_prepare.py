"""Freeze a positive-retention probe and public PubMed metadata."""
import hashlib,json,urllib.request,urllib.parse
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];RUN=BASE/'runs/clinical-v1'

def main():
 RUN.mkdir(exist_ok=True)
 audit=json.loads((BASE/'data_manifest/clinical-reference-audit.json').read_text())
 watches={
 'CD012347':{'condition':'depression','condition2':'chronic obstructive pulmonary disease','conditionJoin':'and','treatment':'psychotherapy'},
 'CD010558':{'condition':'treatment-resistant depression','treatment':'psychotherapy','population':'adults'},
 'CD010753':{'condition':'insomnia','treatment':'antidepressants','population':'adults'}}
 topics=[]
 for t in audit['topics']:
  positives=[r for r in t['labels'] if r['abstract_label']==1]
  controls=sorted([r for r in t['labels'] if r['abstract_label']==0],key=lambda r:hashlib.sha256(('clinical-v1:'+t['topic_id']+':'+r['pmid']).encode()).hexdigest())[:10]
  selected=sorted(positives+controls,key=lambda r:hashlib.sha256(('clinical-order-v1:'+t['topic_id']+':'+r['pmid']).encode()).hexdigest())
  topics.append({'id':t['topic_id'],'watch':{'id':t['topic_id'],**watches[t['topic_id']],'priority':'normal','safetySignal':False},'records':selected})
 config={'status':'positive-enriched retention probe, not prevalence/precision evaluation','selection':'all abstract-positive records plus10 SHA-selected abstract-negative controls per topic; no tuning to labels','topics':topics,'model':'gpt-4.1-mini-2025-04-14','strictness':'standard','scope':'actual production parsing/cleaning/domain/design/stageA/match-verification; screening eligibility only, no live retrieval, ranking quotas, digest, personal vault, or end-to-end claim','transport':'budgeted OpenAI JSON-schema single attempts; production gradeStageA responses replayed offline; no paid correction/retry','metadata':'current PubMed snapshot, not historical2019 metadata','budget_total_usd':10}
 p=RUN/'config.json'
 if p.exists():assert json.loads(p.read_text())==config
 else:p.write_text(json.dumps(config,indent=2))
 ids=sorted({r['pmid'] for t in topics for r in t['records']});p=RUN/'pubmed.xml'
 if not p.exists():
  query=urllib.parse.urlencode({'db':'pubmed','id':','.join(ids),'retmode':'xml'})
  url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+query
  raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SciSpark-evaluation/1.0'}),timeout=60).read()
  import xml.etree.ElementTree as ET
  root=ET.fromstring(raw);returned={x.text for x in root.findall('.//MedlineCitation/PMID')};assert returned==set(ids),(set(ids)-returned,returned-set(ids))
  p.write_bytes(raw)
  (RUN/'metadata-manifest.json').write_text(json.dumps({'requested_pmids':ids,'returned_pmids':sorted(returned),'url':url,'sha256':hashlib.sha256(raw).hexdigest()},indent=2))
 print({'topic_pairs':sum(len(t['records']) for t in topics),'unique_pmids':len(ids),'positive_pairs':sum(r['abstract_label'] for t in topics for r in t['records'])})
if __name__=='__main__':main()
