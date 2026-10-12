import json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'runs/clinical-v1'
config=json.loads((D/'config.json').read_text())
results=json.loads((D/'stage-a-results.json').read_text())
rows=[]
for t in results:
 labels={r['pmid']:r for r in next(x for x in config['topics'] if x['id']==t['topic'])['records']}
 positive=[r for r in t['records'] if labels[r['pmid']]['abstract_label']==1]
 row={'topic':t['topic'],'reference_positive':sum(r['abstract_label']==1 for r in labels.values()),'entered_stage_a':len(positive),'after_quote_and_model':sum(r['grade']['entryId'] is not None for r in positive),'after_match_verification':sum(r['layer'] is not None for r in positive),'after_model_design':sum(r['layer'] is not None and not r['modelDesignDropped'] for r in positive),'invalid_quotes':sum(not r['grade']['quoteVerified'] and r['grade'].get('modelGrade',0)>0 for r in positive),'ungraded':sum(r['grade']['ungraded'] for r in positive)}
 rows.append(row)
 print(row)
print('Failures:')
for t in results:
 labels={r['pmid']:r for r in next(x for x in config['topics'] if x['id']==t['topic'])['records']}
 for r in t['records']:
  if labels[r['pmid']]['abstract_label']==1 and (r['layer'] is None or r['modelDesignDropped']): print(t['topic'],r['pmid'],r['grade'],r['verified'],r['modelDesignDropped'])
(D/'stage-a-summary.json').write_text(json.dumps(rows,indent=2))
