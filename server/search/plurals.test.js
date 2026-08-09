// Plural folding: the shape rules, and the vocabulary guard that makes them
// safe. Every assertion here is a word from this corpus.
const assert = require("node:assert/strict");
const { singularOf, buildPluralMap, foldTokens, pluralMapFromDocs, KEEP } = require("./plurals");

// ── shape ───────────────────────────────────────────────────────────────────
for (const [plural, singular] of [
  ["graphs", "graph"], ["trees", "tree"], ["nodes", "node"], ["edges", "edge"],
  ["queries", "query"], ["arrays", "array"],
  ["matches", "match"], ["boxes", "box"], ["prefixes", "prefix"],
  ["vertices", "vertex"], ["indices", "index"], ["matrices", "matrix"], ["children", "child"],
]) {
  assert.equal(singularOf(plural), singular, `${plural} -> ${singular}`);
}

// Words that end in s and are not plurals. A stemmer without this list turns
// `series` into `sery` and `basis` into `basi`, and the query stops matching
// anything at all — a silent recall bug with no visible cause.
for (const word of ["series", "basis", "analysis", "status", "class", "process", "always", "cross"]) {
  assert.equal(singularOf(word), null, `${word} is not a plural`);
}
assert.ok(KEEP.has("series"));

// Short tokens are left alone, which is what protects the names: bfs, dfs,
// dsu, sos, mos are all three letters and all end in s.
for (const acronym of ["bfs", "dfs", "dsu", "sos", "mos", "abs"]) {
  assert.equal(singularOf(acronym), null, `${acronym} survives`);
}
assert.equal(singularOf(""), null);
assert.equal(singularOf(null), null);
assert.equal(singularOf("graph"), null, "a singular has nothing to fold to");

// ── the vocabulary guard ────────────────────────────────────────────────────
// The rule is not "strip an s", it is "merge two words this corpus has".
{
  const df = new Map([["graph", 546], ["tree", 367], ["series", 12], ["kruskals", 3], ["bits", 40]]);
  const map = buildPluralMap(new Map([...df, ["graphs", 18], ["trees", 35]]));
  assert.equal(map.get("graphs"), "graph");
  assert.equal(map.get("trees"), "tree");
  assert.equal(map.has("series"), false, "no `sery` in the corpus, so no fold");
  assert.equal(map.has("kruskals"), false, "no `kruskal` in the corpus either");
  assert.equal(map.has("bits"), false, "and no `bit`");
  // Add the singular and the same word now folds. This is the whole design.
  const richer = buildPluralMap(new Map([...df, ["bits", 40], ["bit", 90]]));
  assert.equal(richer.get("bits"), "bit");
}

// ── folding is symmetric, which is the property the bug report was about ────
{
  const map = pluralMapFromDocs([
    ["graph", "cycle", "shortest", "path"],
    ["graph", "traversal", "bfs"],
    ["graphs", "and", "trees"],
    ["tree", "diameter"],
  ]);
  const q = (s) => foldTokens(s.split(" "), map).join(" ");
  assert.equal(q("graphs"), "graph", "the plural query becomes the singular");
  assert.equal(q("graph"), "graph", "and the singular is untouched");
  assert.equal(q("graphs and graph"), "graph and graph", "both spellings meet");
  assert.equal(q("trees"), "tree");
  assert.equal(q("bfs"), "bfs", "an acronym is not a plural");
}

// ── a map that isn't there changes nothing ──────────────────────────────────
{
  const tokens = ["graphs", "trees"];
  assert.deepEqual(foldTokens(tokens, new Map()), tokens, "BENCH_STEM=0 is a real off switch");
  assert.deepEqual(foldTokens(tokens, null), tokens);
}

console.log("plural folding tests passed");
