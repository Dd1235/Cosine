# Solver brief — annotating one problem for cosine

`cosine` (/Users/dedeepya/Cosine) is a search engine over ~3,500 competitive-programming
problems. Search matches technique labels, so **the labels are the deliverable**.
Read-only on the repo. Write ONLY into the batch directory named in your task.

Your problem's fetched statement is `data/analysis/external-staging/<id>.json`
(`source_text`, `title`, `source_url`, and `kattis_difficulty` when known).
Canonical vocabulary = keys of `canonical` in `data/pattern_taxonomy.json`.

Do this in order:
1. **Solve it.** Derive the intended solution and its complexity; it must meet the
   stated limits. Check it against every sample. Write a small-n brute force
   (`verify_<slug>.py` in the batch directory) and cross-check on random inputs —
   several problems in this corpus had "obvious" reductions that passed all samples
   and were wrong. If you cannot derive a solution that meets the limits, set
   `"status": "unsolved"`, record what you established and where it breaks —
   **do not guess**. An honest `unsolved` beats a confident wrong label; it stays
   staged and shows as "not yet indexed".
2. **Read the constraints before naming anything.** They decide the technique.
3. **Name techniques from the solution you derived**, not from the statement's
   words. Every label verbatim from the canonical vocabulary; never invent a slug.
4. **Name every technique that genuinely solves it**, but scaffolding inside a
   solution is not a label.

Traps this corpus has measured: `binary-search-answer` (277 carriers, most wrong —
the feasibility test must be the interesting part, never "the answer is
monotone"); `dp-on-dag` (must be a DAG the problem hands you, not the DP's own
state graph); `dsu-on-tree` is small-to-large merging, not union-find.

Output `<batchdir>/<id>.json`:
```json
{"id":"<id>","status":"solved|unsolved",
 "solution":"3-6 sentences: algorithm, why correct, complexity (or what is established)",
 "solution_confidence":0.0-1.0,
 "statement_summary":"ONE paragraph, 40-70 words, third person, plain prose, what the problem ASKS incl. the deciding constraint; no markup/examples/IO format",
 "patterns":["canonical-label"],"pattern_confidence":{"label":0.9},"tags":["array"],
 "source_text_sha256":"<sha256 of the staging file's source_text exactly as stored>",
 "verify_script":"<batchdir>/verify_<slug>.py","notes":"uncertainties, or a technique missing from the vocabulary"}
```
No git, no npm, no edits under the repo.
