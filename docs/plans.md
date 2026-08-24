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

## 2. Per-label audits — done, and one of them was wrong

Six label-first audits ran over mechanically generated candidate sets, every
proposed label then attacked by a second agent whose job was to refute it.

| Label | Candidates | Adds | What the batch actually showed |
| --- | ---: | ---: | --- |
| `sparse-table` | 207 | **3** | the estimate below was wrong — see the note |
| tree techniques | 62 | 21 | half the CF `trees` tag is tries and Fenwicks, not graph trees |
| `partition-dp` | 27 | 12 | real gap; "partition" in a statement is ~50% noise |
| `rerooting-dp` | 17 | 3 | 14 of 17 are subtree-only, exactly as predicted |
| knapsack | 16 | 0 | the cue found partition DPs, which is how §2's `partition-dp` row exists |

**The `sparse-table` estimate of 20–40 was wrong, and the reason is worth
keeping.** Three agents worked 207 candidates independently and all three
concluded the same thing: Codeforces' `data structures` tag is close to
orthogonal to this label. It sits on stack simulation, sort-with-a-set and
prefix sums as readily as on range structures — so it selects precisely the
population sparse-table is not. The corpus really does contain about five such
problems. **The cue to use next time is the technique's precondition, not a
judge tag: range min/max/gcd/AND over an array that is never updated.**

A judge tag is a cheap candidate generator and a bad one. The cues that worked
(`rerooting-dp`, `partition-dp`) described the *shape of the solution*; the ones
that failed (`sparse-table`, tree techniques) described a topic.

### What the audits found that was worth more than their own verdicts

Both are fixed, and both were found independently by more than one agent:

- **The family map only ran at ingest.** `FAMILY_PATTERNS` lived as compiled
  regexes inside `annotate_problem_urls.py`, so no sweep could reach it: 1,029
  problems of 3,468 were missing a family label their own labels implied, and
  `number-theory` sat on 40 problems while 394 carried a number-theory
  technique. The rules are now `families` in the taxonomy, shared with
  `scripts/apply_families.js`.
- **Off-vocabulary labels are dead weight** — 1,217 distinct names over 1,959
  label slots, 912 of them used exactly once, none reachable by any query. The
  definitional ones are aliased now; the rest need the ingest-side vocabulary
  constraint in §5.

---

## 2a. Dense embeddings depend on batch composition — the artifact is not reproducible

**This invalidates every dense/hybrid benchmark comparison across a corpus size
change**, and it is why v80's "three gated gains, one gated loss" on those
rankers should not be believed.

`scripts/embed_corpus.js` embeds in batches of 32 in corpus load order, and
`extractor(texts, …)` pads each batch to its own longest member. So a document's
vector depends on which 31 others share its batch. Measured directly: the same
problem embedded alone versus batched with the corpus's longest statement
differs by **cosine 4.0e-3**.

That is 28x the margin that decides real rankings. Adding weekly 516's three
problems flipped `longest stretch of characters with no repeats` from rank 1 to
rank 2 — between two documents separated by **0.000142** — and moved
dense/paraphrase −0.036 and hybrid/paraphrase −0.046 through the 0.02 gate,
along with several queries that have nothing to do with the new problems.

Proven, not inferred: holding the three records out and re-embedding reproduces
the previous benchmark **exactly**, and two consecutive embed+bench runs on an
unchanged corpus are byte-identical. So the pipeline is deterministic for a
fixed corpus and unstable across insertions — the worst combination, because it
looks reliable right up until you change something.

`embed_corpus.js`'s own header claims the committed artifact means "dev/CI/prod
all score against bit-identical doc vectors". True for a frozen corpus; false
the moment one problem is added.

**The fix** is to make each document's embedding independent of its neighbours:
pass `padding: "max_length", truncation: true` so every sequence is padded
identically, or embed with `BATCH_SIZE = 1`. Both cost time (embed is ~16s
today) and both require a one-off re-embed and a re-baselined benchmark, so it
is its own change, not a rider on a corpus edit.

Until then: **gate on bm25 and tfidf**, which are deterministic from text and
did not move at all. Treat a dense or hybrid slice move under ~0.05 as noise
unless the corpus size was unchanged.

## 2b. The benchmark under-rewards recall work, by construction

Found while gating v80, and it will affect every future labelling pass.

Relevant sets in `bench/queries.json` are **frozen lists of ids**. When a pass
adds a *correct* label, the newly-labelled problem starts ranking for that
technique — and nDCG counts it as noise, because it is not on the list. So
correct recall work reads as a regression.

Both of v80's largest bm25 moves are this and nothing else:

| query | move | what actually happened |
| --- | ---: | --- |
| `sqrt decomposition` | −0.078 | CF 1468-M *Similar Sets* took rank 6. It is a textbook sqrt-decomposition problem; the audit gave it the label it was missing |
| `interval dp balloon burst minimum cost` | −0.173 | six problems gained `interval-dp` when `dp-on-intervals` was aliased. All six are interval DPs |

bm25's whole −0.011 on the technique slice is these. Nothing got worse.

**Do not fix this by editing relevant sets alongside a change they judge** —
that is grading your own work. The honest version is a separate pass that
re-derives the relevant set for each *technique* query from the label it names,
reviewed on its own, with the ranking held fixed. Until then, read a
technique-slice drop after a labelling pass as a question, not a verdict, and
check what took the displaced slot before believing it.

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

**Two skills cover this now**, both readable as standalone briefs so codex or
another session can run them from a clone:

- `.claude/skills/add-contest/SKILL.md` — a whole contest. Q1 skipping, the
  pending queue, per-judge staging.
- `.claude/skills/add-problem/SKILL.md` — one or a few problems, by URL or by
  name, including the "here's my solution, no API calls" path and CSES, which
  belongs to no contest.

Both carry the Codeforces statement workaround, the two label traps, and the
embed-in-the-same-commit rule.

LeetCode weeklies are Sundays, biweeklies alternate Saturdays.

**Hard problems go to an agent, not the cheap model.** Measured on biweekly 189
and weekly 515: six problems, every solution verified against a brute force or a
BFS ground truth, every label canonical, and both audit traps avoided on
problems where they were live — `binary-search-answer` rejected on a
"minimise the maximum" problem after checking the feasibility test was trivial,
and `bitmask-dp` correctly split between Elevator Requests II (interval DP,
m ≤ 1500) and III (Held-Karp, ≤ 16 requests), a near-miss pair a careless
annotator would label identically.

Open: a GitHub Action that opens a PR weekly rather than this being a thing
someone remembers to do. Blocked on nothing except deciding the annotation step
runs with an API key in CI.

---

## 4b. The family sweep, measured on its own

**Applied: 1,152 labels across 1,023 problems** (`scripts/apply_families.js`),
in its own commit with its own embed and bench run — it takes `number-theory`
from 40 carriers to 434, an 11x change in that term's IDF, and only 4 of the 81
benchmark queries touch a family term at all. The benchmark can see a
regression on `binary-search` and `segment-tree` and is blind to one on
`number-theory` or `dynamic-programming`, so isolating it was the only way to
attribute anything.

Measured: **bm25 flat** (nDCG −0.001, Recall@100 −0.012). Four slices crossed
the 0.02 gate — three gains (dense/title +0.046, hybrid/paraphrase +0.038,
hybrid/plural +0.021) and one loss (hybrid/title −0.046, on a ranker that is
not served). tfidf/title Recall@100 +0.125.

The one honest cost: bm25's whole −0.049 technique-slice recall is **two
near-duplicate queries** ("sum over subsets dp bitmask" and "… bitmask dp
transform") losing the same single problem —
`leetcode-count-number-of-maximum-bitwise-or-subsets` slipped from inside the
top 100 to rank 107. It carries `submask-enumeration, bit-manipulation,
backtracking`, gained nothing from the sweep, and was simply outranked on the
query's `dp` token by ~400 problems that did. Dilution working exactly as
predicted, at the size predicted.

What the benchmark cannot show is the point of the change: `number theory` now
returns 1,625 matches led by *Counting Divisors* and *Odd Divisor*, where the
label sat on 40 problems before.

Writing it found a bug in the rules themselves: `dsu-on-tree` matched the DSU
rule and would have handed `union-find` to five problems that never call
`union()`. The taxonomy's own `consumingAliases` already records that the name
is a misnomer; the rule now has a negative lookahead and says why.

## 5. Two smaller things the samples turned up

- **Constrain the contest annotator's vocabulary.** `gpt-4.1` is not *worse*
  than mini — its labels are rarely false — but it emits off-vocabulary labels
  at 32.8% vs mini's 18.7% (z=6.5), and they are problem restatements
  (`peak-cell-condition`). Corpus-wide, **1,217 distinct off-vocabulary names
  sit on 1,959 label slots and 912 of them are used exactly once** — none
  reachable by any query. The v80 audits aliased the definitional ones
  (`prefix-tree`, `substring-search`, `two-pointer`, `prime-sieve`, and 20
  more), which is the tail this can reach; the rest need the fix at ingest,
  which is a vocabulary constraint, not a model swap. Affects 77 problems.
  One agent found a problem where **all five labels were off-vocabulary**
  (`codeforces-1870-h`) — effectively unlabelled while looking labelled.
- **`atcoder-abc159-f`'s statement summary is factually wrong** — it describes a
  value condition the real problem doesn't have. Statements are indexed, so a
  wrong summary is a retrieval bug. Worth a sweep for others like it.

---

## 6. What we are deliberately not doing

- **Auditing the corpus problem by problem.** Measured: 4.6 minutes and 24k
  tokens per problem, with verification. 3,461 problems is ~266 agent-hours and
  ~84M tokens. Audit by *label* over candidate sets instead.

### The next label pass should be driven by starved labels, not by text cues

Both skeptics landed on the same idea independently, and it beats the cue-based
selection this round used. **53 canonical labels have fewer than five carriers**
— `cartesian-tree` 2, `functional-graph` 4, `heavy-light-decomposition` 6,
`z-function` 5, `slope-trick` 2, `submask-enumeration` 2 — and a label with two
carriers answers essentially no query. That list is a finite worklist with an
obvious stopping point, where "find problems that look like X" is neither.

Two labels had **zero** carriers when they were added this round
(`bridge-tree`, `kruskal-reconstruction-tree`) — added precisely because two
audits hit them as walls: the agent found the technique, went looking for the
label, and had to pass. A canonical label nothing carries is a promise the
index cannot keep, so both were given their evidenced carriers in the same
commit.
- **A `source` column for auto-bookmarked problems**, until an importer exists
  that needs it. Migrations 0007 and 0008 were both additive and took minutes.
- **Stemming beyond plurals.** Porter also produces `matrices`→`matric` and
  `series`→`seri`; in a vocabulary full of names a wrong stem is a silent
  recall bug. Plurals shipped ([experiments/13](../experiments/13-plural-folding.md)).
- **A fourth library list.** `:done` + `again` + `marked 3mo+` already composes
  into a revision queue out of filters that exist.
