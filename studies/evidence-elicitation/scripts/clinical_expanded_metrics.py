import json,math
from pathlib import Path
import pytrec_eval
D=Path(__file__).resolve().parents[1]/'runs/clinical-expanded-v1'
cfg=json.loads((D/'config.json').read_text());results=json.loads((D/'ce-results.json').read_text());rows=[]
for t in results:
 labels={r['pmid']:r['abstract_label'] for r in next(x for x in cfg['topics'] if x['id']==t['topic'])['records']}
 assert set(labels)==set(t['scores'])
 rank=sorted(t['scores'],key=lambda k:(-t['scores'][k],k));total=sum(labels.values());dcg=lambda gains:sum(g/math.log2(i+2) for i,g in enumerate(gains))
 ndcg=dcg([labels[k] for k in rank[:10]])/dcg([1]*min(total,10))
 # Unique descending ranks reproduce deterministic ties in the independent metric library.
 check=pytrec_eval.RelevanceEvaluator({t['topic']:labels},{'ndcg_cut_10','recall_50'}).evaluate({t['topic']:{k:len(rank)-i for i,k in enumerate(rank)}})[t['topic']]
 assert abs(ndcg-check['ndcg_cut_10'])<1e-10
 recall=sum(labels[k] for k in rank[:50])/total;assert abs(recall-check['recall_50'])<1e-10
 rows.append({'topic':t['topic'],'candidates':len(rank),'positive':total,'positive_at10':sum(labels[k] for k in rank[:10]),'ndcg10':ndcg,'recall50':recall,'positive_at50':sum(labels[k] for k in rank[:50])})
(D/'ce-metrics.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
