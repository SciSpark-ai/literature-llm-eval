import json
from pathlib import Path
from pilot import provider
from pilot_core import Budget
R=Path(__file__).resolve().parents[1];D=R/'runs/clinical-expanded-v1'
api=provider();api.budget=Budget(R/'budget.jsonl',lane_limit_usd=6)
inputs=json.loads((D/'inputs.json').read_text());out=[]
for t in inputs:
 scores={}
 for offset in range(0,len(t['candidates']),40):
  batch=t['candidates'][offset:offset+40]
  response=api.call('ce',{'model':'jina-reranker-v2-base-multilingual','query':t['query'],'documents':[c['text'] for c in batch],'top_n':len(batch),'return_documents':False})
  results=response['results'];assert sorted(x['index'] for x in results)==list(range(len(batch)))
  scores.update({batch[x['index']]['pmid']:x['relevance_score'] for x in results})
 out.append({'topic':t['topic'],'scores':scores,'batch_size':40})
 (D/'ce-results.json').write_text(json.dumps(out,indent=2))
 print('Completed CE '+t['topic'],flush=True)
