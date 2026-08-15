# Plans

Work that is decided but not done, and the evidence for why it is worth doing.
Kept out of the README, which is for what the site *is* rather than what it
might become — and out of `docs/implementation/`, which is untracked personal
notes. Everything here should be actionable by someone who isn't me.

Each item says what it costs, because the point of writing them down is to be
able to choose between them.

---

## 1. Label precision — removing what is wrong

**Measured, and the first removal is done.**

Two samples: `experiments/15-label-precision-sample.md` (one label, 25 sampled +
one stratum censused) and `experiments/16-general-precision-sample.md` (30
problems, 88 labels, stratified by judge and band).

**Headline: 69.3% of labels correct, 13.6% wrong (95% CI 7.1–20.5%), 15.9%
vague.** 11 of 30 problems carry at least one wrong label.

**The errors are not where anyone guessed.** Not a judge, not a difficulty band
— Codeforces above 1600 was the *cleanest* rated slice at 87.5%. They cluster in
**six label names**, all of them narrow techniques whose names have a loose
English reading to drift into:

| label | carriers | the mistake |
| --- | ---: | --- |
| `binary-search-answer` | 277 | plain binary search in a sorted array |
| `state-compression` | ~~163~~ 73 | rolling-array DP, or just "this DP has states" |
| `dp-on-dag` | 49 | array DP with no graph in it |
| `subset-dp` | 37 | non-bitmask knapsack |
| `sqrt-decomposition` | 21 | a segment-tree problem |
| `tree-diameter` | 9 | root depth |

By category: `dp` 25% wrong, `array` 23% wrong, versus **0 wrong in 20** across
graph / math / data-structure / string, whose names have no casual reading.

### Done: `state-compression`, 90 removals

The predictor was a **co-label**, not the judge or the difficulty:

| stratum | n | justified | evidence |
| --- | ---: | ---: | --- |
| A — has `bitmask-dp`/`subset-dp`/`profile-dp` | 61 | 64% | kept |
| B — only generic `dynamic-programming` | 64 | **0/10** | removed; LeetCode's own `bitmask` tag agrees on 0 of 52 |
| C — neither | 38 | 24% (censused) | 12 kept by name, 26 removed |

Precision on a "state compression" search goes from ~30% to ~66%. Every id and
its reason is in `data/analysis/_state-compression-removal.json`. The twelve
kept in stratum C are the ones a naive co-occurrence rule would have destroyed:
digit DPs with a used-digit mask, grid profile DPs, base-k encodings.

Benchmark: bm25 and tfidf flat, dense title −0.125 on one query (`house robber`,
which lost a label it should never have had — bm25, the ranker with the
exact-title bonus, is unaffected).

### Next: `binary-search-answer`, 277 carriers

The largest remaining offender. 225 of the 277 have no answer-search cue in
their statement at all, so a mechanical pre-filter narrows it but cannot decide
it. Brief written for delegation: **`docs/codex-label-audit.md`** — 1.5–2.5
hours, produces a list, does not touch the corpus.

The other four (116 problems total) are hand-checkable in a sitting once that
pattern is known.

### The rule for removals

One label at a time. Ids listed explicitly in the commit and in
`data/analysis/`. Never a blanket rule over a pattern of ids — stratum C is why:
a co-occurrence rule that looked obviously right would have deleted nine
textbook uses.

## 2. Per-label audits, aimed by the taxonomy report

The audit's items 3 and 9 need re-annotation over named candidates rather than
new vocabulary:

| Label | Uses today | Candidates to check | Expected |
| --- | ---: | --- | ---: |
| `sparse-table` | 1 in 3,461 | 166 CF `data structures` + 10 LC `binary-indexed-tree` misses | 20–40 |
| tree techniques | 56% of 224 tree problems | the 60 CF `trees` misses, starting with rated 2400+ | 30–60 |

Both are label-first, not problem-first: screen candidates cheaply, adjudicate
only the uncertain ones. Problem-first is the expensive mistake — see §5.

---

## 3. Codeforces ratings that haven't been published yet

**Recurring, cheap, easy to forget.** `data/unrated_problems.json` is the
worklist; `python3 scripts/refresh_cf_ratings.py --write` collects whatever has
landed and rewrites it.

Last run 2026-08-09: **all 20 waiting problems got their rating** (contests
2252/2253/2254, 800 through 2600) and the queue is now empty. A problem with no
rating is invisible to every difficulty filter, every sort and `my level`, so
this fails quietly rather than loudly — worth running weekly alongside the
contest ingest.

## 4. Contest ingest cadence

`scripts/ingest_contest.py <url>` then `scripts/fetch_statements.py` for
Codeforces (the dataset lags; Tavily doesn't). LeetCode weeklies are Sundays,
biweeklies alternate Saturdays.

Open: a GitHub Action that opens a PR weekly rather than this being a thing
someone remembers to do. Blocked on nothing except deciding the annotation step
runs with an API key in CI.

---

## 5. Two smaller things the samples turned up

- **Constrain the contest annotator's vocabulary.** `gpt-4.1` is not *worse*
  than mini — its labels are rarely false — but it emits off-vocabulary labels
  at 32.8% vs mini's 18.7% (z=6.5), and they are problem restatements
  (`peak-cell-condition`). Corpus-wide, 916 label names are used exactly once:
  9% of the index that can never match a query. The fix is a vocabulary
  constraint on the ingest path, not a model swap. Affects 77 problems.
- **`atcoder-abc159-f`'s statement summary is factually wrong** — it describes a
  value condition the real problem doesn't have. Statements are indexed, so a
  wrong summary is a retrieval bug. Worth a sweep for others like it.

---

## 6. What we are deliberately not doing

- **Auditing the corpus problem by problem.** Measured: 4.6 minutes and 24k
  tokens per problem, with verification. 3,461 problems is ~266 agent-hours and
  ~84M tokens. Audit by *label* over candidate sets instead.
- **A `source` column for auto-bookmarked problems**, until an importer exists
  that needs it. Migrations 0007 and 0008 were both additive and took minutes.
- **Stemming beyond plurals.** Porter also produces `matrices`→`matric` and
  `series`→`seri`; in a vocabulary full of names a wrong stem is a silent
  recall bug. Plurals shipped ([experiments/13](../experiments/13-plural-folding.md)).
- **A fourth library list.** `:done` + `again` + `marked 3mo+` already composes
  into a revision queue out of filters that exist.
