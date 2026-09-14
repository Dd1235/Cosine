# Does giving an agent a published solution improve its labels?

Six problems, LeetCode Weekly 519 and Biweekly 191, labelled three ways on
2026-09-14. The question was whether fetching an existing solution first —
which is what the Kattis regional batches did — is worth the effort on contest
problems.

**It is not. The model was the bottleneck, not the source material.**

## Setup

A useful accident made this a controlled comparison. The doocs/leetcode
community repo carries accepted code for four of the six and empty stubs for
both Count Shadow Pairs problems, which were too new.

| arm | agent | input | problems |
|---|---|---|---|
| A | Opus | statement + accepted code | the four with solutions |
| B | Opus | statement only | the same four |
| C | Opus | statement only | the two with no published solution |

`gpt-4.1` had already labelled all six through the normal contest pipeline
(`annotate_problem_urls.py --model gpt-4.1`). No agent could see those labels,
and arm B was barred from the solution files and the web.

## Result

Arms A and B agreed on 10 of 12 labels and derived the same time and space
complexity on all four problems. Arm A self-reported that reading the solution
changed its answer on three of four; the control shows that was mostly
illusory, because arm B reached the same place without it.

Against gpt-4.1 on those four problems:

| | gpt-4.1 | Opus |
|---|---|---|
| off-vocabulary labels invented | 5 | 0 |
| wrong technique claims | 4 | 0 |

The two errors that would actually misdirect a searcher:

- **count-subarrays-with-distant-sums** — gpt-4.1 said `two-pointers`,
  `hash-map`, `brute-force`. The accepted solution is a Binary Indexed Tree
  over sorted prefix sums; none of those three appear in it and `fenwick-tree`
  was missed entirely. Negative values are exactly what breaks window
  monotonicity, so `two-pointers` points at the one approach that cannot work.
- **minimum-days-to-score-exactly-n-points** — gpt-4.1 added `greedy` and
  `brute-force` to a bottom-up unbounded knapsack over triangular numbers.

One point against arm A: it dropped `segment-tree` alongside `fenwick-tree`,
reasoning from what the code literally does. The taxonomy's own family rule
(`(^|-)(segment-tree|fenwick-tree)($|-)` → `segment-tree`) implies it, so the
arm holding the solution missed a label the pipeline adds automatically.

## The Count Shadow Pairs pair, where gpt-4.1 was furthest off

The two problems differ in one clause. Part I forbids an index `k` between
with `nums[k] < nums[i]`, which depends only on the left endpoint. Part II
forbids `nums[i] < nums[k] < nums[j]`, which depends on both. A monotonic
stack solves I and provably fails II:

    nums = [5, 4, 4, 5, 5, 2, 2, 5, 4]   stack says 8, truth is 10

gpt-4.1 labelled both `monotonic-stack` and missed `divide-and-conquer` and
`fenwick-tree` on II. Arm C found the split, and its brute-force checks are
kept as `scripts/research/verify_count_shadow_pairs_{i,ii}.py` (5,065 and
5,447 cases; both re-run here before the labels were applied).

## Scope

This holds for contest-grade problems, where the statement is short and the
constraints pin the approach. It should not be read as covering the Kattis
regionals at 8.0–9.2 difficulty, where a published solution genuinely carried
the derivation — but note that those came with their own failure mode, recorded
in `docs/plans.md` §4a: proposals making false claims about their own source.
