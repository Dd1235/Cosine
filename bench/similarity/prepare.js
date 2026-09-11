// Frozen, deterministic candidate pooling. No judgments are inferred from labels.
// node bench/similarity/prepare.js <output-directory>
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { loadProblems } = require('../../server/data');
const { loadArtifact, corpusHash, matchesEmbeddingRecipe } = require('../../server/search/embedding');
const { DenseIndex } = require('../../server/search/dense');
const { SimilarIndex, techniques } = require('../../server/search/similar');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const problems = loadProblems();
const artifact = loadArtifact();
if (!artifact || artifact.manifest.corpusHash !== corpusHash(problems) || !matchesEmbeddingRecipe(artifact.manifest.recipe)) throw Error('Run npm run embed first');
if (problems.some((p, i) => artifact.manifest.ids[i] !== p.id)) throw Error('Artifact row order mismatch');
const dir = process.argv[2];
if (!dir) throw Error('Explicit output directory required (never overwrite a frozen study)');
if (fs.existsSync(dir)) throw Error('Output exists; choose a fresh directory');
const dense = new DenseIndex(problems, { matrix: artifact.matrix, embed: async () => { throw Error('offline only'); } });
const rankers = { dense, technique: new SimilarIndex(problems, dense, { techniqueWeight: 1 }), hybrid: new SimilarIndex(problems, dense, { techniqueWeight: 0.5 }) };
// Round-robin judges + difficulty + annotation density; family assignment is a
// provisional split that reviewers must confirm before frozen evaluation.
const buckets = new Map();
for (const p of problems) {
  const d = p.cses_difficulty?.band ?? p.difficulty;
  const difficulty = typeof d === 'number' ? (p.platform === 'cses' ? (d >= 4 ? 'hard' : 'lower') : d >= 2200 ? 'hard' : 'lower') : String(d || 'unknown');
  const density = techniques(p).size <= 2 ? 'sparse' : 'rich';
  const key = [p.platform, difficulty, density].join('/');
  if (!buckets.has(key)) buckets.set(key, []);
  buckets.get(key).push(p);
}
for (const bucket of buckets.values()) bucket.sort((a,b) => hash(a.id).localeCompare(hash(b.id)));
const seeds = [], seenFamilies = new Set();
const family = p => [...techniques(p)].sort((a,b) => (rankers.technique.idf.get(b)||0)-(rankers.technique.idf.get(a)||0) || a.localeCompare(b))[0] || 'unannotated';
while (seeds.length < 40) {
  let added = false;
  for (const key of [...buckets.keys()].sort()) {
    const bucket = buckets.get(key);
    while (bucket.length && seenFamilies.has(family(bucket[0]))) bucket.shift();
    if (!bucket.length) continue;
    const p = bucket.shift(), group = family(p);
    seeds.push({ problem: p, stratum: key, family: group, split: seeds.length % 2 ? 'test' : 'development' });
    seenFamilies.add(group); added = true;
    if (seeds.length === 40) break;
  }
  if (!added) throw Error('Insufficient distinct provisional technique families');
}
const records = [], packets = [], rankings = {};
for (const seed of seeds) {
  const id = seed.problem.id, pool = new Set();
  rankings[id] = {};
  for (const [name, ranker] of Object.entries(rankers)) {
    const hits = ranker.similar(id, problems.length).hits;
    rankings[id][name] = hits.map(h => h.problem.id);
    hits.slice(0, 10).forEach(h => pool.add(h.problem.id));
  }
  // Dense neighbors with no shared technique are candidate semantic distractors,
  // not automatically irrelevant. Reviewers decide their transfer relevance.
  const own = techniques(seed.problem);
  rankings[id].dense.filter(cid => ![...techniques(problems.find(p => p.id === cid))].some(t => own.has(t))).slice(0,3).forEach(cid => pool.add(cid));
  problems.filter(p => p.id !== id).sort((a,b) => hash(id+a.id).localeCompare(hash(id+b.id))).slice(0,3).forEach(p => pool.add(p.id));
  const candidates = [...pool].sort((a,b) => hash(id+a).localeCompare(hash(id+b)));
  records.push({ seed: id, split: seed.split, provisionalFamily: seed.family, stratum: seed.stratum, candidates });
  const redact = p => ({ id: p.id, title: p.title, statement: p.statement, source_url: p.source_url,
    evidenceStatus: 'Corpus statement; reviewer must obtain full statement, constraints and verified solution before grading.' });
  packets.push({ seed: redact(seed.problem), candidates: candidates.map(cid => redact(problems.find(p => p.id === cid))) });
}
fs.mkdirSync(dir, { recursive: true });
const write = (name, data) => fs.writeFileSync(path.join(dir, name), JSON.stringify(data,null,2)+'\n');
write('study.json', { version: 1, status: 'awaiting-independent-review', corpusHash: corpusHash(problems), recipe: artifact.manifest.recipe,
  seedCount: records.length, createdAt: new Date().toISOString(), familySplitVerified: false, records });
write('rankings.json', Object.fromEntries(Object.entries(rankings).map(([id, runs]) => [id, Object.fromEntries(Object.entries(runs).map(([name, ids]) => [name, ids.slice(0, 100)]))])));
write('blind-review-packets.json', packets);
write('judgments.json', { frozen: false, familySplitVerified: false, judgments: [] });
console.log(`Prepared ${records.length} seeds / ${packets.reduce((n,p)=>n+p.candidates.length,0)} pairs in ${dir}; all unjudged.`);
