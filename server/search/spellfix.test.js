// Spelling correction. The interesting assertions are the NEGATIVE ones: this
// runs in front of the nonsense guard, so anything it over-corrects turns a
// deliberate "no problem mentions that" into a page of wrong results.
const assert = require("node:assert/strict");
const { correctTerms, editDistance } = require("./spellfix");

// A vocabulary shaped like the real one: real terms with plausible frequencies.
const vocab = new Map([
  ["dijkstra", 35], ["kruskal", 14], ["tree", 900], ["pre", 12], ["lifting", 20],
  ["decomposition", 25], ["fenwick", 30], ["segment", 180], ["deep", 40],
  ["dsu", 8], ["lca", 9], ["mex", 6], ["sum", 800], ["binary", 400],
  // The short words the corrector used to reach for. Frequencies are the real
  // ones from the served corpus, because the rules turn on them.
  ["sat", 15], ["bit", 285], ["set", 246], ["cost", 146], ["max", 82],
  ["gray", 3], ["rate", 4], ["stack", 99], ["heap", 101], ["array", 1562],
]);
const fix = (terms) => correctTerms(terms, vocab).map((c) => `${c.from}->${c.to}`);

// ── Distance ────────────────────────────────────────────────────────────────
{
  assert.equal(editDistance("djikstra", "dijkstra", 2), 1, "a transposition is one edit");
  assert.equal(editDistance("kruskals", "kruskal", 2), 1);
  assert.equal(editDistance("abc", "xyz", 2), 3, "beyond the cutoff returns cutoff+1");
  assert.equal(editDistance("same", "same", 2), 0);
}

// ── Corrects what is genuinely a typo ───────────────────────────────────────
{
  assert.deepEqual(fix(["djikstra"]), ["djikstra->dijkstra"]);
  assert.deepEqual(fix(["kruskals"]), ["kruskals->kruskal"]);
  assert.deepEqual(fix(["lifitng"]), ["lifitng->lifting"]);
  assert.deepEqual(fix(["decompostion"]), ["decompostion->decomposition"]);
}

// ── Never touches a term the corpus already has ─────────────────────────────
{
  for (const t of ["dijkstra", "tree", "dsu", "lca", "mex", "sum"]) {
    assert.deepEqual(fix([t]), [], `${t} is a real term and must be left alone`);
  }
}

// ── The regression that matters: nonsense stays nonsense ────────────────────
{
  // "deepya" is two deletions from "deep". Allowing 2 edits at length 6 would
  // correct a person's name into a result page — the exact failure an earlier
  // round fixed by adding the vocabulary guard.
  assert.deepEqual(fix(["deepya"]), [], "a name must not be corrected into a real term");
  assert.deepEqual(fix(["qqqqq"]), []);
  assert.deepEqual(fix(["rahul", "kumar"]), []);
  assert.deepEqual(fix(["asdkjhqwe", "zzzz"]), []);
}

// ── Never aims at the corpus's long tail ────────────────────────────────────
{
  // "muh" (df 2) is one edit from "much". Correcting toward a term used twice
  // is a coincidence, not a correction, and it cost real nDCG on a paraphrase
  // query before MIN_TARGET_DF existed.
  const withTail = new Map([...vocab, ["muh", 2]]);
  assert.deepEqual(correctTerms(["much"], withTail), [], "a df-2 term is not a correction target");
  assert.deepEqual(correctTerms(["muh"], withTail), [], "...and is itself left alone, being known");
}

// ── Short words: the reported bug ───────────────────────────────────────────
//
// `rat` returned problems about `sat`. At three characters one edit is a third
// of the word and this vocabulary always has a neighbour, so distance alone is
// no evidence at all. Each of these used to correct, and each was wrong.
{
  assert.deepEqual(fix(["rat"]), [], "rat is not sat — the first letter has to match");
  assert.deepEqual(fix(["bat"]), [], "bat is not bit — a substitution, not a truncation");
  assert.deepEqual(fix(["seg"]), [], "seg is not set");
  assert.deepEqual(fix(["cot"]), [], "cot is not cost");
  assert.deepEqual(fix(["mox"]), [], "mox is not max");
  // …while the truncation this length was allowed for still works.
  assert.deepEqual(fix(["tre"]), ["tre->tree"], "you typed the start of a longer word");
}

// ── The first character carries the query ───────────────────────────────────
// A typo lands almost anywhere except the first letter, so requiring it costs
// nothing real and removes a whole class of wrong answers.
{
  assert.deepEqual(fix(["sinary"]), [], "binary is one edit away but starts elsewhere");
  assert.deepEqual(fix(["binry"]), ["binry->binary"], "the same typo, first letter intact");
}

// ── A short target needs the corpus behind it ───────────────────────────────
{
  // `graf` used to reach `gray` — a word three problems contain — instead of
  // failing honestly. `graph` is two edits away and out of budget at length 4.
  assert.deepEqual(fix(["graf"]), [], "a four-letter target with df 3 is a coincidence");
  const popular = new Map([...vocab, ["gray", 40]]);
  assert.deepEqual(correctTerms(["graf"], popular).map((c) => c.to), ["gray"],
    "...and the same word, used forty times, is a destination");
}

// ── Four letters still correct, which is why the cutoff isn't length ────────
// Dropping every word under five characters would have been simpler and would
// have taken these three with it.
{
  assert.deepEqual(fix(["stak"]), ["stak->stack"]);
  assert.deepEqual(fix(["hepa"]), ["hepa->heap"]);
  assert.deepEqual(fix(["arry"]), ["arry->array"]);
}

// ── Ties break on corpus frequency, not the alphabet ────────────────────────
{
  // "tre" sits one edit from both "tree" (df 900) and "pre" (df 12).
  // Alphabetical order picks "pre", which is why frequency is consulted.
  assert.deepEqual(fix(["tre"]), ["tre->tree"]);
}

// ── Bounded ─────────────────────────────────────────────────────────────────
{
  assert.ok(fix(["djikstra", "kruskals", "lifitng", "decompostion"]).length <= 2,
    "at most two corrections per query");
  assert.deepEqual(correctTerms(["djikstra"], new Map()), [], "an empty vocabulary corrects nothing");
  assert.deepEqual(correctTerms(["djikstra"], null), []);
}

console.log("spellfix tests passed");
