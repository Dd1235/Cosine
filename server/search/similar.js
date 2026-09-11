const taxonomy = require('../../data/pattern_taxonomy.json');

// Solution-oriented baseline. Family labels stay indexed for search but must
// not count as independent evidence beside their specific child here.
function techniques(problem) {
  const labels = new Set((problem.patterns || []).map(l => taxonomy.aliases[l] || l));
  for (const rule of taxonomy.families || []) {
    const re = new RegExp(rule.match);
    if ([...labels].some(l => l !== rule.family && re.test(l))) labels.delete(rule.family);
  }
  return labels;
}
class SimilarIndex {
  constructor(problems, dense, { techniqueWeight = 0 } = {}) {
    this.problems = problems; this.dense = dense;
    // Dense remains the production default until independent evaluation gates
    // approve a different weight. Structural fallback works without ONNX.
    this.weight = techniqueWeight;
    this.labels = new Map(problems.map(p => [p.id, techniques(p)]));
    const df = new Map();
    for (const labels of this.labels.values()) for (const l of labels) df.set(l, (df.get(l) || 0) + 1);
    this.idf = new Map([...df].map(([l,n]) => [l, Math.min(4, 1 + Math.log((problems.length+1)/(n+1)))]));
    this.labelWeight = new Map([...this.labels].map(([id, labels]) =>
      [id, [...labels].reduce((sum,l) => sum + this.idf.get(l), 0)]));
  }
  similar(id) {
    const source = this.problems.find(p => p.id === id);
    if (!source) return null;
    const a = this.labels.get(id);
    const denseResult = this.dense?.similar(id, this.problems.length);
    const scores = new Map((denseResult?.hits || []).map(h => [h.problem.id, h.score]));
    const weight = denseResult ? this.weight : 1;
    const candidates = denseResult && weight === 0 ? denseResult.hits.map(h => h.problem) : this.problems.filter(p => p.id !== id);
    const hits = candidates.map(problem => {
      const b = this.labels.get(problem.id);
      const shared = [...a].filter(l => b.has(l));
      const intersectionWeight = shared.reduce((v,l) => v + this.idf.get(l), 0);
      const unionWeight = this.labelWeight.get(id) + this.labelWeight.get(problem.id) - intersectionWeight;
      const overlap = unionWeight ? intersectionWeight/unionWeight : 0;
      return { problem, score: weight*overlap + (1-weight)*(scores.get(problem.id) || 0),
        matchedTerms: [], sharedTechniques: shared, techniqueScore: overlap };
    }).filter(h => denseResult || h.techniqueScore > 0);
    if (!(denseResult && weight === 0)) hits.sort((a,b) => b.score-a.score || a.problem.id.localeCompare(b.problem.id));
    return { source: {id: source.id, title: source.title}, hits,
      ranker: weight === 0 ? 'dense' : weight === 1 ? 'technique' : 'solution-hybrid' };
  }
}
module.exports = { SimilarIndex, techniques };
