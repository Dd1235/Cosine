// node bench/similarity/evaluate.js <study-directory>
// Incomplete pools are reported as unjudged and cannot promote a ranker.
const fs = require('fs');
const path = require('path');
function metrics(ids, grades, k = 10) {
  const top = ids.slice(0,k);
  if (top.some(id => !grades.has(id))) return null;
  const dcg = values => values.reduce((s,g,i) => s+(2**g-1)/Math.log2(i+2),0);
  const ideal = [...grades.values()].sort((a,b)=>b-a).slice(0,k);
  const denom = dcg(ideal);
  return { ndcg: denom ? dcg(top.map(id=>grades.get(id)))/denom : 0,
    precision: ids.slice(0,5).filter(id=>grades.get(id)>=2).length/5 };
}
function pairedInterval(deltas) {
  if (!deltas.length) return null;
  let seed = 1729;
  const random = () => ((seed = (1664525*seed+1013904223)>>>0)/4294967296);
  const samples = Array.from({length:2000}, () => deltas.reduce(sum=>sum+deltas[Math.floor(random()*deltas.length)],0)/deltas.length).sort((a,b)=>a-b);
  return [samples[50],samples[1949]];
}
function evaluate(study, rankings, judgments) {
  const rows = [], missing = [];
  for (const record of study.records) {
    const grades = new Map();
    for (const j of judgments.judgments.filter(j=>j.seed===record.seed)) {
      if (!record.candidates.includes(j.candidate)) throw Error('Judgment outside candidate pool');
      if (grades.has(j.candidate)) throw Error('Duplicate adjudicated judgment');
      if (!Number.isInteger(j.grade)||j.grade<0||j.grade>3) throw Error('grade must be integer 0..3');
      if (!j.evidence?.length || !j.reviewers || new Set(j.reviewers).size < 2) throw Error('Each judgment needs solution evidence and two independent reviewers');
      grades.set(j.candidate,j.grade);
    }
    const unjudged = record.candidates.filter(id=>!grades.has(id));
    if (unjudged.length) missing.push({ seed:record.seed, count:unjudged.length });
    for (const [ranker,ids] of Object.entries(rankings[record.seed])) {
      rows.push({ seed:record.seed, split:record.split, stratum:record.stratum, ranker, metrics:metrics(ids,grades) });
    }
  }
  const summaries = {};
  for (const ranker of [...new Set(rows.map(r=>r.ranker))]) {
    const matched = rows.filter(r=>r.ranker===ranker&&r.split==='test'&&r.metrics);
    const pairs = matched.map(r=>({next:r,base:rows.find(b=>b.seed===r.seed&&b.ranker==='dense')})).filter(p=>p.base?.metrics);
    const ndcg = pairs.map(p=>p.next.metrics.ndcg-p.base.metrics.ndcg);
    const precision = pairs.map(p=>p.next.metrics.precision-p.base.metrics.precision);
    const mean = xs=>xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:null;
    summaries[ranker] = { judgedTestSeeds:matched.length, pairedSeeds:pairs.length,
      ndcg:mean(matched.map(r=>r.metrics.ndcg)), precision:mean(matched.map(r=>r.metrics.precision)),
      deltaNdcg:mean(ndcg), deltaPrecision:mean(precision), ndcg95:pairedInterval(ndcg), precision95:pairedInterval(precision),
      slices: Object.fromEntries(['hard','sparse'].map(slice=>[slice, matched.filter(r=>r.stratum.split('/').includes(slice)).map(r=>({seed:r.seed,...r.metrics}))])) };
  }
  const ready = judgments.frozen === true && judgments.familySplitVerified === true && missing.length === 0;
  return { status:ready?'reviewed-needs-latency-and-slice-gates':'incomplete-do-not-promote', missing,
    note:'Unjudged candidates are not zero relevance. Reported nDCG ideal is over the independently judged candidate pool. Compare development separately before freezing.', summaries, rows };
}
module.exports = { metrics, pairedInterval, evaluate };
if (require.main === module) {
  const dir = process.argv[2];
  if (!dir) throw Error('Study directory required');
  const read = name=>JSON.parse(fs.readFileSync(path.join(dir,name),'utf8'));
  console.log(JSON.stringify(evaluate(read('study.json'),read('rankings.json'),read('judgments.json')),null,2));
}
