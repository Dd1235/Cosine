const { suggestLevel } = require("./level");
const { parseSelection, passesDifficulty } = require("./difficulty");

// Personal practice preferences, not claimed ratings or cross-judge scores.
function validateLevels(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  for (const [judge, choice] of Object.entries(value)) {
    if (!choice || typeof choice !== "object" || Array.isArray(choice)) return false;
    if (judge === "leetcode") {
      if (Object.keys(choice).length !== 1 || !["easy", "medium", "hard"].includes(choice.tier)) return false;
    } else if (["codeforces", "atcoder"].includes(judge)) {
      const floor = judge === "atcoder" ? -1000 : 0;
      if (Object.keys(choice).length !== 2 || !Number.isInteger(choice.min) || !Number.isInteger(choice.max)
          || choice.min < floor || choice.max > 5000 || choice.min > choice.max) return false;
    } else return false;
  }
  return true;
}

function practiceLevels(signals, choices, problems) {
  const automatic = suggestLevel(signals, problems);
  delete automatic.cses; // CSES is a deliberate self-assessment, not an inferred rating.
  const suggest = Object.fromEntries(Object.entries(automatic).map(([judge, s]) => [judge, {...s, source: "profile"}]));
  const explicit = suggestLevel({cses: signals.cses}, problems).cses;
  if (explicit) suggest.cses = {...explicit, source: "manual"};
  for (const [judge, choice] of Object.entries(choices || {})) {
    if (!validateLevels({[judge]: choice})) continue;
    const difficulty = judge === "leetcode" ? `lc-${choice.tier}`
      : `${judge === "codeforces" ? "cf" : "atc"}:${choice.min}-${choice.max}`;
    const selected = parseSelection(difficulty);
    suggest[judge] = {
      difficulty, source: "manual", why: `Your saved ${judge} practice level`,
      count: problems.filter(p => p.platform === judge && passesDifficulty(p, selected)).length,
    };
  }
  return {automatic, suggest};
}
module.exports = {validateLevels, practiceLevels};
