const assert = require("node:assert/strict");
const { nativeContestText, problemText } = require("./problem_text");

const weekly = {
  title: "A Contest Problem",
  statement: "Solve it.",
  tags: [],
  patterns: [],
  source_topic: "LeetCode / Weekly Contest 520",
};
assert.equal(nativeContestText(weekly), "Weekly Contest 520");
assert.match(problemText(weekly), /Weekly Contest 520/);
assert.doesNotMatch(problemText(weekly), /LeetCode/);

assert.equal(
  nativeContestText({ source_topic: "LeetCode / Medium Hardest (generated)" }),
  "",
  "generic source buckets must not become search terms"
);
assert.equal(nativeContestText({ source_topic: "Codeforces / Contest 2262" }), "Contest 2262");

console.log("problem text contest metadata tests passed");
