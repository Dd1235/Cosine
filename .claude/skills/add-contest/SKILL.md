---
name: add-contest
description: Add a whole contest (LeetCode weekly/biweekly, Codeforces round, AtCoder ABC/ARC) to the cosine corpus — stage it, solve and label the problems, embed, validate, bench, commit. Use when asked to add a contest, add the latest contest, or catch the corpus up on recent rounds.
---

# Adding a contest to the cosine corpus

`cosine` is a search engine over ~3,440 competitive-programming problems.
Records live in `data/problemset_llm/<judge>/<id>.json` and search matches their
`statement`, `tags` and `patterns`, so **the labels are the deliverable**. A
wrong label puts a stranger in front of someone searching a technique; a missing
one means the problem never answers a search it should.

Run from a checkout of `Dd1235/Cosine`. Nothing here needs an OpenAI key.

## 1. Stage

```bash
python3 scripts/ingest_contest.py https://leetcode.com/contest/weekly-contest-516/
python3 scripts/ingest_contest.py https://codeforces.com/contest/2248
```

This only appends to `Problems/urls_contests.txt` and, for Codeforces, merges
statements into the shared cache. It never commits.

**Q1 is skipped on LeetCode** (credit 3 — the warm-up, nearly always Easy). This
corpus is deliberately hard-focused; `credit` is used rather than the difficulty
label because it is fixed the moment the contest is created.

**Codeforces may queue instead of staging.** codeforces.com is Cloudflare-blocked
to scripts, statements come from the open-r1 HuggingFace dataset, and that
dataset lags live contests by weeks. Anything absent lands in
`data/pending_contests.json`; collect it later with `--retry-pending`. A problem
with no statement is nearly unsearchable, so nothing half-formed enters.

To find the latest LeetCode contest, the GraphQL `contest` query works and the
REST endpoint does not (`/contest/api/info/<slug>/` is Cloudflare-403):

```bash
curl -s -X POST https://leetcode.com/graphql -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0' -d '{"query":"query c($s:String!){contest(titleSlug:$s){title startTime} contestQuestionList(contestSlug:$s){titleSlug credit}}","variables":{"s":"weekly-contest-516"}}'
```

Weeklies are Sundays; biweeklies alternate Saturdays. A contest that has not run
yet still returns a record — check `startTime`.

## 2. Solve, then label

**Do not let a cheap model label a hard problem from the statement.** Measured:
for *Minimum Possible Maximum Waiting Time*, gpt-4.1-mini answered
`binary-search-answer + greedy + simulation` where the real solution binary
searches the answer and checks feasibility with a memoised DP. Rewriting the
prompt did not help — the model was the bottleneck.

Two paths that work, both free of API spend:

- **Claude subagents** (one per problem). Ask for the solution first, labels
  second.
- **Codex**, which is in this environment as `codexp` (personal account):

```bash
codexp exec --sandbox read-only -m gpt-5.6-luna \
  -c model_reasoning_effort='"high"' --skip-git-repo-check "$(cat prompt.md)"
```

Codex takes ~4–10 minutes per problem at high effort, so run it in the
background — a foreground call will hit a 10-minute tool timeout.

The prompt must, in this order:

1. **Solve the problem** and state the complexity. Check the derived algorithm
   against the worked samples; if it disagrees with a sample it is wrong.
2. **Name techniques from the solution**, not from the statement's words.
3. **Name every technique that genuinely solves it**, not only the setter's —
   someone searching "two pointers" should find a problem binary search also
   solves. But scaffolding inside a solution is not a label.

Ask for JSON: `solution`, `statement_summary` (one paragraph, 40–70 words, third
person, *including the constraint that decides the technique* — "with at most 16
requests"), `patterns`, `pattern_confidence`, `tags`, `notes`.

**Feed the model the canonical vocabulary and require verbatim values:**

```bash
python3 -c "import json;print(', '.join(sorted(json.load(open('data/pattern_taxonomy.json'))['canonical'])))"
```

Off-vocabulary labels are dead weight — 1,217 distinct names sit on 1,959 label
slots today and 912 are used exactly once, reachable by no query.

## 3. Run a skeptic pass

Feed the problems *and* the proposed labels back and ask a second run to refute
them. This is not optional; it has caught real errors every time.

Two traps to name explicitly in the skeptic prompt:

- **`binary-search-answer` is the corpus's biggest source of wrong labels** (277
  carriers, most wrong). It means the feasibility test is the interesting part —
  not "the answer is monotone so you could binary search it", and never when a
  direct linear solution is what anyone would write.
- **`bitmask-dp` vs interval DP.** Elevator Requests II (interval DP, m ≤ 1500)
  and III (Held-Karp, ≤ 16 requests) are a near-miss pair a careless annotator
  labels identically. The constraint decides it.

Take `keep` + `add`, drop everything refuted.

## 4. Write the records

```json
{
  "id": "leetcode-<slug>", "title": "...", "slug": "...", "platform": "leetcode",
  "source_url": "https://leetcode.com/problems/<slug>/",
  "source_topic": "LeetCode / Weekly Contest 516",
  "source_tags": [], "statement": "<the summary>",
  "tags": ["array", "..."], "patterns": ["most-central-first", "..."],
  "annotation": {"version": "problem-patterns-v1", "model": "<what you used>",
                 "generated_at_unix": 0, "pattern_confidence": {"label": 0.95}},
  "difficulty": "Medium"
}
```

Apply the family map so a specific label implies its broad one (`digit-dp` →
`dynamic-programming`, `sieve` → `number-theory`):

```python
import sys; sys.path.insert(0, "scripts")
from annotate_problem_urls import with_families
patterns = with_families(patterns, 12)
```

Keep the derivation in `data/analysis/<id>.json` — solution, what the skeptic
dropped, what it added. That directory is deliberately **not** indexed.

**LeetCode `source_tags` will be empty** — judge topic tags land days after a
contest. `python3 scripts/apply_source_tags.py --write` picks them up later.

## 5. Finish

```bash
python3 scripts/backfill_acceptance_rate.py --write   # metadata; no re-embed needed
npm run embed && npm run validate                      # embed FIRST — validate checks corpusHash
npm run bench
```

`npm run validate` must print `0 error(s)`.

**Gate on bm25 and tfidf, not dense or hybrid.** Dense embeddings depend on
batch composition, so inserting problems perturbs unrelated documents' vectors
by ~4e-3 cosine and flips near-ties — see `docs/plans.md` §2a. A dense/hybrid
slice move under ~0.05 after a corpus insertion is noise.

Also expect the benchmark to *under*-reward correct labels: relevant sets are
frozen id lists, so a newly-labelled correct problem scores as noise
(`docs/plans.md` §2b). Check what took a displaced slot before believing a drop.

Commit corpus + embeddings together — `corpusHash` covers title, statement, tags
and patterns, so those need `npm run embed` in the **same commit**. Metadata
(difficulty, acceptance rate) does not.

Commit messages here are **subject-line only** — no body, no trailers.
