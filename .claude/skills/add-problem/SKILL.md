---
name: add-problem
description: Add one or a few individual problems to the cosine corpus, by URL or by name, from LeetCode, Codeforces, AtCoder or CSES — including the "here is my solution, no API calls" path. Use when asked to add a specific problem rather than a whole contest.
---

# Adding a single problem to the cosine corpus

For a whole contest use `add-contest` instead. This is the path for one problem,
a handful, or a problem that belongs to no contest at all (CSES).

`cosine` searches ~3,440 problems by `statement`, `tags` and `patterns`, so the
labels are the deliverable. Records live in
`data/problemset_llm/<judge>/<id>.json`.

## Getting the statement

**LeetCode** — GraphQL, and check the category:

```bash
curl -s -X POST https://leetcode.com/graphql -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0' \
  -d '{"query":"query q($s:String!){question(titleSlug:$s){title difficulty content categoryTitle topicTags{slug}}}","variables":{"s":"two-sum"}}'
```

**`categoryTitle` must be `Algorithms`.** The problemset is three catalogues
sharing one URL shape — Database, Shell and JavaScript problems are not DSA and
must not enter. `scripts/annotate_problem_urls.py` enforces this and refuses
before any model call; 31 such records had to be removed once.

**Codeforces** — codeforces.com is Cloudflare-403 to scripts. Two ways in:

- The open-r1 HuggingFace dataset (free, but lags live contests by weeks).
- Tavily `extract` with `extract_depth: "advanced"` — the basic depth stops
  before the statement. Use the **`/contest/<id>/problem/<X>`** URL form, not
  `/problemset/problem/...`: the latter drops `<ul>` content, which silently
  cost 2254F its XOR operation. Verify the extracted text contains
  `time limit per test`; if it does not, the extractor missed the statement.

Never reuse `fetch_codeforces.py` / `fetch_codeforces_named.py` for a one-off —
both **truncate** `data/cache/codeforces_statements.json`. `ingest_contest.py`
merges instead.

**AtCoder / CSES** — `scripts/annotate_problem_urls.py` handles both from a URL.

## Labelling

Solve first, label second, and never label a hard problem from its statement
alone. Use Claude subagents or codex (`codexp exec --sandbox read-only -m
gpt-5.6-luna -c model_reasoning_effort='"high"'` — background it; it takes
minutes). Feed the model the canonical vocabulary and require verbatim values:

```bash
python3 -c "import json;print(', '.join(sorted(json.load(open('data/pattern_taxonomy.json'))['canonical'])))"
```

Then run a **skeptic pass** over the proposed labels. Name the two traps:
`binary-search-answer` means the feasibility test is the interesting part (277
carriers, most wrong), and the bitmask-vs-interval-DP near-miss is decided by
the constraint, not the wording.

### When the user supplies the solution

Perfectly good, and cheaper than any model: read their code, name the techniques
from it, and record the code in `data/analysis/<id>.json`. This is how
`codeforces-2042-d` was added — two ordered-set sweeps, labelled from the C++.
No API calls at all.

## Writing it

Follow the shape in `add-contest` step 4, apply `with_families(patterns, 12)`,
and keep the derivation in `data/analysis/<id>.json` (not indexed).

Watch the **12-label cap** — `scripts/apply_review.js` warns and skips past it,
so a 13th label vanishes silently. If a problem is at the cap and genuinely
needs a new label, trim a label with one corpus-wide use rather than dropping
the new one.

If the technique has no canonical label, add it to `data/pattern_taxonomy.json`
— **and give it carriers in the same commit.** A canonical label nothing carries
is a promise the index cannot keep. Check first whether it wants to be an alias
of something that exists instead:

```bash
node scripts/normalize_patterns.js --write   # after editing the taxonomy
```

## Finishing

```bash
npm run embed && npm run validate    # embed FIRST — validate checks corpusHash
npm run bench
```

`0 error(s)` required. Gate on **bm25 and tfidf**; dense and hybrid shift when
the corpus grows for reasons unrelated to the change (`docs/plans.md` §2a).

Corpus and embeddings go in the **same commit** when indexed text changed —
`corpusHash` covers title, statement, tags and patterns, not metadata. Commit
messages are subject-line only, no body, no trailers.

## Checking it worked

Search for the technique you just added and confirm the problem comes back:

```bash
node -e '
const {loadProblems}=require("./server/data");const {Bm25Index}=require("./server/search/bm25");
const {expandQuery}=require("./server/search/query_expand");
const i=new Bm25Index(loadProblems());
i.search(expandQuery("mo algorithm").query,5).hits.forEach((h,n)=>console.log(n+1,h.problem.id));'
```
