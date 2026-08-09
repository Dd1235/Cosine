# 16 — Pattern-label precision: a 30-problem hand audit

**Question.** Search matches on `patterns`. A *wrong* pattern makes a problem surface for a query it has nothing
to do with — the worst failure a searcher can hit. Nobody had measured how often that happens. This is the first
measurement.

**Method.** 30 problems drawn at random, stratified so no judge or difficulty band dominates (LeetCode
easy/medium/hard, Codeforces above and below 1600, AtCoder, CSES). Every one of their 88 pattern labels was judged
individually by one human-equivalent evaluator against the problem's actual intended solution:

| verdict | meaning |
| --- | --- |
| `correct` | a genuine solution uses this technique |
| `wrong` | it does not — this label would mislead a searcher |
| `vague` | not false, but carries no information (`simulation` on a non-simulation problem, `greedy` where nothing is chosen greedily) |
| `unsure` | the summary was too thin and I could not verify |

Missing techniques were recorded separately. Most problems here are well-known and were judged from recognition;
CF 1427G's two editorial solutions and CF 2254A's rules were confirmed against the Codeforces editorial and problem
page rather than recalled.

---

## 1. Headline numbers

**88 labels across 30 problems (2.93 labels/problem, matching the corpus mean of 2.95).**

| verdict | count | share |
| --- | --- | --- |
| correct | 61 | **69.3%** |
| wrong | 12 | **13.6%** |
| vague | 14 | **15.9%** |
| unsure | 1 | 1.1% |

Problem-level, which is what a user actually feels:

- **11 / 30 problems (37%) carry at least one wrong label.**
- 19 / 30 (63%) carry at least one wrong *or* vague label.
- 11 / 30 (37%) are 100% clean.

### Uncertainty — read this before quoting any number

n=30 problems is a small sample, and the 88 labels are **clustered inside those 30 problems**, so the effective
sample size is nearer 30 than 88. A cluster bootstrap (20,000 resamples over problems, not labels) gives:

| metric | point | 95% CI |
| --- | --- | --- |
| wrong | 13.6% | **[7.1%, 20.5%]** |
| wrong + vague | 29.5% | [20.7%, 38.6%] |
| correct | 69.3% | [60.0%, 78.6%] |

So the honest headline is: **somewhere between 1-in-14 and 1-in-5 labels is actively wrong.** Every per-slice
number below rests on 8–11 labels from ~3 problems and is **directional only** — no slice-to-slice difference in
this table is statistically distinguishable from noise. The one place I make a strong claim (§3) is backed by a
full-corpus count, not by the sample.

This is also one evaluator's judgment, the same limitation the benchmark query set carries.

### By judge

| judge | n | correct | wrong | vague | unsure |
| --- | --- | --- | --- | --- | --- |
| CSES | 8 | 87.5% | 0.0% | 12.5% | — |
| LeetCode | 25 | 76.0% | 16.0% | 8.0% | — |
| AtCoder | 29 | 65.5% | 17.2% | 17.2% | — |
| Codeforces | 26 | 61.5% | 11.5% | 23.1% | 3.8% |

### By difficulty band

| band | n | correct | wrong | vague | unsure |
| --- | --- | --- | --- | --- | --- |
| CF >=1600 | 8 | **87.5%** | 12.5% | 0.0% | — |
| CSES | 8 | 87.5% | 0.0% | 12.5% | — |
| LC Hard | 8 | 87.5% | 0.0% | 12.5% | — |
| AtCoder <1600 | 10 | 80.0% | 10.0% | 10.0% | — |
| CF <1600 | 8 | 75.0% | 12.5% | 12.5% | — |
| LC Easy | 7 | 71.4% | **28.6%** | 0.0% | — |
| LC Medium | 10 | 70.0% | 20.0% | 10.0% | — |
| AtCoder DP contest (unrated) | 11 | 63.6% | 18.2% | 18.2% | — |
| AtCoder >=1600 | 8 | 50.0% | 25.0% | 25.0% | — |
| CF unrated (Div3, 2026) | 10 | **30.0%** | 10.0% | **50.0%** | 10.0% |

**Difficulty does not predict error.** Codeforces above 1600 — the band the brief guessed might be worst — is the
*best* rated band in the sample (87.5% correct, 1 wrong label in 8). LC Hard has zero wrong labels. Meanwhile
LC Easy has the highest wrong rate, and its two wrong labels sit on **`Binary Search` and `Climbing Stairs`** — two
of the most-trafficked problems in the corpus. Whatever drives these errors, it is not problem difficulty.

### By annotating model

| model | problems | n labels | correct | wrong | vague |
| --- | --- | --- | --- | --- | --- |
| gpt-4.1-mini | 27 | 78 | 74.4% | 14.1% | 11.5% |
| gpt-4.1 (contest ingest) | 3 | 10 | 30.0% | 10.0% | 50.0% |

The gpt-4.1 row is **3 problems** and cannot support a conclusion on its own. See §3 — the corpus-wide evidence says
something more specific, and less alarming, than "gpt-4.1 is worse".

---

## 2. Per-problem verdicts

Markers: `ok` = correct, **`WRONG`**, `vague`, `unsure`.

| id | title | band | label verdicts |
| --- | --- | --- | --- |
| atcoder-abc130-e | Common Subsequence | AC 1676 | dynamic-programming `ok` · counting `ok` · modular-arithmetic `vague` |
| atcoder-abc169-f | Knapsack for All Subsets | AC 1698 | **subset-dp `WRONG`** · modular-arithmetic `vague` · counting `ok` |
| atcoder-abc159-f | Knapsack for All Segments | AC 1876 | **prefix-sum `WRONG`** · dp-on-subsequences `ok` |
| atcoder-abc208-d | Shortest Path Queries 2 | AC 1190 | floyd-warshall `ok` · shortest-path `ok` |
| atcoder-abc157-e | Simple String Queries | AC 1443 | segment-tree `ok` · bit-manipulation `ok` · range-query `ok` · point-update `ok` · **sqrt-decomposition `WRONG`** |
| atcoder-abc206-d | KAIBUNsyo | AC 879 | union-find `ok` · greedy `vague` · graph-modeling `ok` |
| atcoder-dp-m | Candies | AC DP | prefix-sum `ok` · **dp-on-dag `WRONG`** · modular-dp `vague` · dp-optimization `ok` |
| atcoder-dp-l | Deque | AC DP | interval-dp `ok` · game-theory `ok` · game-dp `ok` |
| atcoder-dp-t | Permutation | AC DP | **dp-on-dag `WRONG`** · prefix-sum `ok` · modular-arithmetic `vague` · dp-optimization `ok` |
| codeforces-432-d | Prefixes and Suffixes | CF 2000 | kmp `ok` · string-matching `ok` |
| codeforces-1446-b | Catching Cheaters | CF 1800 | longest-common-subsequence `ok` · **brute-force `WRONG`** · dp-on-substrings `ok` |
| codeforces-1427-g | One Billion Shades of Grey | CF 3300 | max-flow `ok` · min-cut `ok` · grid-graph-modeling `ok` |
| codeforces-1184-a1 | Heidi Learns Hashing (Easy) | CF 1200 | equation-solving `ok` · search `vague` · brute-force `ok` |
| codeforces-522-a | Reposts | CF 1200 | dfs `ok` · **tree-diameter `WRONG`** |
| codeforces-1166-b | All the Vowels Please | CF 1100 | constructive-algorithm `ok` · factorization `ok` · grid-construction `ok` |
| codeforces-2254-c1 | Marenol (easy version) | CF Div3 | substring-replacement `vague` · parity-invariant `ok` · simulation `vague` |
| codeforces-2253-c | Sum of Distinct Values in a Matrix | CF Div3 | greedy `ok` · set-union `vague` · distinct-values `vague` · matrix-operations `vague` |
| codeforces-2254-a | Riptide | CF Div3 | **brute-force `WRONG`** · simulation `unsure` · case-analysis `ok` |
| cses-3219 | Sliding Window Mex | CSES | sliding-window `ok` · ordered-set `ok` · hash-map `vague` · mex `ok` |
| cses-1094 | Increasing Array | CSES | greedy `ok` |
| cses-1737 | Range Queries and Copies | CSES | persistent-segment-tree `ok` · range-sum-query `ok` · point-update `ok` |
| leetcode-binary-search | Binary Search | LC Easy | binary-search `ok` · **binary-search-answer `WRONG`** |
| leetcode-two-sum | Two Sum | LC Easy | hash-map `ok` · complement-search `ok` |
| leetcode-climbing-stairs | Climbing Stairs | LC Easy | dynamic-programming `ok` · **state-compression `WRONG`** · bottom-up-dp `ok` |
| leetcode-maximum-value-of-k-coins-from-piles | Maximum Value of K Coins From Piles | LC Hard | prefix-sum `ok` · dynamic-programming `ok` · knapsack `ok` |
| leetcode-minimum-cost-for-cutting-cake-ii | Minimum Cost for Cutting Cake II | LC Hard | greedy `ok` · sorting `ok` |
| leetcode-max-dot-product-of-two-subsequences | Max Dot Product of Two Subsequences | LC Hard | dynamic-programming `ok` · subsequence-dp `ok` · maximum-dot-product `vague` |
| leetcode-minimum-array-changes-to-make-differences-equal | Minimum Array Changes to Make Differences Equal | LC Medium | **binary-search-answer `WRONG`** · prefix-sum `ok` · **two-pointers `WRONG`** |
| leetcode-maximum-score-after-applying-operations-on-a-tree | Maximum Score After Applying Operations on a Tree | LC Medium | tree-dp `ok` · dfs `ok` · greedy `vague` |
| leetcode-count-partitions-with-max-min-difference-at-most-k | Count Partitions With Max-Min Difference at Most K | LC Medium | partition-dp `ok` · monotonic-queue-optimization `ok` · monotonic-queue `ok` · sliding-window `ok` |

### Why each wrong label is wrong

| problem | label | what the solution actually is |
| --- | --- | --- |
| leetcode-binary-search | `binary-search-answer` | Plain binary search over a sorted array. Binary-search-on-answer means searching a monotone predicate over the *answer space*. The taxonomy keeps these as separate canonical entries (`binary-search-on-answer` aliases to the latter), so this is a real collision. |
| leetcode-climbing-stairs | `state-compression` | The model meant "you only need two variables". That is a **rolling array / space optimization**. `state-compression` in the taxonomy's `dp` category means bitmask DP. |
| atcoder-dp-m, atcoder-dp-t | `dp-on-dag` (×2) | Both are 1-D counting DPs over an array accelerated by prefix sums. There is no graph anywhere in either problem. `dag-dp` aliases to this label, so the pollution is real. |
| atcoder-abc169-f | `subset-dp` | A knapsack-style counting DP with N,S ≈ 3000. `subset-dp`'s aliases (`dp-on-subsets`, `subset-enumeration`) make it unambiguously the bitmask-DP label. The correct label, `knapsack`, is missing — and the problem is *titled* "Knapsack for All Subsets". |
| codeforces-522-a | `tree-diameter` | Longest root-to-node depth from a fixed root, not the longest path between any two nodes. |
| atcoder-abc157-e | `sqrt-decomposition` | Solved with a segment tree of 26-bit masks, or 26 BITs. Sqrt decomposition can in principle solve *any* range query, which is exactly why applying it here empties the label. |
| leetcode-minimum-array-changes… | `binary-search-answer` | You enumerate every X in [0,k] with a difference array. The cost is not monotone in X, so binary search is not merely unused — it is unsound here. |
| leetcode-minimum-array-changes… | `two-pointers` | Not used. LeetCode's own tags are array / hash-table / prefix-sum. |
| atcoder-abc159-f | `prefix-sum` | The DP is `dp[i][j] = dp[i-1][j] + dp[i-1][j-a_i]` with an `+= i` seeding term. No prefix sums. |
| codeforces-1446-b | `brute-force` | An O(nm) modified-LCS DP over n,m ≤ 5000. Brute force is the thing the problem is designed to defeat. |
| codeforces-2254-a | `brute-force` | Sort the three values, answer is `min(b-a, c-b)`, or 0 if two are already equal. There is no candidate set to enumerate. (Official tags: implementation, sortings.) |

The one `unsure`: `simulation` on **codeforces-2254-a**. The intended solution is the O(1) formula above, but
Codeforces is Cloudflare-blocked to fetch and I could not confirm the bound on `a,b,c`. If they are tiny, a literal
round-by-round loop is a legitimate Div-3-A solution and the label is fine; if they reach 1e9 it is a TLE and the
label points at the wrong approach.

---

## 3. Where the errors concentrate

**Not in a judge. Not in a difficulty band. In a handful of specific label names.**

Break the 12 wrong labels down by *what kind of label* went wrong:

| kind | count | labels |
| --- | --- | --- |
| **A specific technique used in its broad, everyday sense instead of its narrow CP sense** | **7 / 12 (58%)** | `binary-search-answer` ×2, `dp-on-dag` ×2, `state-compression`, `subset-dp`, `tree-diameter` |
| A technique that is simply not used at all | 3 | `prefix-sum`, `two-pointers`, `sqrt-decomposition` |
| `brute-force` on a problem with nothing to brute-force | 2 | `brute-force` ×2 |

Bucket A is the whole story. In every one of those seven, the annotator picked a label whose *plain English reading*
fits ("this DP has stages, so it's a DAG"; "this compresses state to two variables"; "this searches for an answer")
but whose *taxonomy meaning* is narrower. And these are precisely the **high-value precision queries** — nobody
types `binary-search-answer` casually; they type it because they want that specific technique. So the errors land
exactly where a wrong hit hurts most.

By taxonomy category the same thing shows up as `dp` 25% wrong (4/16) and `array` 23% wrong (5/22), against
**0 wrong out of 20** across `graph`, `math`, `data-structure` and `string` combined. Graph and data-structure
labels are near-perfect here (`floyd-warshall`, `kmp`, `persistent-segment-tree`, `max-flow`/`min-cut`,
`union-find`, `monotonic-queue` all correct) because those names have no casual English reading to drift into.

### The targeted re-audit, sized against the full corpus

Six labels produced 7 of the 12 wrong verdicts. Counting them across all 3,461 problems:

| label | corpus usage | note |
| --- | --- | --- |
| `binary-search-answer` | **277 problems (8.0%)** | wrong twice in a 30-problem sample |
| `state-compression` | **163 problems (4.7%)** | wrong once; means bitmask DP, gets used for "O(1) space" |
| `dp-on-dag` | 49 (1.4%) | wrong twice |
| `subset-dp` | 37 (1.1%) | wrong once |
| `sqrt-decomposition` | 21 (0.6%) | wrong once |
| `tree-diameter` | 9 (0.3%) | wrong once |
| **union** | **525 problems (15.2% of corpus)** | |

**This is the actionable subset.** Two properties make it cheap:

1. `dp-on-dag`, `subset-dp`, `sqrt-decomposition` and `tree-diameter` total **116 problems** — small enough to
   hand-check exhaustively in one sitting, and each has a crisp mechanical test (is there an actual DAG? is there a
   bitmask over ≤ ~22 elements? is the intended complexity O((n+q)√n)? is it a path between two arbitrary nodes?).
2. `binary-search-answer` (277) and `state-compression` (163) are bigger but both admit a cheap **pre-filter**
   rather than a full re-annotation: flag `binary-search-answer` wherever it co-occurs with plain `binary-search`
   and the problem has no minimize-the-maximum / maximize-the-minimum objective; flag `state-compression` wherever
   it appears without `bitmask` or any small-set-of-items signal. Both filters should cut the review set hard before
   a human or a stronger model ever sees it.

If the sample rate holds, re-auditing those 525 problems addresses roughly **58% of all wrong labels in the corpus**
while touching 15% of it.

### On the two models — the sample's scariest number is the wrong reading

The gpt-4.1 slice scored 30% correct, but that is 10 labels from 3 problems and **only one of them was wrong**. The
other seven non-correct were `vague`. The corpus lets us test the mechanism at a useful n instead of guessing:

| | problems | labels | **non-canonical labels** |
| --- | --- | --- | --- |
| gpt-4.1-mini | 3,384 | 9,870 | 1,850 (**18.7%**) |
| gpt-4.1 (contest ingest) | 77 | 344 | 113 (**32.8%**) |

z = 6.5, p < 0.0001. gpt-4.1 invents off-vocabulary label names at **1.75× mini's rate**. And the labels it invents
are problem restatements, not techniques — straight from the corpus:

```
codeforces-2248-f  peak-cell-condition, rectangle-updates
codeforces-2253-d  coordinate-increment-sequence, minimizing-euclidean-distance
codeforces-2253-e  diameter-intersection-analysis, path-enumeration
codeforces-2253-b  adjacent-swap, maximum-alternating-subsequence
codeforces-2253-c  set-union, distinct-values, matrix-operations
```

So the correct reading is **not** "gpt-4.1 is less accurate". Its labels are rarely false; they are frequently
*empty* — restating the problem's surface where a technique name belongs. That is consistent with why it was adopted
for contests in the first place (mini was *missing* techniques): gpt-4.1 does find more, and its extra output is
verbose rather than incorrect. The fix is **vocabulary constraint at generation time, not a model swap** — the
contest path should reject any label not in `canonical` (or not resolvable through `aliases`) and re-ask.

That path is also small enough to fix now: **77 problems**.

One near-miss worth a one-line alias: `codeforces-1992-g` carries `dp-over-subsets`, which is `subset-dp` — the
alias table already has `dp-on-subsets` but not `dp-over-subsets`.

### The canonical / non-canonical split

| | n | correct | wrong | vague |
| --- | --- | --- | --- | --- |
| canonical labels | 66 | 69.7% | **18.2%** | 10.6% |
| non-canonical labels | 22 | 68.2% | **0.0%** | **31.8%** |

Clean and counter-intuitive: **off-vocabulary labels were never wrong — they were three times more likely to be
useless.** `parity-invariant`, `range-query`, `point-update`, `factorization`, `complement-search` and
`grid-construction` are all accurate and genuinely searchable, and simply belong in the taxonomy.
`maximum-dot-product`, `distinct-values`, `matrix-operations` and `substring-replacement` are titles wearing a
label's clothes.

Corpus-wide the tail is large: **19.2% of all 10,214 label instances are non-canonical, spread over 1,221 distinct
names, 916 of which are used exactly once.** A label used once in a 3,461-problem corpus can never do retrieval work
— it is 9% of the index earning nothing.

### Model confidence is not a usable filter

`pattern_confidence` barely separates: mean 0.922 on correct vs 0.873 on wrong. Eight wrong labels carry
confidence ≥ 0.90 (`sqrt-decomposition` 0.90, `binary-search-answer` 0.95, `tree-diameter` 0.90, `subset-dp` 0.98).
The low tail does carry signal — 5 of the 7 labels at confidence ≤ 0.80 were wrong or vague — but that tail is only
7 labels of 88. **Do not use confidence to gate a re-audit; it will miss the confident errors, which are most of them.**

---

## 4. Missing labels

23 / 30 problems are missing at least one technique they clearly use; 36 total, ~1.2 per problem. The recurring
gaps:

- **`counting` (4×) and `combinatorics` (2×)** — applied inconsistently. `atcoder-abc130-e` and `atcoder-abc169-f`
  both get `counting`; `atcoder-abc159-f`, `atcoder-dp-m` and `atcoder-dp-t` are the same kind of "count the
  configurations mod p" problem and do not. This is the clearest inconsistency in the sample: near-identical
  problems annotated in the same batch, minutes apart, disagree.
- **`knapsack` (3×)** — missing on `atcoder-abc169-f` and `atcoder-abc159-f`, both of which have "Knapsack" **in the
  title**, and on `atcoder-dp-m` (bounded knapsack). Worth a targeted sweep: title contains "knapsack" but patterns
  do not.
- **`two-pointers` (3×)**, **`sorting` (2×)**, **`divisors` (2×)** — ordinary omissions.
- **`min-cost-flow` on codeforces-1427-g.** The editorial gives two solutions: repeated min-cuts with incremental
  max-flow, and an LP-dual min-cost-max-flow. The labels capture the first (`max-flow`, `min-cut` — both correct)
  and miss the second. `min-cost-flow` is already canonical, with `min-cost-max-flow` aliased to it.
- **`fibonacci` and `rolling-array` on Climbing Stairs** — the second is what `state-compression` was reaching for.
- **`prefix-sum` on leetcode-count-partitions…** — the dp-sum-over-window is prefix-summed, and LeetCode's own tags
  list it.

The general shape: **missing labels are the specific one under a present generic one** (`knapsack` under
`dynamic-programming`, `difference-array` under `prefix-sum`, `min-cost-flow` under `max-flow`) — the exact mirror
of the wrong-label failure, where an over-specific label was used in a generic sense. Both point at the same root
cause: the annotator is not holding the specific-vs-family distinction that `with_families()` exists to encode.

**Out of scope but noticed:** `atcoder-abc159-f`'s statement summary is wrong. It says "strictly increasing
subsequences" — the real problem counts subsequences by *increasing index*, with no condition on values. The
summary misread the index condition as a value condition. Statement summaries are indexed text, so this one is
also a retrieval defect.

---

## 5. Verdict

**The labels are mostly right, and where they are wrong they are wrong in a small, nameable, fixable way.** Roughly
69% of labels are correct and 14% (95% CI 7–20%) are actively wrong, which at 2.95 labels per problem means about
a third of problems carry at least one misleading pattern — real, but not a crisis, and *not* spread evenly. It is
not a judge problem (CSES and LeetCode Hard have zero wrong labels), and it is emphatically not a difficulty
problem — Codeforces above 1600 was the cleanest rated band in the sample and the two worst offenders were
LeetCode's `Binary Search` and `Climbing Stairs`. 58% of the wrong labels are one repeated mistake: a narrow
technique name (`binary-search-answer`, `state-compression`, `dp-on-dag`, `subset-dp`, `tree-diameter`,
`sqrt-decomposition`) applied in its loose English sense, which is destructive precisely because those are the
queries users type when they want one specific thing. Those six labels cover 525 problems (15.2% of the corpus),
116 of them small enough to hand-check outright and the two large ones (`binary-search-answer` at 277,
`state-compression` at 163) reducible by a mechanical co-occurrence pre-filter — so most of the total error is
reachable without re-annotating anything. Do not gate that work on `pattern_confidence`; it does not separate
(0.92 correct vs 0.87 wrong, and eight wrong labels sit at ≥0.90). Separately and independently, the contest
ingest path needs a vocabulary constraint, not a model change: gpt-4.1 is not less accurate than mini, but it emits
off-vocabulary labels at 1.75× the rate (32.8% vs 18.7%, p<0.0001), and those are problem restatements
(`peak-cell-condition`, `minimizing-euclidean-distance`) that can never be searched for — rejecting any output not
in `canonical`/`aliases` and re-asking would fix 77 problems and stop the drift before it scales.

---

*Sample: `samples/general.json`, 30 problems / 88 labels, judged 2026-08-09. Corpus at time of audit: 3,461
problems, 10,214 label instances (3,384 gpt-4.1-mini / 77 gpt-4.1).*

*Sources consulted for problems judged from outside recognition:*
*[CF Global Round 11 editorial](https://codeforces.com/blog/entry/83553?locale=en) (1427G),*
*[CF 2254A](https://codeforces.com/problemset/problem/2254/A),*
*[USACO Guide — One Billion Shades of Grey](https://usaco.guide/problems/cf-one-billion-shades-of-grey/solution).*
