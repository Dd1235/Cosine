// The line between "a word this corpus doesn't use" and "someone leaned on
// the keyboard".
//
// It exists because the meaning ranker is allowed to answer the first and must
// refuse the second, and because the obvious signal — the cosine score — was
// measured and cannot tell them apart: on the live index `xkcdqq` scores 0.565
// and `rat` scores 0.296.
const assert = require("node:assert/strict");
const { isWordLike, queryIsWordLike } = require("./wordlike");

// ── words the corpus happens not to use ─────────────────────────────────────
// These are the point. `rat` returns Cat and Mouse, Save More Mice and Mice
// and Cheese from the dense index; it was never being asked.
for (const w of [
  "rat", "mouse", "cheese", "maze", "robot", "chess", "pizza", "train",
  "garden", "rhythm", "queue", "sieve", "palindrome", "knapsack", "xor",
]) {
  assert.equal(isWordLike(w), true, `${w} is a word`);
}

// ── keyboard ────────────────────────────────────────────────────────────────
for (const junk of ["asdkjhqwe", "qqqqq", "zzzz", "xkcdqq", "lkjhgfdsa", "zxcvbn", "hjkl", "ffff"]) {
  assert.equal(isWordLike(junk), false, `${junk} is a mash`);
}

// ── the three rules, one at a time ──────────────────────────────────────────
assert.equal(isWordLike("bcdfg"), false, "no vowel");
assert.equal(isWordLike("aaa"), false, "a tripled letter");
assert.equal(isWordLike("astrngths"), false, "five consonants in a row");
assert.equal(isWordLike("a"), false, "one character is not a word");
assert.equal(isWordLike(""), false);
assert.equal(isWordLike(null), false);
assert.equal(isWordLike("RAT"), true, "case doesn't matter");

// ── whole queries ───────────────────────────────────────────────────────────
{
  assert.equal(queryIsWordLike(["rat"]), true);
  assert.equal(queryIsWordLike(["cat", "mouse"]), true);
  // One mash spoils it: otherwise `graph asdkjhqwe` gets through on the
  // strength of a word the corpus doesn't have either.
  assert.equal(queryIsWordLike(["graph", "asdkjhqwe"]), false);
  assert.equal(queryIsWordLike([]), false, "an empty query is not a question");
  assert.equal(queryIsWordLike(null), false);
}

// ── the honest limit ────────────────────────────────────────────────────────
// A name is shaped exactly like a word, and no rule without a dictionary will
// say otherwise. `deepya` gets nearest-by-meaning results and a status line
// saying nothing matched, instead of the clean zero it used to get. Asserted
// so the tradeoff is visible in the tests rather than only in the README.
assert.equal(isWordLike("deepya"), true, "a name passes — this is the known cost");
assert.equal(isWordLike("kumar"), true);

console.log("wordlike tests passed");
