// Searchable document text shared by every local ranker and route vocabulary.
// Judge/platform names stay facets: indexing "leetcode" on every LeetCode
// record would make that word swamp useful terms. Native contest identifiers
// are different — users reasonably search for "weekly contest 520" — so keep
// only that narrow, discriminative part of source_topic.
const NATIVE_CONTEST_RE = /\b(?:(?:weekly|biweekly)\s+contest|contest)\s+\d+\b/i;

function nativeContestText(problem) {
  const topic = typeof problem?.source_topic === "string" ? problem.source_topic : "";
  return topic.match(NATIVE_CONTEST_RE)?.[0] || "";
}

function problemText(problem) {
  return [
    problem.title,
    problem.statement,
    ...(problem.tags || []),
    ...(problem.patterns || []),
    nativeContestText(problem),
  ].join(" ");
}

module.exports = { nativeContestText, problemText };
