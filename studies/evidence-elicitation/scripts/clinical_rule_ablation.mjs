// Offline execution of production parsing and rule gates; never performs live retrieval.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { createServer } from '../../../scispark-wiki-psychiatry/node_modules/vite/dist/node/index.js';
const study = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.resolve(study, '../../scispark-wiki-psychiatry');
const dir = path.join(study, 'runs/clinical-v1');
const server = await createServer({ root, configFile: false, server: { middlewareMode: true, hmr: false, ws: false }, resolve: { alias: { '@': path.join(root, 'src') } } });
try {
  const load = p => server.ssrLoadModule('/src/lib/' + p + '.ts');
  const [{ searchPubmed }, { loadPsychiatryPack }, { cleanTitle, cleanAbstract, qualityFlags }, { domainFilter }, { designGate }] = await Promise.all([
    load('papers/pubmed'), load('clinical/pack/load'), load('clinical/text/clean'), load('clinical/filter/prefilter'), load('clinical/filter/gate'),
  ]);
  const config = JSON.parse(await fs.readFile(path.join(dir, 'config.json'), 'utf8'));
  const xml = await fs.readFile(path.join(dir, 'pubmed.xml'), 'utf8');
  const ids = config.topics.flatMap(t => t.records.map(r => r.pmid));
  const papers = await searchPubmed({ query: 'offline fixture', limit: ids.length }, { fetchFn: async url => {
    if (String(url).includes('esearch.fcgi')) return Response.json({ esearchresult: { idlist: ids } });
    if (String(url).includes('efetch.fcgi')) return new Response(xml);
    throw new Error('Unexpected transport request');
  }});
  const byId = new Map(papers.map(p => [p.ids.pmid, p]));
  if (byId.size !== ids.length || ids.some(id => !byId.has(id))) throw new Error('Metadata coverage mismatch');
  const pack = await loadPsychiatryPack(root);
  const allMesh = JSON.parse(await fs.readFile(path.join(dir, 'all-mesh.json'), 'utf8'));
  const baseline = JSON.parse(await fs.readFile(path.join(dir, 'rule-results.json'), 'utf8'));
  const variants = [];
  for (const variant of ['baseline', 'all-mesh', 'condition-terms', 'both']) {
  const extended = variant === 'condition-terms' || variant === 'both';
  const activePack = extended ? { ...pack, textWords: [...new Set([...pack.textWords, ...pack.taxonomy.nodes.filter(n => n.type === 'condition').flatMap(n => [n.name, ...n.synonyms])])] } : pack;
  const topics = config.topics.map(topic => {
    const candidates = topic.records.map(({ pmid }) => {
      const original = byId.get(pmid);
      const raw = variant === 'all-mesh' || variant === 'both' ? { ...original, fields: allMesh[pmid] } : original;
      const paper = { ...raw, title: cleanTitle(raw.title) ?? '', abstract: cleanAbstract(raw.abstract) };
      return { paper, key: pmid, provenance: [{ query: 'offline reference pool', tier: 'entry', entryId: topic.id }], flags: qualityFlags(paper) };
    });
    const domain = domainFilter(activePack, candidates);
    const gate = designGate(activePack, [topic.watch], domain.kept, config.strictness);
    const domainIds = new Set(domain.kept.map(c => c.key));
    const gateIds = new Set(gate.gated.map(c => c.key));
    return { id: topic.id, records: topic.records.map(r => ({ ...r, title: byId.get(r.pmid).title, domain_kept: domainIds.has(r.pmid), design_kept: gateIds.has(r.pmid), drop: [...domain.drops, ...gate.drops].find(d => d.key === r.pmid) ?? null })), candidates: gate.gated };
  });
  if (variant === 'baseline') {
    for (let i = 0; i < topics.length; i++) {
      if (JSON.stringify(topics[i].records) !== JSON.stringify(baseline.topics[i].records)) throw new Error('Baseline drift: stop comparison');
    }
  }
  variants.push({ variant, topics });
  }
  const hashes = {};
  for (const sub of ['src/lib/clinical', 'src/lib/papers', 'packs/psychiatry']) {
    const walk = async dir => { for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) await walk(p);
      else if (/\.(ts|json)$/.test(p)) hashes[path.relative(root, p)] = createHash('sha256').update(await fs.readFile(p)).digest('hex');
    }};
    await walk(path.join(root, sub));
  }
  const output = { scope: 'Offline production parser, cleaner, domain filter and standard design gate only. No LLM or retrieval measurement.', created_at: new Date().toISOString(), source_hashes: hashes, variants };
  await fs.writeFile(path.join(dir, 'rule-ablation.json'), JSON.stringify(output, null, 2) + '\n');
  for (const v of variants) for (const t of v.topics) console.log(JSON.stringify({variant: v.variant, topic: t.id, abstract_positive_kept: t.records.filter(r => r.abstract_label === 1 && r.design_kept).length, content_positive_kept: t.records.filter(r => r.content_label === 1 && r.design_kept).length, controls_kept: t.records.filter(r => r.abstract_label === 0 && r.design_kept).length}));
} finally { await server.close(); }
