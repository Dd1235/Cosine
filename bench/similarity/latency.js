// Warm, non-personalized scoring latency. HTTP/DB/browser latency is separate.
const os = require('os');
const { loadProblems } = require('../../server/data');
const { loadArtifact, corpusHash, matchesEmbeddingRecipe } = require('../../server/search/embedding');
const { DenseIndex } = require('../../server/search/dense');
const { SimilarIndex } = require('../../server/search/similar');
const problems = loadProblems(), artifact = loadArtifact();
if (!artifact || artifact.manifest.corpusHash !== corpusHash(problems) || !matchesEmbeddingRecipe(artifact.manifest.recipe)) throw Error('Matching reproducible artifact required');
const dense = new DenseIndex(problems, { matrix: artifact.matrix });
const variants = {
  dense: new SimilarIndex(problems, dense),
  technique: new SimilarIndex(problems, null),
  hybrid: new SimilarIndex(problems, dense, { techniqueWeight: .5 }),
};
const latency = {};
for (const [name, index] of Object.entries(variants)) {
  const samples = [];
  for (let i=0;i<220;i++) {
    const start = performance.now();
    index.similar(problems[(i*71)%problems.length].id);
    if (i>=20) samples.push(performance.now()-start);
  }
  samples.sort((a,b)=>a-b);
  latency[name] = { repetitions:samples.length, medianMs:samples[100], p95Ms:samples[190] };
}
console.log(JSON.stringify({observedAt:new Date().toISOString(),node:process.version,os:os.type(),release:os.release(),arch:os.arch(),cpu:os.cpus()[0].model,corpusHash:corpusHash(problems),count:problems.length,scope:'warm scoring only; excludes HTTP and personalized DB reads',latency},null,2));
