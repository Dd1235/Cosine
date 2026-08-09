// "graph" and "graphs" gave very different results — measured directly.
//
// The 71-query benchmark could not see this bug, because every query in it
// happened to use the same grammatical number as the corpus does. And it can't
// be measured with relevance judgements either: nobody is going to label the
// 546 problems that match "graph".
//
// So this measures AGREEMENT instead. Asking the same question in the other
// number should return the same problems, whatever those problems are — the
// singular's own results are the reference, and no new judgement is needed.
//
//   node bench/plural_agreement.js              # as served
//   BENCH_STEM=0 node bench/plural_agreement.js # before the fold existed
const fs = require("fs");
const path = require("path");
const { Bm25Index } = require("../server/search/bm25");

const ROOT = path.join(__dirname, "..");
const problems = [];
for (const judge of ["leetcode", "codeforces", "cses", "atcoder"]) {
  const dir = path.join(ROOT, "data", "problemset_llm", judge);
  for (const file of fs.readdirSync(dir)) {
    problems.push(JSON.parse(fs.readFileSync(path.join(dir, file), "utf8")));
  }
}

// Nouns this corpus is actually made of, plus three multi-word queries — the
// single words are where the cliff was, the phrases are what people type.
const PAIRS = [
  ["graph", "graphs"], ["tree", "trees"], ["query", "queries"], ["string", "strings"],
  ["interval", "intervals"], ["subarray", "subarrays"], ["node", "nodes"], ["edge", "edges"],
  ["vertex", "vertices"], ["index", "indices"], ["matrix", "matrices"], ["prefix", "prefixes"],
  ["cycle", "cycles"], ["palindrome", "palindromes"], ["permutation", "permutations"],
  ["segment tree range query", "segment trees range queries"],
  ["shortest path graph", "shortest paths graphs"],
  ["binary tree traversal", "binary trees traversals"],
];

const index = new Bm25Index(problems);
const ids = (q, k) => index.search(q, k).hits.map((h) => h.problem.id);
const total = (q) => index.search(q, 1).total;
const overlap = (a, b) => {
  const set = new Set(b);
  return a.length ? a.filter((x) => set.has(x)).length / a.length : 1;
};

let sumTop10 = 0;
let sumCounts = 0;
const rows = [];
for (const [singular, plural] of PAIRS) {
  const [a, b] = [ids(singular, 10), ids(plural, 10)];
  const [ta, tb] = [total(singular), total(plural)];
  const agree = overlap(a, b);
  sumTop10 += agree;
  sumCounts += Math.min(ta, tb) / Math.max(1, Math.max(ta, tb));
  rows.push({ pair: `${singular} / ${plural}`, agree, ta, tb });
}

console.log(`plural agreement · ${problems.length} problems · folding ${process.env.BENCH_STEM === "0" ? "OFF" : "on"}\n`);
console.log(`${"query pair".padEnd(46)}${"top-10 same".padStart(12)}${"results".padStart(16)}`);
for (const r of rows) {
  console.log(`${r.pair.padEnd(46)}${`${(100 * r.agree).toFixed(0)}%`.padStart(12)}${`${r.ta} vs ${r.tb}`.padStart(16)}`);
}
const top10 = (100 * sumTop10) / PAIRS.length;
const counts = (100 * sumCounts) / PAIRS.length;
console.log(`\nmean top-10 agreement ${top10.toFixed(1)}%   ·   mean result-count ratio ${counts.toFixed(1)}%`);

// A guard, not just a report: if this drops back, the bug is back.
if (process.env.BENCH_STEM !== "0" && top10 < 95) {
  console.error(`\nFAIL: expected near-total agreement with folding on, got ${top10.toFixed(1)}%`);
  process.exit(1);
}
