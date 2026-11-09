"""Offline exploratory combinations; global label denominators, exact-score ties."""
import json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'runs/expanded-clinical-pointwise-v1';rows=json.loads((D/'analysis.json').read_text());ce={x['topic']:x['scores'] for x in json.loads((R/'runs/clinical-expanded-v1/ce-results-complete.json').read_text())};out=[]
for topic,scores in ce.items():
 allrows=[r for r in rows if r['topic']==topic];assert set(scores)=={r['pmid'] for r in allrows}
 ordered=sorted(allrows,key=lambda r:(-scores[r['pmid']],hashlib.sha256(('cascade-v1:'+r['pmid']).encode()).hexdigest()))
 variants=[('CE',allrows,lambda r:(scores[r['pmid']],),0),('LLM',allrows,lambda r:(r['grade'],),len(allrows)),('LLM_then_CE',allrows,lambda r:(r['grade'],scores[r['pmid']]),len(allrows))]
 for n in [50,100]:
  variants.append(('CE%d_then_LLM'%n,ordered[:n],lambda r:(r['grade'],),n))
  variants.append(('CE%d_then_LLM_then_CE'%n,ordered[:n],lambda r:(r['grade'],scores[r['pmid']]),n))
 for name,candidates,key,calls in variants:
  for label in ['abstract_label','content_label']:
   positive=sum(r[label] for r in allrows);groups={}
   for r in candidates:groups.setdefault(key(r),[]).append(r[label])
   gains=[]
   for _,v in sorted(groups.items(),reverse=True):gains.extend([sum(v)/len(v)]*len(v))
   dcg=lambda vs:sum(v/math.log2(i+2) for i,v in enumerate(vs))
   out.append({'topic':topic,'variant':name,'label':label,'n':len(allrows),'llm_calls':calls,'candidate_count':len(candidates),'candidate_recall':sum(r[label] for r in candidates)/positive,'ndcg10':dcg(gains[:10])/dcg([1]*min(positive,10)),'precision10':sum(gains[:10])/10,'recall50':sum(gains[:50])/positive,'recall100':sum(gains[:100])/positive})
(D/'cascade-metrics.json').write_text(json.dumps(out,indent=2))
lines=['# Exploratory offline scorer combinations','','2026-10-09. No API calls, new model outputs, prompt changes, or product edits.','','## Methods','','All combinations reuse the complete frozen 682-paper scores. Full-pool LLM_then_CE sorts lexicographically by descending LLM grade, then descending CE score. CE50/CE100 selects the first 50/100 by CE before LLM grading; a fixed SHA-256 PMID tie-break handles CE cutoff ties without labels. Both LLM-only and LLM-plus-CE downstream ordering are reported. Exact ties in each final score tuple use expected metrics. Candidate recall and final recall use positives in the original full topic pool as denominator, never only selected candidates.','','These are post-hoc development combinations motivated by observed ties. They are exploratory, not preregistered or held-out evidence. Pointwise scores can be reused because each saved LLM request contained only its paper; this does not simulate a batched/context-dependent LLM. LLM call counts are prospective unique paper decisions; no latency or monetary saving is measured by this replay.','','## Abstract-label comparison','','| Topic | Variant | nDCG@10 | Recall@50 | Candidate recall | LLM decisions |','|---|---|---:|---:|---:|---:|']
for x in out:
 if x['label']=='abstract_label':lines.append('| %s | %s | %.3f | %.1f%% | %.1f%% | %d |'%(x['topic'],x['variant'],x['ndcg10'],100*x['recall50'],100*x['candidate_recall'],x['llm_calls']))
lines+=['','Full-text inclusion-label metrics are retained in cascade-metrics.json and must be interpreted separately from abstract screening. These are rank-based comparisons with no quote or native feed gate. Candidate truncation losses remain visible even when downstream reranking is excellent.','','## Validation','','Checked equal original candidate identities, expected-score tie handling, and that final recall never exceeds candidate recall. For CE50 variants, recall@50 equals candidate recall by construction. Scores for CE and raw LLM reproduce the preceding standalone metrics to numerical tolerance. Only three exposed topics with sampled negatives; confirm any preferred combination on unseen topics before product adoption.']
for x in out:
 assert x['recall50']<=x['candidate_recall']+1e-9
 if x['candidate_count']==50:assert abs(x['recall50']-x['candidate_recall'])<1e-9
prev=json.loads((D/'metrics.json').read_text())['ranking']
for x in out:
 if x['variant'] in ['CE','LLM']:
  old=next(y for y in prev if y['topic']==x['topic'] and y['label']==x['label'] and y['arm']==('cross-encoder' if x['variant']=='CE' else 'clinical-original-pointwise'))
  assert abs(old['ndcg10']-x['ndcg10'])<1e-9
(R/'reports/expanded-cascade-comparison.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[10:]))
