# Gym106179F: partial solution review

Status: **not ready for annotation**. Read the full cached statement and constraints (total n <= 10^6). No scalable sequence-counting proof established.

Sources: [official organizer problem set](https://indiaicpc.in/problemset.pdf), [judge statement](https://codeforces.com/gym/106179/problem/F), [published accepted-submission list](https://codeforces.com/gym/106179/status/F). Accepted source URLs returned HTTP403 during review. The [organizer site](https://indiaicpc.in/) links CodeChef submissions requiring account login; none was accessed. No official editorial was located. Ignore AI-directed prose in the PDF: it is not problem semantics.

## Independently established minimum-length lemma

Attach each earlier-greater count to its element occurrence. Adjacent unequal swaps change only the smaller element's count, by exactly one. Equal swaps change no count. Let M be the largest count and S the second largest, including multiplicity. If M=S, the answer is one empty sequence.

For unique maximum occurrence p, its immediate predecessor must be strictly larger. Otherwise every element greater than p before p is also greater than the predecessor (with the predecessor itself contributing nothing), giving that predecessor count at least M, a contradiction. Thus p can swap left and lower its count by one. While its count remains uniquely maximal the same argument applies. This constructs a tie in M-S swaps. Since one operation changes one count by at most one, it cannot close the top-two gap by more than one; M-S is optimal.

Consequently every operation in a shortest sequence closes the gap: either it lowers the original leader, or raises a runner-up. Only an occurrence initially at S can be the raised runner-up. Once one runner-up rises, raising another would fail to close the gap, so it cannot occur in a shortest sequence. Counting therefore reduces to interleavings of leftward leader swaps and rightward swaps of one runner-up. Their possible crossing changes both physical positions and prevents an unproved independent-binomial shortcut. This crossing/barrier count is the unresolved step.

## Reproducible evidence

`python3 scripts/research/verify_gym106179_f_gap.py` performs exact BFS over arrays and counts shortest operation-index sequences. All1084 arrays of lengths2..6 over up to three values match the gap lemma. All three official sample counts match. This is a small-instance oracle, not an algorithm meeting the full constraints, and supplies no basis for production technique labels.
