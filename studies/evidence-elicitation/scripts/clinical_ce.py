import json
from pathlib import Path
from pilot import provider
from pilot_core import Budget
R=Path(__file__).resolve().parents[1];D=R/'runs/wiki-clinical-v1'
api=provider();api.budget=Budget(R/'budget.jsonl',lane_limit_usd=6)
inputs=json.loads((D/'inputs.json').read_text());out=[]
for t in inputs:
 response=api.call('ce',{'model':'jina-reranker-v2-base-multilingual','query':t['query'],'documents':[c['text'] for c in t['candidates']],'top_n':len(t['candidates']),'return_documents':False})
 results=response['results'];assert sorted(x['index'] for x in results)==list(range(len(t['candidates'])))
 out.append({'topic':t['topic'],'scores':{t['candidates'][x['index']]['pmid']:x['relevance_score'] for x in results}})
 (D/'ce-results.json').write_text(json.dumps(out,indent=2))
 print('Completed CE '+t['topic'],flush=True)
