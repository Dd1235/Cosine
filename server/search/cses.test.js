const assert = require("node:assert/strict");
const { parseSelection, passesDifficulty, sortByDifficulty, buildDifficultyPayload, SORTABLE_JUDGES } = require("./difficulty");
const { suggestLevel } = require("./level");
const problems = [
  { id: "unknown", platform: "cses" },
  { id: "expert", platform: "cses", cses_difficulty: { band: 5 } },
  { id: "standard", platform: "cses", cses_difficulty: { band: 2 } },
  { id: "foundation", platform: "cses", cses_difficulty: { band: 1 } },
];
const selection = parseSelection("cses-standard,cses-expert,cf:1400-1600");
assert.deepEqual(problems.filter((p) => passesDifficulty(p, selection)).map((p) => p.id), ["expert", "standard"]);
assert.equal(passesDifficulty({ platform: "codeforces", difficulty: 1500 }, selection), true);
assert.equal(passesDifficulty({ platform: "codeforces", difficulty: null }, selection), false);
assert.equal(passesDifficulty({ platform: "leetcode", difficulty: "Hard" }, selection), true);
assert.deepEqual(sortByDifficulty(problems, "asc").map((p) => p.id), ["foundation", "standard", "expert", "unknown"]);
assert.deepEqual(sortByDifficulty(problems, "desc").map((p) => p.id), ["expert", "standard", "foundation", "unknown"]);
assert.equal(buildDifficultyPayload(problems).named.find((b) => b.id === "cses-standard").count, 1);
assert.ok(SORTABLE_JUDGES.has("cses"));
assert.equal(suggestLevel({ cses: { band: 2 } }, problems).cses.difficulty, "cses-standard");
assert.deepEqual(suggestLevel({ codeforces: { rating: 1600 } }, problems), {});
assert.deepEqual(suggestLevel({ cses: { band: 7 } }, problems), {});
assert.deepEqual(suggestLevel({ cses: { band: 3 } }, problems), {});
console.log("CSES bands, composed filtering, sorting and explicit level passed");
