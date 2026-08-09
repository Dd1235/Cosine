# 13 — "graph" and "graphs" give very different results

**Date:** 2026-08-09
**Reported by:** a user, in one sentence, which turned out to be the largest
recall bug in the lexical index.

## The bug

| query | results | top hits |
| --- | --- | --- |
| `graph` | 546 | Clone Graph · Acyclic Graph Edges · Shortest Cycle in a Graph |
| `graphs` | **18** | Bubble Sort Graph · Kefa and Park · Ralph and Mushrooms |
| `tree` | 367 | Tree · Path Queries · Subtree Queries · Tree Diameter |
| `trees` | **35** | Erect the Fence · Cut Off Trees for Golf Event · Christmas Trees |

Not merely "different" — actively wrong. A rare term carries a large IDF, so
the handful of documents that happen to contain the plural outrank every
document about the actual technique. `trees` returns problems about *trees*.

Measured across 18 singular/plural pairs, **mean top-10 agreement was 8.9%**.
Ten of the eighteen pairs shared *nothing at all* in their top ten.

## Why the benchmark never caught it

Every one of the 71 labelled queries happened to use the same grammatical
number as the corpus. A benchmark only measures what somebody thought to
write down, and nobody writes the plural of their own test query.

It also can't be fixed by adding judgements: nobody is going to label the 546
problems matching `graph`. So the measurement is **agreement** rather than
relevance — asking the same question the other way should return the same
problems, whatever those problems are, and the singular's own results are the
reference. That's `npm run bench:plural`, and it fails the run if agreement
falls below 95%.

## The fix: s-stemming, guarded by the corpus vocabulary

`server/search/plurals.js`. A token folds to its singular **only when that
singular is a word this corpus actually contains**:

```
graphs   → graph      (546 documents have `graph`)
queries  → query      143 folds like this
vertices → vertex     7 irregulars, listed explicitly
series   ✗            there is no `sery`
bfs      ✗            no `bf`, and it is 3 letters
kruskals ✗            no `kruskal` in the corpus
```

958 of 5,715 vocabulary terms fold (16.8%). Documents and queries are folded
with the same map, in `Bm25Index`, `TfidfIndex` and the inverted index behind
the explain page — including the exact-title lookup, so *Minimum Height Trees*
still matches itself.

**Why not Porter.** It would also produce `sorting`→`sort`, `matrices`→`matric`,
`series`→`seri`, rewriting tokens that were fine. In a vocabulary full of names
(`kruskals`, `mos`, `sos`, `dsu`) a wrong stem is a silent recall bug with no
visible cause. Plurals were the reported problem; the guard means every fold
can be justified by pointing at two words that both exist.

## Results

**Agreement, the thing that was broken** (`bench:plural`, 18 pairs):

| | off | on |
| --- | --- | --- |
| mean top-10 agreement | 8.9% | **100%** |
| mean result-count ratio | 46.2% | **100%** |

**The 71-query benchmark**, now 81 with a `plural` slice (v7: ten existing
queries restated in the other number, inheriting their judgements):

| ranker | slice | P@1 | P@5 | MRR | nDCG@10 | R@100 |
| --- | --- | --- | --- | --- | --- | --- |
| **bm25** | all | ±0 | +0.005 | −0.001 | +0.008 | −0.003 |
| bm25 | plural | ±0 | ±0 | +0.026 | **+0.096** | ±0 |
| bm25 | technique | **−0.047** | −0.010 | −0.016 | ±0 | ±0 |
| hybrid | all | ±0 | +0.009 | +0.003 | +0.012 | +0.001 |
| dense | all | ±0 | ±0 | ±0 | ±0 | ±0 |
| **tfidf** | all | −0.013 | −0.005 | −0.014 | −0.013 | −0.032 |

**The cost, stated plainly.** bm25's technique slice loses P@1 0.047 — one
query of 21, *monotonic queue optimization dp sliding window maximum of dp
values*, where folding `values`→`value` shifts enough IDF mass to swap ranks 1
and 2 between two near-identical DP problems. 21 queries moved in total: 15
down, 6 up, and the ups are larger (`bfs jump game reachable shortest` +0.667,
`count separate land regions` +0.500).

tfidf pays more (nDCG −0.013 overall, paraphrase −0.084) and that is expected:
its IDF is unsmoothed `log(N/df)` over a cosine-normalised vector, so merging
two terms moves it further than BM25's saturated tf and smoothed IDF. bm25 is
the default and dense is untouched; tfidf is a comparison baseline, and it is
worse for this.

**Shipped anyway**, because the trade is a coin-flip between ranks 1 and 2 on
one benchmark query against a plural returning 3% of the right results. The
benchmark measures precision on queries that already worked; it cannot see a
question nobody could ask successfully.

## Notes

- The embeddings are **not** affected — `problemText` feeds the sentence
  encoder raw, and only the lexical tokenizer folds. The README's Ideas
  section claimed stemming would invalidate the committed embeddings; it
  wouldn't, and that claim is now corrected.
- `BENCH_STEM=0` turns folding off end to end for A/Bs, like `BENCH_EXPAND=0`.
- Dense agreement was already high and is unchanged: semantic search never had
  this problem, which is a decent argument for the two-ranker design.
