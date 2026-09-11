# CSES difficulty evidence

`public_counts.json` snapshots the public list. Its two numbers remain neutrally named: the list does not label them, and individual task statistics require login. Third-party usage suggests distinct solvers / attempting users, but this is not verified first-party semantics and is **not submission acceptance**. Release cohorts are unknown; task IDs and annotation dates are not release dates.

`statements/` contains timestamped task text and SHA-256 hashes, fetched from the actual task pages by `scripts/collect_cses_evidence.py`. Diagrams need separate visual review where they carry essential information; HTML-to-text does not reproduce diagrams. Existing production summaries and patterns are not an independent solution review.

Bands: 1 Foundation (direct simulation/basic observation), 2 Standard (one standard technique), 3 Intermediate (nontrivial insight or combination), 4 Advanced (specialized technique or substantial composition), 5 Expert (demanding optimization/proof/implementation). These are CSES-only pedagogical estimates, never cross-judge ratings.

Publication requires two separately performed assessments, solution/complexity rationale grounded in statements, independent pilot evaluation, and adjudication. A reviewer must not see another review or public counts. A generated template is not a completed review. Claude Opus authentication was unavailable during initial collection; no Opus review is claimed.

Current state: all400 tasks have two independent agent assessments, with14 specialist supplements plus two independently verified pilot solutions resolving the16 first-pass flags. Original assessments remain immutable. The60-task pilot has an independent evaluation split30/30. The formula froze before held-out evaluation: review-only won by the predeclared tie rule because inadmissible statistics contributed zero. Held-out agreement within one band is30/30; mean absolute error is0.467 bands. This is agent-review agreement, not a human calibration claim. Source-assisted evaluator follow-ups are transparently marked; a search surfaced unrelated third-party scores which were not used, so perfect blindness to all public proxies cannot be claimed.

`published_bands.json` and the400 corpus metadata records are the **local review candidate**, using the rounded mean of the two assessments plus explicit proof-based specialist overrides. `publish_cses_bands.py` validates coverage, hashes and unresolved discrepancies; dry-run is the default. No statistic-based adjustment is enabled. The source-count meanings are still unverified, so all four numerical variants coincide; this is absence of admissible evidence, not evidence that completion statistics are useless.

`historical_inventory.json` pins a2022 author inventory containing exactly300 current tasks. The remaining100 are a separate historical-presence stratum, not verified per-task release dates. `cross_inventory_check.json` reports sensitivity across these strata (36older,24other pilot tasks, all within one band). This does not replace a verified release-cohort experiment for a future statistical model. Production release remains subject to the user's local review.

Run `python3 scripts/evaluate_cses_difficulty.py --phase evaluate`, `python3 scripts/publish_cses_bands.py`, and `python3 -m unittest discover -s tests -p test_cses_difficulty_experiment.py` to reproduce the gates. Specialist checks are documented in `SPECIALIST_VERIFICATION.md`.

The [official May 2025 update](https://cses.fi/blog/text/3613), dated 2025-05-11, confirms 100 additions bringing the total to 400. It does not enumerate their IDs. Model analyses can require solving a task first. This evidence establishes the release event, not per-task cohort membership.
