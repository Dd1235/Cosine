// The CSES bands are estimates, so the card has to say so and say how sure it
// is. That claim is only as good as the record behind it: a band with no stored
// confidence must read as "unknown", not as "high", and nothing outside CSES
// may ever claim one. Pure functions, so a plain test rather than a DOM
// harness.
const assert = require("node:assert/strict");
const difficulty = require("./difficulty");

const published = {
  platform: "cses",
  cses_difficulty: {
    band: 4,
    confidence: "medium",
    method: "cses-reviewed-v1",
    evidence: ["https://cses.fi/problemset/task/1148"],
    reviewed_at: "2026-09-11",
  },
};

// format() is asserted against the Sheets formatter in practice.test.js; this
// pins it here too, because the new functions must not have changed its words.
assert.equal(difficulty.format(published), "Advanced · CSES estimate");

assert.equal(difficulty.confidence(published), "medium");

// A specialist check resolved this one, and the card is allowed to say so.
const overridden = {
  platform: "cses",
  cses_difficulty: {
    ...published.cses_difficulty,
    band: 5,
    confidence: "low",
    override: { original_band: 4, reason: "Completed specialist solution and proof review" },
  },
};
assert.equal(difficulty.confidence(overridden), "low");
assert.equal(difficulty.format(overridden), "Expert · CSES estimate");

// Nothing but a published CSES estimate carries a confidence.
for (const problem of [
  { platform: "codeforces", difficulty: 1900 },
  { platform: "leetcode", difficulty: "Hard" },
  { platform: "cses" },
  { platform: "cses", cses_difficulty: null },
  { platform: "cses", cses_difficulty: { band: 6, confidence: "high" } },
  { platform: "cses", cses_difficulty: { band: "4", confidence: "high" } },
]) {
  assert.equal(difficulty.confidence(problem), null, `confidence on ${JSON.stringify(problem)}`);
}

// A record written before confidence was stored is honest about it: the band
// still shows, the agreement claim does not.
const unlabelled = { platform: "cses", cses_difficulty: { band: 2, method: "cses-reviewed-v1" } };
assert.equal(difficulty.confidence(unlabelled), null);
assert.equal(difficulty.format(unlabelled), "Standard · CSES estimate", "the band still shows");
assert.equal(difficulty.confidence({ platform: "cses", cses_difficulty: { band: 2, confidence: "certain" } }), null);

// One source of wording for the card tooltip and the manual.
for (const level of ["high", "medium", "low"]) {
  assert.match(difficulty.confidenceTitle(level), new RegExp(`^${level} confidence: `));
}
assert.match(difficulty.confidenceTitle("high"), /both/);
assert.match(difficulty.confidenceTitle("medium"), /one band apart/);
assert.match(difficulty.confidenceTitle("low"), /specialist/);
assert.equal(difficulty.confidenceTitle(null), "");
assert.equal(difficulty.confidenceTitle("unknown"), "");

console.log("difficulty tests passed (confidence and tooltip wording)");
