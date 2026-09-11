# Solution-transfer similarity study

1. `node bench/similarity/prepare.js experiments/similarity-v1` freezes 40
   stratified seeds and pools the dense, technique, 50/50 hybrid, potential
   semantic-distractor, and random candidates. Preparation refuses stale
   embeddings and existing output directories.
2. Give only `blind-review-packets.json` to two independent reviewers. These
   packets contain corpus statements and source URLs, **not verified solutions**.
   Reviewers must obtain the complete statement, constraints and solution before
   grading. Production labels, ranks, scores and source algorithms are withheld.
3. Grade each pair: 0 unrelated, 1 broad prerequisite only, 2 substantial solution
   transfer, 3 essentially the same core technique/invariant. Record adjudicated
   judgments as `{seed,candidate,grade,reviewers:["reviewer-a","reviewer-b"],
   evidence:["verified solution URL or reasoning"]}`. Resolve disagreements;
   never fill missing grades with zero.
4. Independently confirm solution-family and duplicate-family separation between
   development and held-out test. Generated family labels are only provisional.
   Record final family IDs and verify no family occurs in both splits; do not
   tune while examining held-out relevance. Set `familySplitVerified:true` and
   `frozen:true` in judgments only after this review and development tuning.
5. `node bench/similarity/evaluate.js experiments/similarity-v1` reports coverage,
   held-out metrics, paired bootstrap intervals and hard/sparse slices. nDCG's
   ideal ranking is over the judged pool. Unjudged top results have no metric.

The initial study has **no judgments** and cannot authorize a ranking change.
The solution-signature arm requires separately verified solution signatures and
must add its candidates to the review pool before judgments freeze. This scaffold
compares only the three available baselines. A production promotion still requires
+0.05 held-out nDCG@10, +0.10 P@5, confidence inspection, no material hard/sparse
regression, and warm similarity p95 below 20 ms on a recorded environment. The
script intentionally does not turn incomplete evidence into an automatic pass.

## Where this stopped (2026-09-11)

The scaffold, the frozen 40-seed pool and the fetched evidence are done. What is
missing is the part a script cannot produce:

- `judgments.json` is `{frozen:false, familySplitVerified:false, judgments:[]}`.
  **Zero human judgments exist**, so `evaluate.js` reports `metrics: null` for
  every seed. That is the script refusing to score, not a bug — do not "fix" it.
- `review_c.json` is one reviewer (`independent_evaluator_c`, 97/97 items graded)
  and is explicitly `partial_evidence_researched_not_promotion_ready`. Step 2
  wants **two** independent reviewers before adjudication.
- `evidence-b/` holds 833 statements fetched from the official sites on
  2026-09-11, each with `statement_sha256` and `observed_at`. Re-fetching is the
  expensive part of this study; treat that directory as the asset.

To resume: get a second reviewer over `blind-review-packets.json`, adjudicate
into `judgments.json`, verify the family split, set both flags true, then re-run
`evaluate.js`. Promotion still needs +0.05 held-out nDCG@10, +0.10 P@5, no
material hard/sparse regression and warm p95 under 20 ms.
