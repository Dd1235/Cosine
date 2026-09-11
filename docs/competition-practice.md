# Competition practice

Choose collections from the competition control. Selected collections form a
union; judge, difficulty, technique and progress filters intersect that union.
A collection link restores its selection through `contest=id,id`. Unknown
collection IDs produce no matches rather than broadening the search.

Collection membership is separate from judge and technique. Browse uses the
published problem order. Cards hide difficulty and technique hints until
revealed. A resource can link an official booklet, editorial, practice judge or
non-coding round without becoming a ranked problem. Counts distinguish searchable
members from members still awaiting statement or solution review.

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
