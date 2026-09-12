# Competition practice

Competitions live in the judge row: a `+ competition` chip at its end opens a
picker (arrow keys, Enter, Escape, click-outside), and each active competition
is a removable chip beside the judge chips. The chip is hidden until the
registry loads and while every collection is already active, so an unused
feature has no footprint. Selected collections form a union; judge, difficulty,
technique and progress filters intersect that union. A collection link restores
its selection through `contest=id,id`. Unknown collection IDs produce no
matches rather than broadening the search.

Adding or removing a competition is the one facet change that pushes a history
entry, so Back undoes it; typing and every other facet still replace the
current entry, because a debounced search box must not bury the previous page
under partial queries. Back and Forward re-apply the whole URL state through
one function, the same one the page boots from. Logout keeps competitions, as
it keeps judges. A `practice=1` link ignores `contest=` on load — practice
excludes the source contest by definition, so the pair can only be empty.

Collection membership is separate from judge and technique. Browse uses the
published problem order. Every card that belongs to a collection carries a
small competition tag (the collection's short name); clicking it adds that
collection. With a collection active, difficulty, tags, patterns and the CSES
provenance line start hidden until revealed; the statement and the "find
similar" / "practice this idea" links stay visible, because hiding them left
the feature's own follow-on actions unreachable. `:compare` is a ranker lens and
ignores collections; the status line says so. A resource can link an official
booklet, editorial, practice judge or non-coding round without becoming a
ranked problem. Counts distinguish searchable members from members still
awaiting statement or solution review, and a collection with no indexed
problems says so in the status line instead of reading as a broken filter.

Members arrive through `scripts/ingest_contest.py`, which reads a Kattis
problem-source page (`icpc.kattis.com` and `open.kattis.com`, where ICPC World
Finals and the Asia regionals are hosted) or an `open.kattis.com/contests/<id>`
page, stages every statement into `data/analysis/external-staging/`, and prints
a registry skeleton. CodeChef problems stage through the same adapter module.
Staging authorises nothing: a problem publishes only through
`scripts/publish_external.py`, which requires a derived solution, an independent
skeptic review pinned to the statement's hash, and canonical labels. A problem
that could not be solved stays staged and counts as "not yet indexed". Kattis
publishes a per-host difficulty score; it is stored as `kattis_difficulty`
metadata and shown in the detail line, never mapped onto a rating, a filter or
a sort. No Indian regional is hosted on Kattis, so that collection remains
resource-only until Gym- or CodeChef-hosted rounds are added.

Find similar keeps the source in the URL, excludes the source and verified
aliases, and filters before pagination. It retains the current facets and saved
list context. Practice this idea is a separate action: it removes the source
collection and saved-list scope, requests not-done practice, and excludes other
problems from the source contest. Explicit judge, difficulty and technique
choices remain. These are recommendations, not claims of PYQ membership.
Empty results offer an explicit reset action.

CSES uses its own five estimated bands and an explicitly selected personal band.
The preference is local for visitors and account-scoped for signed-in users.
There is no conversion from Codeforces rating. Unknown difficulty never passes
a rating filter and sorts last in either direction. Cards and Sheets share the
same formatter.

CSES publishes no difficulty, so every band is an estimate and is labelled as
one. Each of the 400 tasks got two independent solution reviews from the
statement; the band is their rounded mean, and fourteen specialist checks with
a proof or a finite computation override that mean where a review was unsafe.
Confidence states how much the two reviews agreed: high means both chose the
band, medium means they were one band apart, low means a specialist check
resolved it rather than agreement. It is agreement between reviews, not human
calibration, and it maps to no rating on any other judge. No count-based
adjustment is applied; the two public CSES counters are unlabelled, so every
statistical variant contributes zero. The method, the held-out numbers and the
open questions are in `experiments/19-cses-reviewed-bands.md`; the reviews,
snapshots, published bands and the publisher's gates are under `data/cses/`,
described in `data/cses/README.md`.

Sheets tokens stay memory-only; note content stays between the browser and
Google. Acknowledgements apply only to the values and mutation generation sent.
An edit during a sync triggers a later sync, and an account change invalidates
old callbacks. Google Sheets live writes are not part of the isolated preview
check; HTTP failures, in-flight edits and account switches have local tests.

The production similarity order remains reproducible dense cosine pending an
independently judged solution-transfer experiment. Technique explanations use
canonical family-collapsed labels, with structural overlap as the dense-disabled
fallback. Scores are not probabilities and are not displayed as such.

Research inspiration: [AlgoSimBench](https://arxiv.org/abs/2507.15378) uses
algorithmically different semantic distractors and attempted solutions;
[CPRet](https://arxiv.org/abs/2505.12925) separates problem-duplicate retrieval
from code-oriented tasks. Neither establishes that a new ranker improves this
application. Our held-out evaluation and slice gates remain required.

Local release gate: use the isolated PostgreSQL preview and verify the finished
UI before any production migration, push, merge or deployment. The regular
startup script runs configured migrations and must not be used for that preview.
