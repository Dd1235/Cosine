// Plural folding for the lexical rankers.
//
// The bug this exists for: `graph` returned 546 problems and `graphs` returned
// 18 — and the 18 were mostly wrong, because a rare token carries a huge IDF,
// so any document that happened to contain the plural outranked every actual
// graph problem. Same for `tree` (367) against `trees` (35, led by *Cut Off
// Trees for Golf Event*). Typing the plural of a technique is not an unusual
// thing to do, and it fell off a cliff.
//
// This is **s-stemming, guarded by the corpus vocabulary** — not a full
// stemmer. The difference is the guard: a plural folds into its singular only
// when that singular is a word this corpus actually contains. So `graphs` →
// `graph` (546 documents have it) and `queries` → `query`, while `series`
// stays `series` (there is no `sery`), `bfs` stays `bfs` (no `bf`), and every
// word that merely ends in s is left alone.
//
// Why not Porter: it would also fold `sorting`→`sort`, `matrices`→`matric`,
// `series`→`seri` — rewriting tokens that were fine, in a vocabulary full of
// names (`kruskals`, `mos`, `sos`) where a wrong stem is a silent recall bug
// with no user-visible cause. Plurals were the reported problem, plurals are
// what this fixes, and the guard means every fold is defensible by pointing at
// two words that both exist.
//
// Documents and queries are folded with the SAME map, which is the only way
// the exact-title lookup keeps working: "minimum height trees" has to still
// equal the title it came from.

// Words this must never touch, whatever the vocabulary says. Each one is a
// word whose trailing s is part of it, and the shape rules below can't tell.
const KEEP = new Set([
  "less", "class", "pass", "process", "always", "status", "bonus", "axis",
  "basis", "analysis", "hypothesis", "this", "plus", "minus", "gauss", "cross",
  "chess", "guess", "access", "success", "address", "press", "mass", "loss",
  "os", "us", "is", "as", "its", "yes", "news", "series", "species", "means",
]);

// The irregulars that matter in a problem statement. Shape rules can't reach
// these — `vertices` shares no suffix with `vertex` — and they are exactly the
// words this corpus is made of: 74 problems say vertices, 112 say indices.
// Still vocabulary-guarded like everything else; if the singular isn't here,
// the fold doesn't happen.
const IRREGULAR = {
  vertices: "vertex",
  indices: "index",
  matrices: "matrix",
  leaves: "leaf",
  children: "child",
  maxima: "maximum",
  minima: "minimum",
};

const MIN_LENGTH = 4;   // "bfs", "dfs", "sos", "mos", "dsu" are all safe here

// The singular a token would fold to, by shape alone. Vocabulary decides
// whether it actually does.
function singularOf(token) {
  if (!token) return null;
  if (IRREGULAR[token]) return IRREGULAR[token];
  if (token.length < MIN_LENGTH || KEEP.has(token)) return null;
  if (/(ss|us|is)$/.test(token)) return null;          // class, radius, basis
  if (/[^aeiou]ies$/.test(token)) return `${token.slice(0, -3)}y`;  // queries -> query
  if (/(ch|sh|s|x|z)es$/.test(token)) return token.slice(0, -2);    // matches -> match
  if (/s$/.test(token)) return token.slice(0, -1);     // graphs -> graph
  return null;
}

// docFreq: Map<token, df> over the raw (unfolded) corpus vocabulary.
// Returns Map<plural, singular> for the folds that are safe here.
function buildPluralMap(docFreq) {
  const map = new Map();
  for (const token of docFreq.keys()) {
    const singular = singularOf(token);
    // The guard, and the whole design: fold only into a word this corpus has.
    // Without it, `series` becomes `sery` and stops matching anything.
    if (singular && docFreq.has(singular)) map.set(token, singular);
  }
  return map;
}

function foldTokens(tokens, map) {
  if (!map || !map.size) return tokens;
  return tokens.map((t) => map.get(t) || t);
}

// Convenience for an index: count raw document frequency, then build the map.
function pluralMapFromDocs(docTokenLists) {
  const df = new Map();
  for (const tokens of docTokenLists) {
    for (const t of new Set(tokens)) df.set(t, (df.get(t) || 0) + 1);
  }
  return buildPluralMap(df);
}

// Off is a supported state: BENCH_STEM=0 measures the rankers without it.
const ENABLED = process.env.BENCH_STEM !== "0";

module.exports = { singularOf, buildPluralMap, foldTokens, pluralMapFromDocs, ENABLED, KEEP, IRREGULAR };
