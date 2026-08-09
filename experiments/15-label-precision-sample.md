# 15 — Label precision: is `state-compression` filler?

**Date:** 2026-08-09
**Scope:** research only. Nothing under `data/` was modified.
**Question:** [14-taxonomy-audit.md §3c](14-taxonomy-audit.md) claimed `state-compression` (163 uses, 8th
most common label) is filler meaning "this DP has states". That was a guess off ~10 hand-reads.
This is the measurement.

**Criterion.** A use is *justified* if a mainstream solution compresses state — a bitmask over a
set, a packed row/column profile, or a base-k encoding of a small tuple. *Wrong* if no mainstream
solution does. *Unsure* if the compression appears only in an **optional** optimisation (a plain
hash set or dict also passes), or the evidence is too thin.

---

## Verdict

**The audit was right, and if anything understated it.** On the 25 randomly sampled carriers:
**9 justified, 15 wrong, 1 unsure.**

But the naive extrapolation from those 25 is the wrong number, and it is wrong in the *optimistic*
direction. The sample over-drew the one slice where the label is mostly correct (56% of the sample
vs 37% of the population — a 1.9σ draw, unlucky but not suspicious). Post-stratifying on that slice,
and replacing the worst-sampled stratum with a full census, gives:

| Estimate | justified | wrong | unsure |
|---|---:|---:|---:|
| Naive, from the 25 | 59 (36%) | **98 (60%)** | 7 |
| **Post-stratified (use this)** | **48 (30%)** | **112 (69%)** | 3 (2%) |
| 95% range on the post-stratified figure | 33–78 | **82–127** | — |

So: **roughly 112 of the 163 uses are wrong — about 69%, and I am confident it is at least half
(lower bound 82, i.e. 50%).** A search for "state compression" today returns 163 problems of which
~48 are about state compression. Precision ≈ 30%.

Three things make this stronger than 25 hand-reads normally would:

1. **An independent second opinion exists.** LeetCode publishes its own `bitmask` tag (43 problems
   corpus-wide, 2.9% of LC). Among our LC carriers it fires on **30/43 (70%)** of one stratum and
   **0/79 (0%)** of the other two. It is a high-precision, low-recall signal — its presence is strong
   evidence, its absence weak — and it partitions the carriers exactly where my hand-reads do.
2. **The worst-sampled stratum was censused, not extrapolated.** The random 25 drew only 1 of the 38
   problems in stratum C. Extrapolating 23% of the population from n=1 would have made the headline
   meaningless (±23 points on its own), so I read all 38. That part of the estimate has **zero**
   sampling error.
3. **The residual uncertainty is concentrated in one stratum** (A, 14 of 61 sampled), and it does not
   change any decision below.

---

## The 25, in sample order

`A` = also carries a bitmask-family label (`bitmask-dp`/`subset-dp`/`profile-dp`) ·
`B` = carries generic `dynamic-programming`, no bitmask sibling · `C` = neither.

| # | id | title | str | verdict | reason |
|---:|---|---|:--:|:--|---|
| 1 | `codeforces-1423-j` | Bubble Cup hypothesis | A | **wrong** | Digit DP over the bits of m with a bounded **carry**. A carry counter is a state, not a compressed set. (CF tags it `bitmasks` — I disagree; that tag reflects the binary setting, not a packed state.) |
| 2 | `leetcode-minimum-swaps-to-make-sequences-increasing` | Min Swaps To Make Sequences Increasing | B | **wrong** | LC 801. Two states, `swap[i]`/`noswap[i]`. Archetypal "the DP has states" filler. |
| 3 | `cses-1159` | Book Shop II | B | **wrong** | Bounded knapsack (binary splitting / deque). Nothing to compress; the 1-D rolling array is *space* compression, a different thing. |
| 4 | `codeforces-1681-d` | Required Length | C | *unsure* | Reachable values are `x·2^a·3^b·5^c·7^d`, so the (a,b,c,d) tuple **can** be packed into an index — but a `set<long long>` BFS also passes, and CF tags it `brute force, hashing`. Compression is optional here. **Settles it:** whether we count optional optimisations; if yes → justified. |
| 5 | `leetcode-minimum-distance-to-type-a-word-using-two-fingers` | Min Distance to Type a Word… | B | **wrong** | LC 1320. The trick is a state *reduction* (one finger is pinned to `word[i-1]`), leaving a 2-D DP. Flattening `i*27+j` for a memo key is not the technique. |
| 6 | `atcoder-dp-o` | Matching | A | **justified** | AtCoder EDPC O — *the* textbook bitmask DP. `dp[mask]` over the set of matched women. |
| 7 | `leetcode-number-of-ways-to-stay-in-the-same-place-after-some-steps` | Number of Ways to Stay in the Same Place… | B | **wrong** | LC 1269. DP over (steps, position). No set anywhere. |
| 8 | `codeforces-1031-b` | Curiosity Has No Limits | A | **wrong** | Brute-force the 4 values of `t_1`, then each `t_{i+1}` is forced. The 2 bits come from the input; nothing is being compressed. `bit-manipulation` is the right label. |
| 9 | `leetcode-minimum-xor-sum-of-two-arrays` | Minimum XOR Sum of Two Arrays | A | **justified** | LC 1879, n≤14. Assignment-problem bitmask DP. LC's own `bitmask` tag agrees. |
| 10 | `leetcode-count-number-of-ways-to-place-houses` | Count Number of Ways to Place Houses | B | **wrong** | LC 2320. Answer is `fib(n+1)²`; the two sides are independent. Linear DP, 2 states. |
| 11 | `leetcode-minimum-moves-to-spread-stones-over-grid` | Min Moves to Spread Stones Over Grid | A | **justified** | LC 2850. Bitmask DP matching surplus stones to the set of empty cells (LC editorial approach 2). LC `bitmask` tag agrees. |
| 12 | `leetcode-visit-array-positions-to-maximize-score` | Visit Array Positions to Maximize Score | B | **wrong** | LC 2786. State = parity of the last element. Two states. |
| 13 | `leetcode-maximum-score-from-performing-multiplication-operations` | Max Score from Performing Multiplication Ops | B | **wrong** | LC 1770. Right index is *derived* from (op, left) — a state reduction, not a compression. |
| 14 | `codeforces-855-e` | Salazar Slytherin's Locket | A | **justified** | Digit DP where the state is a **parity bitmask over ≤10 digits**. Exactly the technique. CF tags `bitmasks`. |
| 15 | `leetcode-minimum-moves-to-clean-the-classroom` | Min Moves to Clean the Classroom | A | **justified** | BFS over (cell, **bitmask of collected litter**, energy). The mask is load-bearing. |
| 16 | `leetcode-number-of-squareful-arrays` | Number of Squareful Arrays | A | **justified** | LC 996, n≤12. Hamiltonian-path count via `dp[mask][last]`. LC `bitmask` tag agrees. |
| 17 | `leetcode-maximum-product-of-subsequences-with-an-alternating-sum-equal-to-k` | Max Product of Subsequences… | A | **wrong** | DP over (index, alternating sum, capped product, parity). No subset mask — `bitmask-dp` is wrong here too. LC tags: `array, hash-table, dynamic-programming`. |
| 18 | `leetcode-paint-house-iv` | Paint House IV | B | **wrong** | LC 3429. Pairs houses from both ends; 3×3 colour combos. A 2-D DP index is not a base-k packing — if it were, every 2-D DP would qualify, which is the failure mode itself. |
| 19 | `codeforces-534-f` | Simplified Nonogram | A | **justified** | 5×20 grid, column-by-column DP whose state is the **5-bit column profile** + segment counts. Textbook profile DP. |
| 20 | `leetcode-maximum-number-of-groups-getting-fresh-donuts` | Max Number of Groups Getting Fresh Donuts | A | **justified** | LC 1815. State is the count-vector of remainders (batchSize≤9), **packed into one integer key**. The base-k case, verbatim. |
| 21 | `leetcode-partition-array-for-maximum-xor-and-and` | Partition Array for Maximum XOR and AND | A | **wrong** | LC tags are `math, greedy, bit-manipulation, enumeration` — **no `dynamic-programming` at all**, so the packed-triple DP is not the accepted solution. `bitmask-dp` is also wrong here. |
| 22 | `leetcode-find-the-maximum-number-of-fruits-collected` | Find the Max Number of Fruits Collected | B | **wrong** | LC 3363. Child 1's path is forced down the diagonal and the other two regions don't overlap → three *independent* 1-D DPs. Decomposition, not packing. |
| 23 | `leetcode-partition-equal-subset-sum` | Partition Equal Subset Sum | A | **wrong** | LC 416, plain 0/1 knapsack. The `bitset` speed-up is a machine-word trick, not state compression — and `subset-dp` is misapplied too (that means DP over subsets/SOS). |
| 24 | `leetcode-find-minimum-cost-to-remove-array-elements` | Find Min Cost to Remove Array Elements | B | **wrong** | State = which of the first three elements carried over. One index. |
| 25 | `leetcode-minimum-incompatibility` | Minimum Incompatibility | A | **justified** | LC 1681, n≤16. Bitmask DP with submask enumeration over used elements. LC `bitmask` tag agrees. |

**Totals: 9 justified · 15 wrong · 1 unsure.**

---

## Where the misapplication concentrates

It is not spread evenly, and it is not really about the judge or the difficulty. **One co-label
predicts it almost perfectly.**

### The signal: does the problem carry a bitmask-family sibling?

| Stratum | Definition | Population | Sampled | justified | wrong | LC `bitmask` tag |
|---|---|---:|---:|---:|---:|---:|
| **A** | carries `bitmask-dp` / `subset-dp` / `profile-dp` | 61 | 14 | 9 (64%) | 5 (36%) | **30/43 = 70%** |
| **B** | carries generic `dynamic-programming`, no bitmask sibling | 64 | 10 | **0 (0%)** | **10 (100%)** | **0/52 = 0%** |
| **C** | neither | 38 | **38 (census)** | 9 (24%) | 26 (68%) | **0/27 = 0%** |

Stratum B is the finding. **Ten for ten wrong in the sample**, and LeetCode — a judge that does
publish a `bitmask` tag, on 43 of its problems — tags **zero** of the 52 LC problems in this
stratum. Two independent methods, same answer. `state-compression` + generic `dynamic-programming`
+ nothing else is, as near as I can measure, a pure synonym for "this is a DP".

Stratum A is where the label earns its keep: 64% correct, 24× enriched for LC's `bitmask` tag over
the 2.9% baseline. Even there it is *redundant* — every justified case in A already carries
`bitmask-dp`, so removing `state-compression` from A entirely would lose no findability, only the
literal phrase.

Stratum C is mixed and is the interesting third: 9 genuine uses that carry **no** bitmask label at
all, so a `bitmask-dp` co-occurrence rule alone would silently delete them. They are the digit-DP-
with-a-used-digit-mask and grid-profile families:

> **Genuine, keep (9):** `leetcode-count-special-integers` and `leetcode-numbers-with-repeated-digits`
> (10-bit used-digit mask), `leetcode-painting-a-grid-with-three-different-colors` and
> `leetcode-number-of-ways-to-paint-n-3-grid` (column packed base-3 — textbook profile DP),
> `leetcode-tiling-a-rectangle-with-the-fewest-squares` (skyline profile), `leetcode-unique-paths-iii`
> and `leetcode-maximum-number-of-achievable-transfer-requests` (visited/subset mask; both carry LC's
> `bit-manipulation` tag), `atcoder-abc114-c` (3-bit mask over {3,5,7}), `leetcode-poor-pigs`
> (base-(T+1) encoding).
>
> **Unsure (3):** `codeforces-1681-d`, `leetcode-count-beautiful-numbers` (smooth-number exponent
> packing — real, but optional), `leetcode-count-ways-to-choose-coprime-integers-from-rows`
> (mask-over-prime-factors is one solution, Möbius is the labelled one).
>
> **Wrong (26):** the rest — the digit DPs whose state is just "last digit" or a running sum
> (`count-stepping-numbers-in-range`, `count-good-integers-in-a-range`,
> `non-negative-integers-without-consecutive-ones`, `number-of-balanced-integers-in-a-range`, …),
> the multi-agent grid DPs (`cherry-pickup`, `cherry-pickup-ii`), the graph/SCC DPs
> (`codeforces-1137-c`, `codeforces-894-e`, `codeforces-576-d`), plus `codeforces-343-a` and
> `cses-1729`.

### The non-signals

Checked, and largely explained away by the stratum effect:

- **Judge.** LeetCode is 122/163 (75%) of carriers vs 43% of the corpus, so the label *is*
  LC-skewed. But within-sample, LC is 6/18 justified (33%) and CF is 3/5 (60%) — small n, and the
  gap disappears once you condition on stratum. LC's dominance is a volume effect, not a
  quality-of-judge effect. **A judge-scoped fix would be wrong.**
- **Difficulty.** LC Medium carriers are 1/6 justified in-sample vs LC Hard 5/12 — suggestive, but
  the population split is 29 Medium / 92 Hard / 1 Easy, and stratum B is 15/29 of Medium vs 36/92 of
  Hard. Difficulty is a proxy for stratum, not an independent axis. CF ratings show no trend at all
  (strata are evenly spread across all four bands). **A difficulty-scoped fix would be wrong.**
- **Annotator model.** All 163 carriers were annotated by `gpt-4.1-mini`; not one by `gpt-4.1`. So
  this is not a model-comparison finding — but it is consistent with §14's result that mini
  substitutes a familiar word for the technique it cannot see.
- **Stored confidence is useless here.** Mean `pattern_confidence` for `state-compression` is 0.892
  in stratum A vs 0.809 in B and 0.784 in C. Directionally right, wildly overconfident, and the
  ranges overlap completely (B spans 0.60–0.90). No threshold separates the classes. Don't build the
  fix on it.

**Conclusion: the fix is targetable, on exactly one axis — the co-label.**

---

## Recommendation

**Remove `state-compression` from stratum B (64 problems) mechanically, hand-fix the 26 wrong cases
in stratum C, and leave stratum A alone for now.** Do not delete the label.

Projected effect on precision (a search for "state compression"):

| Action | carriers left | justified left | precision |
|---|---:|---:|---:|
| leave it | 163 | ~48 | **30%** |
| drop stratum B (64, mechanical) | 99 | ~48 | **48%** |
| + drop the 26 clear-wrong in C (hand-listed above) | 73 | ~48 | **66%** |
| + re-annotate the ~22 wrong in A | ~51 | ~48 | ~94% |

Reasoning:

1. **Stratum B is the safe, large, mechanical win.** 64 problems, 39% of all carriers, with two
   independent lines of evidence putting the justified rate at zero (sample 0/10; LC `bitmask` tag
   0/52). The 95% upper bound on what we'd lose is 18 problems, and the LC tag evidence pushes the
   realistic figure to ~0. Every one of them keeps `dynamic-programming`, so nothing becomes
   unfindable — they just stop answering a query they have nothing to do with. This needs no LLM:
   it is a filter on `patterns`, exactly the kind of edit `normalize_patterns.js` already does.
2. **Do not use a `bitmask-dp` co-occurrence rule as the whole fix.** It would take out the 9
   genuine stratum-C uses named above — including two textbook profile DPs and the used-digit-mask
   digit DPs. Those are the *best* problems the label has. Stratum C has to be handled by the
   explicit 26-id list, which is why I censused it.
3. **Leave stratum A.** It is 64% correct, and its errors are the least harmful kind: those five
   problems all carry `bitmask-dp` too, so they were already going to surface for bitmask queries —
   the wrong `state-compression` adds no new bad results. Fixing A means re-annotating 61 problems
   to recover ~22, which is poor value against §14's ranked backlog and cuts against the standing
   preference to re-annotate only new/contest problems.
4. **Don't split it into a narrower label.** The narrower label already exists — it is `bitmask-dp`
   (100 uses), and §3b of the audit already flags the 59-problem overlap as a near-duplicate pair.
   Adding a third name for the same idea makes the split-index problem worse. If anything, once B and
   C are cleaned the remaining ~73 carriers are close enough to `bitmask-dp` that **aliasing
   `state-compression` → `bitmask-dp` becomes worth considering** — with one caveat: it is not a true
   synonym for the 9 stratum-C profile/base-k problems, and "state compression" (状态压缩) is a phrase
   people genuinely type. Keep it as a label; just stop applying it to every DP.
5. **Don't delete the label.** ~48 problems use it correctly and it is a real, searchable technique
   name. This is a precision problem with a known, bounded fix, not a bad concept.

**Sequencing note.** This changes `patterns`, which is indexed text — the corpusHash covers
title/statement/tags/patterns — so whichever subset ships needs `npm run embed` in the same commit.

This slots into §14's backlog at item 11 ("split or delete `state-compression`; audit its 102
non-bitmask uses"). That item's instinct was right and its scope was nearly right: the 102
non-bitmask uses are strata B+C, and **90 of those 102 (88%) are wrong**. The correction is that 12
of them are genuine and must be kept by id.

---

## What I could not determine

1. **Stratum A's true rate.** 14 of 61 sampled, 9/14 justified, 95% CI [39%, 84%] — so the true count
   of good uses in A is somewhere in 24–51. It does not change the recommendation (leave A alone
   either way), but it is why the headline range is 82–127 rather than something tighter. *What would
   settle it:* 20 more hand-reads drawn only from A.
2. **Whether the 3 unsure cases count.** All three hinge on the same judgement call — does an
   *optional* packing (`1681-d`'s exponent tuple, `count-beautiful-numbers`'s smooth-number product)
   count as the technique? I said no, on the grounds that a label should describe the solution people
   actually write. Counting them the other way moves the headline by 3 problems (~2 points), i.e. not
   at all. *What would settle it:* a policy decision, not more data.
3. **Whether `dp-optimization` (20 uses) has the same disease.** §14 flagged it with "the same
   smell" and I did not test it. Same method would work and it is 8× cheaper.
4. **Whether users search this phrase at all.** §14's open question 4 asked for CTR telemetry on
   searches containing "state compression". Still unanswered, and still the thing that would say
   whether 30% precision is costing anyone anything. Worth pulling from the v6 `result_open` data
   before spending re-annotation budget on stratum A.
