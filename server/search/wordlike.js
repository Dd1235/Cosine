// Does this query look like words?
//
// The search route refuses a query whose every term is absent from the corpus.
// That is right for BM25, which genuinely scores zero on it — but wrong for
// the meaning ranker, which has a real embedding for `rat` and answers it with
// Cat and Mouse, Save More Mice, Mice and Cheese. It was simply never asked.
//
// Relaxing that needs a line between "a real word this corpus doesn't use" and
// "someone leaned on the keyboard", and the obvious signal does not work:
// measured on the live index, `xkcdqq` scores 0.565 while `rat` scores 0.296,
// so no cosine cutoff separates them. That is the same finding that stopped
// the score-threshold idea the first time.
//
// What does separate them is shape. Gibberish is unpronounceable; words are
// not. Three rules, no dictionary and no dependency:
//
//   rat mouse cheese maze robot chess pizza train garden rhythm  → words
//   asdkjhqwe qqqqq zzzz xkcdqq lkjhgfdsa zxcvbn hjkl            → not
//
// The honest limit: a name is shaped like a word, so `deepya` passes. The
// meaning ranker will answer it with its nearest neighbours and say that
// nothing matched literally, rather than returning a clean zero. That is a
// real change to what this site promised about names, and it is written down
// in the README rather than left for someone to discover.

// Any vowel at all, y included — "rhythm" and "gym" are words.
const HAS_VOWEL = /[aeiouy]/;
// "qqqqq", "zzzz", "ffff": no English word triples a letter.
const TRIPLED = /(.)\1{2,}/;
// Five consonants in a row is a keyboard row, not a syllable. ("dijkstra"
// fails this, which costs nothing — it is in the corpus, so it never reaches
// here.)
const CONSONANT_RUN = /[bcdfghjklmnpqrstvwxz]{5,}/;

function isWordLike(token) {
  const t = String(token || "").toLowerCase();
  if (t.length < 2) return false;
  if (!HAS_VOWEL.test(t)) return false;
  if (TRIPLED.test(t)) return false;
  if (CONSONANT_RUN.test(t)) return false;
  return true;
}

// A query is word-like when every term in it is. One mashed token is enough to
// make the whole thing a mash — the alternative lets `graph asdkjhqwe` through
// on the strength of a word the corpus doesn't have anyway.
function queryIsWordLike(terms) {
  const list = (terms || []).filter(Boolean);
  return list.length > 0 && list.every(isWordLike);
}

module.exports = { isWordLike, queryIsWordLike };
