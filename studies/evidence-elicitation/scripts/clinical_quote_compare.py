"""Paired descriptive analysis; these are development topics, not held-out claims."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'runs'
config=json.loads((R/'clinical-v1/config.json').read_text())
output=[]
for name in ['clinical-v1','clinical-quote-v2']:
 d=R/name
 results=json.loads((d/'stage-a-results.json').read_text())
 responses=json.loads((d/'stage-a-responses.json').read_text())
 for t in results:
  labels={r['pmid']:r for r in next(v for v in config['topics'] if v['id']==t['topic'])['records']}
  pos=[r for r in t['records'] if labels[r['pmid']]['abstract_label']==1]
  kept=lambda r:r['layer'] is not None and not r['modelDesignDropped']
  row={'variant':name,'topic':t['topic'],'positive_entered':len(pos),'positive_kept':sum(kept(r) for r in pos),'positive_quote_fail':sum(r['grade'].get('modelGrade',0)>0 and not r['grade']['quoteVerified'] for r in pos),'controls_kept':sum(kept(r) for r in t['records'] if labels[r['pmid']]['abstract_label']==0),'ungraded':sum(r['grade']['ungraded'] for r in t['records'])}
  output.append(row)
 cost=sum((r['usage']['prompt_tokens']*.4+r['usage']['completion_tokens']*1.6)/1e6 for r in responses.values())
 print(name,'estimated_usd',cost)
print(json.dumps(output,indent=2))
(R/'clinical-quote-v2/comparison.json').write_text(json.dumps(output,indent=2)+'\n')
