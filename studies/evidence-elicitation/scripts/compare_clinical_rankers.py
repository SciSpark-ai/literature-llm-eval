import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'runs';D=R/'wiki-clinical-v1'
config=json.loads((R/'clinical-v1/config.json').read_text())
wiki=json.loads((D/'wiki-results.json').read_text());ce={t['topic']:t['scores'] for t in json.loads((D/'ce-results.json').read_text())}
clinical={}
for variant in ['clinical-v1','clinical-quote-v2']:
 req=json.loads((R/variant/'stage-a-requests.json').read_text());responses=json.loads((R/variant/'stage-a-responses.json').read_text())
 base=json.loads((R/'clinical-v1/rule-results.json').read_text());offsets={};bytopic={}
 for q in req:
  topic=q['topic'];offset=offsets.get(topic,0);candidates=next(t for t in base['topics'] if t['id']==topic)['candidates'][offset:offset+20]
  assessments=json.loads(responses[q['id']]['choices'][0]['message']['content'])['assessments']
  assert sorted(a['index'] for a in assessments)==list(range(len(candidates)))
  bytopic.setdefault(topic,{}).update({candidates[a['index']]['key']:a['grade'] for a in assessments});offsets[topic]=offset+len(candidates)
 clinical[variant]=bytopic
out=[]
for t in wiki:
 topic=t['topic'];labels={r['pmid']:r['abstract_label'] for r in next(c for c in config['topics'] if c['id']==topic)['records']}
 weights={'question':50,'topic':30,**({'approach':20} if t['context']['hasApproach'] else {})}
 scores={r['pmid']:sum((r['raw'][k]['grade'] or 0)*v for k,v in weights.items())/sum(weights.values()) for r in t['records']}
 methods={'wiki-raw':scores,'ce':ce[topic],**{v:clinical[v][topic] for v in clinical}}
 for method,m in methods.items():
  assert set(m)==set(scores)
  ranked=sorted(m,key=lambda key:(-m[key],key))
  gains=[labels[k] for k in ranked[:10]];ideal=sorted([labels[k] for k in m],reverse=True)[:10]
  dcg=lambda values:sum(v/math.log2(i+2) for i,v in enumerate(values))
  out.append({'topic':topic,'method':method,'nDCG10_conditional_pool':dcg(gains)/dcg(ideal),'positive_at10':sum(gains),'pool_size':len(m),'positive_in_pool':sum(labels[k] for k in m)})
print(json.dumps(out,indent=2));(D/'rank-comparison.json').write_text(json.dumps(out,indent=2))
for t in wiki:
 labels={r['pmid']:r['abstract_label'] for r in next(c for c in config['topics'] if c['id']==t['topic'])['records']}
 print('Wiki postvalidation',t['topic'],'positive retained',sum(r['kept'] for r in t['records'] if labels[r['pmid']]==1),'controls retained',sum(r['kept'] for r in t['records'] if labels[r['pmid']]==0))
