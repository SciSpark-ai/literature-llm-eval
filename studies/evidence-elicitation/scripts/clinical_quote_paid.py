"""Single-attempt paid transport for frozen production Stage A requests."""
import json, math, sys
from pathlib import Path
from pilot import provider
from pilot_api import API
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'runs/clinical-quote-v2'
SKIP={'$schema','minItems','maxItems','minLength','maxLength','minimum','maximum','exclusiveMinimum','exclusiveMaximum','multipleOf','pattern','minProperties','maxProperties','format'}
def clean(x):
    if isinstance(x,list): return [clean(v) for v in x]
    if not isinstance(x,dict): return x
    return {k:({n:clean(s) for n,s in v.items()} if k in {'properties','$defs','definitions','patternProperties'} else clean(v)) for k,v in x.items() if k not in SKIP}
requests=json.loads((D/'stage-a-requests.json').read_text())
bodies=[]
for r in requests:
 q=r['req']
 bodies.append({'model':r['model'],'messages':q['messages'],'max_tokens':q['maxTokens'],'temperature':q['temperature'],'response_format':{'type':'json_schema','json_schema':{'name':'result','strict':False,'schema':clean(q['jsonSchema'])}}})
ceiling=sum(math.ceil(max(.01,((4*len(json.dumps(b,sort_keys=True,ensure_ascii=False).encode())+4096)*.4+b['max_tokens']*1.6)/1e6)*1e6) for b in bodies)/1e6
rows=[json.loads(l) for l in (ROOT/'budget.jsonl').read_text().splitlines()]
reserved=sum(r['ceiling_microusd'] for r in rows if r['event']=='reserved')/1e6
print(json.dumps({'requests':len(bodies),'new_ceiling':ceiling,'previous_reserved':reserved,'combined':reserved+ceiling}),flush=True)
if reserved+ceiling>4: raise RuntimeError('Conservative ranking allocation exceeded')
if '--run' in sys.argv:
 api=API(ROOT,provider().keys,max_output_tokens=8192)
 output={}
 for request,body in zip(requests,bodies):
  output[request['id']]=api.call('llm',body)
  (D/'stage-a-responses.json').write_text(json.dumps(output))
  print('Completed '+str(len(output))+'/'+str(len(bodies)),flush=True)
