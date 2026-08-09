const { tokenize } = require("./tokenize");
const plurals = require("./plurals");

function problemText(p) {
  return [p.title, p.statement, ...(p.tags || []), ...(p.patterns || [])].join(" ");
}

function buildInvertedIndex(problems) {
  const postings = new Map();
  // Folded like the rankers are, so a term looked up here means the same thing
  // it means there — this index backs the explain page.
  const rawDocTokens = problems.map((p) => tokenize(problemText(p)));
  const pluralMap = plurals.ENABLED ? plurals.pluralMapFromDocs(rawDocTokens) : new Map();
  problems.forEach((p, docId) => {
    const tokens = plurals.foldTokens(rawDocTokens[docId], pluralMap);
    const seen = new Set();
    for (const tok of tokens) {
      if (seen.has(tok)) continue;
      seen.add(tok);
      let set = postings.get(tok);
      if (!set) {
        set = new Set();
        postings.set(tok, set);
      }
      set.add(docId);
    }
  });

  function lookup(term) {
    return postings.get(pluralMap.get(term) || term) || null;
  }

  return { postings, lookup, pluralMap };
}

module.exports = { buildInvertedIndex };
