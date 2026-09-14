# CSES estimated bands: reviewed fallback

The local candidate covers all400 current task IDs with Foundation, Standard,
Intermediate, Advanced and Expert. Two independent agents read the statements
and derived feasible solutions. Sixteen specialist concerns received additional
proof, author-code or finite-computation checks; original assessments remain
archived. Confidence and explicit overrides accompany every estimate.

The pilot contains30 development and30 held-out examples. Independent evaluation
judgments were initially made from statements without the assessors' bands,
production patterns or project count snapshot. Source-assisted follow-ups are
marked; a broad search surfaced unrelated third-party points, so absolute
blindness to every public proxy cannot be claimed. This is not human calibration.

The four frozen variants are reviewed baseline, smoothed completion, within-cohort
log volume, and combined adjustment. Completion prior strength is100 and the
statistical adjustment is capped at half a band, attenuated for sparse/recent
observations. Unknown cohorts disable volume. **All statistical adjustments are
currently disabled** because count meanings and task-level release cohorts were
not established. Therefore the variants coincide, and the predeclared tie rule
selects reviewed-only. No statistical benefit is claimed.

The formula froze before held-out evaluation. Development MAE is0.333 bands;
held-out MAE is0.467, with30/30 within one band and no two-band errors. Final
specialist overrides are individually recorded; they are not a tuned statistical
model. Public counts remain neutral evidence rather than being called submission
acceptance.

A pinned2022 inventory contains300 current tasks. A separate historical-presence
check spans36 of those and24 other pilot tasks, each stratum100% within one band.
The100-task complement is consistent with the official May2025 addition, but the
announcement does not enumerate IDs. This check cannot certify exact release
cohorts or authorize volume/newness adjustments. Those research questions remain
open before any future statistical variant.

Reproduction: `python3 scripts/evaluate_cses_difficulty.py --phase evaluate`,
`python3 scripts/publish_cses_bands.py` (dry-run), and the checks documented in
`data/cses/SPECIALIST_VERIFICATION.md`. The publisher requires unchanged frozen
inputs, complete double-review coverage, statement hashes and resolved specialist
flags. Local user verification remains required before production release.
