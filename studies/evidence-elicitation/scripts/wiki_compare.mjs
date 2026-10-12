import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {createServer} from '../../../scispark-wiki-psychiatry/node_modules/vite/dist/node/index.js';
const study=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),root=path.resolve(study,'../../scispark-wiki-psychiatry'),dir=path.join(study,'runs/wiki-clinical-v1');
await fs.mkdir(dir,{recursive:true});
for(const file of ['assessment-skill.ts','engine.ts','contract.ts']) {
 const rel='src/lib/recommendation/'+file;
 if(!execFileSync('git',['show','435afcd:'+rel],{cwd:root}).equals(await fs.readFile(path.join(root,rel))))throw Error('Upstream drift '+file);
}
const server=await createServer({root,configFile:false,server:{middlewareMode:true,hmr:false,ws:false},resolve:{alias:{'@':path.join(root,'src')}}});
try{
 const load=p=>server.ssrLoadModule('/src/lib/'+p+'.ts');
 const [{recommendationAssessmentSkill:skill},{runSkill},{MemoryVaultStorage},{DEFAULT_SETTINGS},{scoreCandidate}]=await Promise.all([load('recommendation/assessment-skill'),load('skills/runner'),load('vault/memory-storage'),load('llm/settings'),load('recommendation/engine')]);
 const base=JSON.parse(await fs.readFile(path.join(study,'runs/clinical-v1/rule-results.json'),'utf8'));
 const cfg=JSON.parse(await fs.readFile(path.join(study,'runs/clinical-v1/config.json'),'utf8'));
 const mode=process.argv[2]??'capture',requests=[],results=[];
 const saved=mode==='replay'?JSON.parse(await fs.readFile(path.join(dir,'stage-a-responses.json'),'utf8')):{};
 for(const t of base.topics){
  const w=cfg.topics.find(x=>x.id===t.id).watch;
  const query=`${w.treatment} for ${w.condition}${w.condition2?' AND '+w.condition2:''}${w.population?' in '+w.population:''}`;
  const context={text:query,topics:[query],hasQuestion:true,hasApproach:Boolean(w.population),memories:[],fieldPreferences:[],diversity:'focused'};
  const records=[];
  for(let i=0;i<t.candidates.length;i+=20){
   const candidates=t.candidates.slice(i,i+20).map(c=>({...c.paper,abstract:c.paper.abstract?.slice(0,1800)}));
   const provider={id:'openai',jsonSchemaTarget:'draft-07',complete:async(model,request)=>{
    const req={...request,temperature:0};const id=createHash('sha256').update(JSON.stringify({model,req})).digest('hex');
    if(mode==='capture'){requests.push({id,topic:t.id,model,req});throw Error('Capture only');}
    const r=saved[id];if(!r)throw Error('Missing response; no retry');
    return {text:r.choices[0].message.content,usage:{inputTokens:r.usage.prompt_tokens,outputTokens:r.usage.completion_tokens},model,provider:'openai',stopReason:'stop'};
   }};
   const run=await runSkill({skill,input:{context,candidates},storage:new MemoryVaultStorage(),settings:{...DEFAULT_SETTINGS,tierModels:{fast:{provider:'openai',model:cfg.model},strong:{provider:'openai',model:cfg.model}},dailyBudgetUsd:10},providerOverride:{fast:provider}});
   if(mode==='replay'){
    if(run.status!=='ok'||!run.output)throw Error('Wiki validation failed: '+t.id+' batch '+i);
    for(let j=0;j<candidates.length;j++){
     const raw=run.output.assessments.find(a=>a.index===j);if(!raw)throw Error('Missing assessment');
     const scored=scoreCandidate({paper:candidates[j],sources:['pubmed'],queries:[query]},raw,context,[],new Date('2026-10-09T00:00:00Z'));
     records.push({pmid:candidates[j].ids.pmid,raw,kept:Boolean(scored),ranking:scored?.ranking});
    }
   }
  }
  results.push({topic:t.id,context,query,records,candidates:t.candidates.map(c=>({pmid:c.key,text:c.paper.title+'\n'+(c.paper.abstract??'').slice(0,1800)}))});
 }
 await fs.writeFile(path.join(dir,mode==='capture'?'stage-a-requests.json':'wiki-results.json'),JSON.stringify(mode==='capture'?requests:results,null,2));
 await fs.writeFile(path.join(dir,'inputs.json'),JSON.stringify(results.map(({topic,query,candidates,context})=>({topic,query,candidates,context})),null,2));
 console.log({mode,batches:requests.length,topics:results.length});
}finally{await server.close();}
