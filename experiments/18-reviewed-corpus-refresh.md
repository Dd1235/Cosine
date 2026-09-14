# Reviewed competition refresh — 2026-09-11

The served corpus grows from 3482 to 3506 records: seven CF2260 tasks, seven
recovered CF tasks, four ICPC India prelim tasks from Gym106179, five IICPC
Codefest tasks from the official CodeChef mirror, and World Finals2024 Billboards
from Kattis. Every published addition has a full statement, a derived feasible
solution, and an independent skeptic review in `data/analysis/*-review.json`.
These are Codex reviews; the requested Claude CLI was unavailable because it was
not logged in. No Opus provenance is claimed.

CF metadata was checked against the official problemset API on the observation
date. All15 previous pending ratings were backfilled earlier. CF2260 and Gym
ratings remain unknown. No cross-judge conversions are made. Seven recovered
skip entries and two already-reviewed stale entries (2042D,1998D) were reconciled.
Missing statements and missing ratings retain separate worklists.

The official LeetCode GraphQL discovery found Weekly518 and Biweekly190 already
covered by the existing credit-based exclusions and anchors. Weekly519 and
Biweekly191 had not run. No LC records or intentional exclusions changed.

The matching singleton embedding artifact preserves **all3482 existing vectors
bit-for-bit** after inserting24 unrelated records. The saved text benchmark is
`bench-2026-09-11T07-13-11-503Z.json`; compare against the unchanged-corpus
singleton baseline `bench-2026-09-11T06-52-47-400Z.json`. Corpus growth is a separate
experiment from embedding recipe and ranker changes. Existing vocabulary drift
remains a validator warning; there are zero structural errors.

The CodeChef adapter reads actual structured problem components instead of the
editor template in `body`. The Kattis adapter isolates the balanced statement
container, excluding account metadata. Both fail closed on incomplete pages and
leave unknown difficulty null. Staging does not authorize publication.

Sources: [Codefest mirror](https://www.codechef.com/CDFESTMR2026),
[ICPC India official booklet](https://indiaicpc.in/problemset.pdf),
[Gym106179](https://codeforces.com/gym/106179),
[World Finals2024 archive](https://icpc.kattis.com/problem-sources/ICPC%20World%20Finals%202024),
[CF2260 setter editorial](https://codeforces.com/blog/entry/156529).
