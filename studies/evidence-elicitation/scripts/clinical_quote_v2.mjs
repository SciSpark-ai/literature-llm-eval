import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createServer} from '../../../scispark-wiki-psychiatry/node_modules/vite/dist/node/index.js';
const study=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const root=path.resolve(study,'../../scispark-wiki-psychiatry');
const dir=path.join(study,'runs/clinical-quote-v2');
const mode=process.argv[2]??'capture';
const server=await createServer({root,configFile:false,server:{middlewareMode:true,hmr:false,ws:false},resolve:{alias:{'@':path.join(root,'src')}}});
try {
 const load=p=>server.ssrLoadModule('/src/lib/'+p+'.ts');
 const [{gradeStageA},{MemoryVaultStorage},{DEFAULT_SETTINGS},{verifyMatchedParts},{loadPsychiatryPack},{layerOf},{designAccepted}]=await Promise.all([load('clinical/grade/stage-a'),load('vault/memory-storage'),load('llm/settings'),load('clinical/grade/verify-parts'),load('clinical/pack/load'),load('clinical/select/select'),load('clinical/filter/gate')]);
 const config=JSON.parse(await fs.readFile(path.join(dir,'config.json'),'utf8'));
 const baseline=JSON.parse(await fs.readFile(path.join(dir,'rule-results.json'),'utf8'));
 for(const [file,hash] of Object.entries(baseline.source_hashes)) {
  const actual=createHash('sha256').update(await fs.readFile(path.join(root,file))).digest('hex');
  if(actual!==hash) throw Error('Source drift: '+file);
 }
 const requests=[]; const results=[];
 const saved=mode==='replay'?JSON.parse(await fs.readFile(path.join(dir,'stage-a-responses.json'),'utf8')):{};
 const pack=await loadPsychiatryPack(root);
 for(const topic of baseline.topics) {
  const watch=config.topics.find(t=>t.id===topic.id).watch;
  const provider={id:'openai',jsonSchemaTarget:'draft-07',complete:async(model,req)=>{
   req=structuredClone(req);
   req.messages[0].content += '\nQuote extraction requirement: Return ONE short, exact, contiguous excerpt of 8-160 characters copied from the provided title or abstract. Do not paraphrase, concatenate separate passages, insert ellipses, or add words. Choose a passage supporting the relevance judgement; a treatment-result summary is not required.';
   const id=createHash('sha256').update(JSON.stringify({model,req})).digest('hex');
   if(mode==='capture'){requests.push({id,topic:topic.id,model,req});throw Error('Offline capture only');}
   const r=saved[id]; if(!r)throw Error('No frozen response; paid retries disabled');
   return {text:r.choices[0].message.content,usage:{inputTokens:r.usage.prompt_tokens,outputTokens:r.usage.completion_tokens},model,provider:'openai',stopReason:'stop'};
  }};
  try {
   const run=await gradeStageA(topic.candidates,[watch],[],{storage:new MemoryVaultStorage(),settings:{...DEFAULT_SETTINGS,tierModels:{fast:{provider:'openai',model:config.model},strong:{provider:'openai',model:config.model}},dailyBudgetUsd:10},providerOverride:{fast:provider}});
   results.push({topic:topic.id,failedBatches:run.failedBatches,records:topic.candidates.map(candidate=>{
    const grade=run.grades.get(candidate.key); const verified=verifyMatchedParts(grade,candidate,[watch],pack);
    const modelDesignDropped=Boolean(verified.modelDesign && candidate.designSource !== 'publication-type' && !designAccepted(config.strictness,verified.modelDesign));
    return {pmid:candidate.key,grade,verified,layer:layerOf({grade:verified},[watch]),modelDesignDropped,design:candidate.design};
   })});
  }catch(e){if(mode!=='capture')throw e;}
 }
 if(mode==='capture') {if(!requests.length)throw Error('No requests captured');await fs.writeFile(path.join(dir,'stage-a-requests.json'),JSON.stringify(requests,null,2));console.log({captured:requests.length});}
 else {await fs.writeFile(path.join(dir,'stage-a-results.json'),JSON.stringify(results,null,2));console.log(results.map(t=>({topic:t.topic,failedBatches:t.failedBatches,graded:t.records.length,eligible:t.records.filter(r=>r.layer!==null).length,ungraded:t.records.filter(r=>r.grade.ungraded).length})));}
}finally{await server.close();}
