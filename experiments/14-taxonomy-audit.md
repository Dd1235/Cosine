# 14 — Taxonomy audit: the vocabulary is too small, and the models have been telling us so

**Date:** 2026-08-09
**Scope:** research only. Nothing under `data/` was modified.
**Corpus:** 3,461 problems · 10,304 pattern occurrences · 183 canonical labels, 182 aliases, 12 groups.

## Verdict

The vocabulary is **not** in good shape, and the centroid incident was not a one-off — it is
the shape of the whole thing. The single biggest problem: **the taxonomy is roughly half the
size the corpus needs, and the annotators have been writing the missing half in free text for
months.** 1,320 distinct non-canonical strings appear on 51.5% of all problems, accounting for
**2,570 of 10,304 label occurrences (24.9%)**. That is not model sloppiness — the cleanest proof
is that the *better* model drifts *more*: `gpt-4.1` (the contest annotator) writes 4.53 labels
per problem with only **61.6% canonical**, while `gpt-4.1-mini` writes 2.94 with **75.5%
canonical**. Upgrading the annotator increases drift, because it sees more techniques and the
vocabulary has no words for them. Independent confirmation comes from the judges themselves:
across every domain where Codeforces or LeetCode publishes its own tags, we carry the
corresponding technique on **only 33–56%** of the problems they tag (`data structures` 34%,
`geometry` 38–40%, `matrices` 33%, `fft` 42%, `trees` 53%, `strings` 43%, `number theory` 47%).
Two structural consequences follow: 145 problems carry **zero** canonical labels (CSES's entire
geometry section is in there — `cses-2191` Polygon Area, `cses-2192` Point in Polygon,
`cses-2193` Polygon Lattice Points — as is `cses-1732` Finding Borders, the archetypal KMP
problem, labelled only `prefix-function, kmp-algorithm`, neither of which is a word we know),
and 506 problems (14.6%) carry nothing but generic filler (`greedy`/`simulation`/`brute-force`/…).
The good news, and it is real: **no canonical label is unused**, every alias points at a
canonical target, and the alias mechanism itself works. This is an *additive* problem — the
existing vocabulary is mostly correct, there is just not enough of it, and ~570 drift
occurrences are pure synonyms of labels that already exist.

---

## Method

Everything below is computed directly from `data/problemset_llm/*/*.json` and
`data/pattern_taxonomy.json`. Three independent evidence sources:

1. **Drift labels as a wishlist.** When a model writes `prime-checking` 19 times, that is 19
   problems asserting a technique the vocabulary cannot name. Counts below are *lower bounds* —
   they only count problems where a model bothered to invent a name.
2. **Judge tags as a second opinion.** Codeforces publishes `source_tags` on 1,417 problems,
   LeetCode on 1,445. For each judge tag I mapped the family of our labels that should cover it
   and measured what fraction of the judge's tagged problems carry any of them.
3. **CSES section names as a curriculum.** 400 CSES problems arrive pre-sorted into
   Tree Algorithms / Range Queries / Geometry / Advanced Techniques / …, which is a ready-made
   statement of what a technique vocabulary should contain.

One bounded web check against [cp-algorithms](https://cp-algorithms.com/) — its article list is
the de-facto CP vocabulary — is used only to confirm that the names I propose are the names the
field actually uses, and to sanity-check which whole sections we are missing.

---

## Finding 1 — Missing labels

Ranked by number of problems that already carry a hand-invented synonym. Every count is a
**floor**: it counts only problems where the annotator wrote *something*, never problems where it
silently fell back to `greedy`.

| # | Label to add | Problems already naming it | Synonyms in use | Labelled instead | Evidence ids |
|---|---|---:|---|---|---|
| 1 | `lexicographic-order` | **48** | `lexicographic-order` 18, `lexicographical-order` 10, `-comparison` 8, `-ordering` 5, `-enumeration` 3, `-minimum` 2 | `greedy`, `sorting` | `codeforces-1279-e`, `codeforces-1913-f`, `cses-3225`, `cses-1757`, `atcoder-abc202-d` |
| 2 | `graph-modeling` | **38** | `graph-construction` 31, `graph-transformation` 4, `graph-representation` 3 | `dfs`, `bfs` | `codeforces-1284-f`, `codeforces-1368-g`, `cses-3158`, `codeforces-808-f`, `atcoder-abc143-e` |
| 3 | `state-space-bfs` | **35** | `state-space-search` 32, `state-space-exploration` 2 | `bfs`, `brute-force` | `codeforces-1257-b`, `codeforces-1886-f`, `cses-1670`, `leetcode-cat-and-mouse-ii` |
| 4 | `interval-scheduling` | **33** | `interval-scheduling` 14, `-covering` 6, `-coverage` 3, `-merging` 3, `-management` 3 | `greedy`, `sorting` | `codeforces-1725-f`, `codeforces-545-c`, `codeforces-7-b`, `leetcode-insert-interval`, `leetcode-maximum-score-of-non-overlapping-intervals` |
| 5 | `parity-argument` | **32** | `parity-check` 27, `parity-analysis` 2, `parity-invariant` 1, `graph-parity-check` 1 | `constructive-algorithm`, `greedy` | `codeforces-1622-f`, `codeforces-1807-d`, `cses-2078`, `cses-3357`, `leetcode-minimum-edge-toggles-on-a-tree` |
| 6 | `primality-test` | **29** | `prime-checking` 19, `prime-sieve` 6, `miller-rabin-primality-test` 1 | `brute-force`, `number-theory` | `cses-3396`, `cses-3423`, `codeforces-1844-b`, `codeforces-808-f`, `codeforces-161-e` |
| 7 | `divisor-enumeration` | **26** | `divisor-enumeration` 15, `factorization` 5, `divisor-counting` 4, `divisor-check` 3 | `brute-force`, `gcd` | `codeforces-762-a`, `codeforces-1618-c`, `codeforces-1475-a`, `atcoder-abc170-d`, `atcoder-abc172-d` |
| 8 | `manhattan-distance` | **19** | `manhattan-distance` 16, `coordinate-transformation` 2, `chebyshev-distance` 1 | `sorting`, `greedy` | `cses-3410`, `cses-3411`, `codeforces-620-a`, `codeforces-1245-d`, `codeforces-1920-f2` |
| 9 | `inversion-count` | **17** | `inversion-count` 12, `counting-inversions` 3, `inversion-counting` 2 | `fenwick-tree`, `greedy` | `cses-3140`, `cses-1162`, `codeforces-1760-e`, `codeforces-645-b`, `codeforces-1416-c` |
| 10 | `bipartite-graph` (2-colouring) | **15** | `bipartite-check` 9, `graph-coloring` 4, `coloring` 3 | `dfs`, `union-find` | `codeforces-19-e`, `codeforces-813-f`, `codeforces-1630-f`, `cses-3308`, `cses-1668` |
| 11 | `grid-dp` | **14** | `dp-on-grid` 8, `grid-dp` 6 | `dynamic-programming` | `leetcode-cherry-pickup`, `leetcode-dungeon-game`, `codeforces-722-e`, `codeforces-429-b` |
| 12 | `reachability` | **13** | `reachability` 4, `graph-reachability` 3, `connectivity-check` 3, `path-existence` 3 | `dfs`, `union-find` | `cses-2138`, `cses-1705`, `codeforces-766-d`, `codeforces-652-e`, `codeforces-402-e` |
| 13 | `string-dp` | **12** | `dp-on-strings` 7, `dp-on-substrings` 2, `dp-on-string` 2 | `dynamic-programming` | `codeforces-1446-b`, `codeforces-633-c`, `leetcode-wildcard-matching`, `atcoder-abc141-e` |
| 14 | `automaton-dp` | **12** | `state-machine` 7, `state-machine-dp` 4, `dp-on-automaton` 1 | `dynamic-programming` | `cses-1112`, `codeforces-247-e`, `leetcode-best-time-to-buy-and-sell-stock-iv`, `leetcode-valid-number` |
| 15 | `two-heaps` | **10** | `two-heaps` 8, `median-finding` 2 | `heap`, `ordered-set` | `leetcode-find-median-from-data-stream`, `leetcode-sliding-window-median`, `cses-1074`, `cses-1076` |
| 16 | `longest-common-subsequence` | **8** | `longest-common-subsequence` 6, `longest-common-prefix` 2 | `dynamic-programming` — `cses-3403`, *titled* "Longest Common Subsequence", carries `dynamic-programming, sequence-reconstruction` | `cses-3403`, `cses-3404`, `codeforces-1446-b`, `codeforces-346-b`, `codeforces-578-d` |
| 17 | `linked-list` | **8** | `linked-list` 2, `doubly-linked-list` 2, `pointer-manipulation` 2, `list-manipulation`, `node-insertion` | `hash-map`, `heap` | `leetcode-lru-cache`, `leetcode-lfu-cache`, `leetcode-all-oone-data-structure`, `leetcode-reverse-nodes-in-k-group`, `leetcode-rotate-list` |
| 18 | `subtree-size` / `subtree-query` | **8** | `subtree-query` 5, `subtree-size` 1, `subtree-size-calculation` 1 | `dfs`, `tree-dp` | `cses-1674`, `cses-2079`, `cses-1137`, `cses-1139`, `codeforces-600-e` |
| 19 | `extended-euclid` | **7** | `linear-diophantine-equation` 3, `extended-euclidean-algorithm` 2, `diophantine-equation` 2 | `gcd`, `constructive-algorithm` | `cses-3214`, `codeforces-743-c`, `codeforces-817-a`, `atcoder-abc186-e`, `leetcode-check-if-it-is-a-good-array` |
| 20 | Geometry primitives (a family, not one label) | **~12** | `line-segment-intersection` 2, `cross-product`, `shoelace-formula`, `polygon-area`, `pick-s-theorem`, `point-in-polygon-test`, `ray-casting`, `closest-pair-of-points`, `angle-calculation` 2, `slope-calculation` 2 | nothing canonical at all | `cses-2189`–`cses-2194` (six consecutive CSES geometry tasks) |

Also worth adding, smaller but each is a named technique with zero vocabulary:
`tree-hashing` (`cses-1700`, `cses-1701`), `matrix-rank` / `determinant` (`codeforces-1067-e`,
`codeforces-167-e`), `bitset` (`cses-1706`, `cses-1745`), `euler-totient` (`codeforces-284-a`,
`codeforces-1114-f`), `kadane` / `maximum-subarray` (`cses-1643`, 16 problems mention the phrase),
`prufer-code` (`cses-1134`, currently labelled `greedy, heap, degree-counting`),
`burrows-wheeler-transform` (`cses-1113`), `girth` (`cses-1707`).

**cp-algorithms corroboration.** Whole cp-algorithms sections have no representation here:
its *Geometry* section has 25 articles, we have 7 labels; its *Algebra* section names
Extended Euclid, Linear Diophantine, Primality tests, Euler's totient, Number of divisors,
Discrete log, Primitive root, Continued fractions — we name none of them. Its *Linear Algebra*
section (rank, determinant) has no label. Conversely, nothing cp-algorithms names is missing
from our graph/flow/string coverage except `Prüfer code`, `strong orientation`, and
`bipartite graph check` — those three families are in genuinely good shape.

---

## Finding 2 — Under-applied labels

The name exists; far too few problems carry it. Measured against the judges' own tags, which
are free and independent. `recall` = fraction of the judge's tagged problems that carry any
label from our matching family.

### The worst offenders, by number of problems affected

| Judge tag | Judge says | We label | Recall | Corpus-wide count of the whole family | Sample misses |
|---|---:|---:|---:|---:|---|
| CF `data structures` | 243 | 82 | **34%** | 709 | `codeforces-706-d`, `codeforces-1548-e`, `codeforces-293-e`, `codeforces-1609-f` |
| LC `hash-table` | 299 | 123 | **41%** | 158 | `leetcode-count-beautiful-substrings-ii`, `leetcode-find-latest-group-of-size-m` |
| CF `strings` | 137 | 59 | **43%** | 232 | `codeforces-1598-g`, `codeforces-552-e`, `codeforces-1624-d`, `codeforces-182-d` |
| CF `number theory` | 124 | 58 | **47%** | 441 | `codeforces-1475-g`, `codeforces-1950-d`, `codeforces-922-f` |
| CF `trees` | 122 | 65 | **53%** | 207 | `codeforces-1795-f` (r2400), `codeforces-1623-e` (r2500), `codeforces-1935-f` (r2800) |
| CF+CSES+LC geometry | 99 | 40 | **40%** | 102 | `cses-2191`, `cses-2192`, `cses-2193`, `cses-3410`, `leetcode-max-points-on-a-line` |
| CF `combinatorics` | 72 | 40 | **56%** | 313 | `codeforces-1477-f`, `codeforces-474-d`, `codeforces-489-d` |
| LC `ordered-set` | 48 | 21 | **44%** | 36 | `leetcode-the-skyline-problem`, `leetcode-exam-room`, `leetcode-132-pattern`, `leetcode-reverse-pairs` |
| CF `divide and conquer` | 35 | 20 | **57%** | 80 | `codeforces-1548-e`, `codeforces-1295-e`, `codeforces-337-d` |
| CF `flows` | 33 | 22 | 67% | 58 | `codeforces-1525-d`, `codeforces-808-f`, `codeforces-132-e` |
| CF `string suffix structures` | 31 | 14 | **45%** | 57 | `codeforces-932-g`, `codeforces-524-f`, `codeforces-825-f`, `codeforces-727-e` |
| CF `fft` | 24 | 10 | **42%** | 15 | `codeforces-1477-f`, `codeforces-993-e`, `codeforces-1439-d`, `codeforces-1654-h` |
| CF `matrices` | 21 | 7 | **33%** | 43 | `codeforces-497-e`, `codeforces-576-d`, `codeforces-865-g`, `codeforces-1286-d` |
| CF `graph matchings` | 20 | 11 | 55% | 61 | `codeforces-468-e`, `codeforces-1067-e`, `codeforces-1139-e` |
| CF `ternary search` | 15 | 7 | **47%** | **8** | `codeforces-939-e`, `codeforces-818-f`, `codeforces-431-e`, `codeforces-1427-h` |
| CF `chinese remainder theorem` | 15 | 7 | **47%** | **7** | `codeforces-993-e`, `codeforces-919-e`, `codeforces-338-d`, `codeforces-722-f` |
| LC `randomized` | 12 | 5 | **42%** | **5** | `leetcode-shuffle-an-array`, `leetcode-random-pick-with-weight`, `leetcode-insert-delete-getrandom-o1` |
| LC `suffix-array` | 6 | 1 | **17%** | 21 | `leetcode-longest-common-subpath`, `leetcode-sum-of-scores-of-built-strings` |
| CF `expression parsing` | 6 | 2 | **33%** | 7 | `codeforces-552-e`, `codeforces-64-b`, `codeforces-70-b` |
| LC `interactive` | 2 | 0 | **0%** | 13 | `leetcode-find-in-mountain-array`, `leetcode-guess-the-word` |

Three rows deserve emphasis because the *judge's tag count exceeds our entire corpus-wide use of
the label*: `ternary-search` (CF alone tags 15, we use it 8 times anywhere),
`chinese-remainder-theorem` (CF tags 15, we use it 7 times — all seven on CF problems),
`randomized-algorithm` (LC tags 12, we use it 5 times — all five on LC).

### Rare labels: 51 of 183 canonical labels are used ≤4 times

Not all of these are wrong — `berlekamp-massey`, `matroid-intersection`, `dominator-tree` are
genuinely rare. But several are core techniques that are simply not being applied:

| Label | Uses | Why the count is implausible |
|---|---:|---|
| `sparse-table` | **1** (`cses-1647`) | RMQ is a top-10 CP technique; LC alone tags 30 problems `binary-indexed-tree`, CF tags 243 `data structures`. Searching "sparse table" returns exactly one problem. |
| `tree-center` | 1 | Distinct from centroid, appears in every tree-diameter problem family |
| `virtual-tree` | 1 | Only `codeforces-2252-f`, the problem that triggered this audit |
| `heavy-light-decomposition` | 3 | CSES has a whole Path Queries family; only `cses-2134`, `codeforces-593-d`, `atcoder-abc294-g` |
| `tree-centroid` | 3 | `cses-1701`, `codeforces-2252-f`, `leetcode-minimum-height-trees`. The alias fix works — `centroid` now reaches 10 problems — but the label is applied 3 times, so the *technique* is still nearly unfindable. |
| `convex-hull` | 3 | 99 judge-tagged geometry problems in corpus |
| `subtree-dp` | 4 | `tree-dp` carries 65; the split is arbitrary |
| `flood-fill` | 4 | 275 problems mention grid/matrix |
| `bellman-ford` | 4 | 31 CF `shortest paths` problems |
| `merge-sort-tree` | 4 | LC tags 30 BIT problems, several are offline-order |
| `mo-algorithm` | 5 | `sqrt-decomposition` carries 21 |
| `min-cut` | 3 | 33 CF `flows` problems |

---

## Finding 3 — Bad vocabulary

### 3a. The drift is a long tail with a short, valuable head

| Bucket | Distinct labels | Occurrences | What it is |
|---|---:|---:|---|
| Drift used **once** | 931 | 931 | Model phrasing, mostly restating the problem (`peak-cell-condition`, `min-removal-to-trigger-condition`, `row-column-intersection`). **Not worth enumerating or fixing.** |
| Drift used **twice** | 178 | 356 | Same, mostly |
| Drift used **3–9×** | 178 | ~740 | The real signal — this is Finding 1's raw material |
| Drift used **≥10×** | 33 | ~543 | Techniques with no name, or synonyms of names we have |

So of 2,570 drift occurrences, roughly **1,280 sit on labels used 3+ times** — those are worth
acting on; the other half is irreducible noise from asking an LLM for free-text labels.

**~570 occurrences are pure synonyms of labels that already exist** and need no new vocabulary,
just alias entries. The biggest clusters:

| Existing canonical | Drift occurrences absorbable | The synonyms |
|---|---:|---|
| `counting` | 70 | `group-by` 13, `aggregation` 12, `frequency-array` 4, `frequency-analysis` 4, `pair-counting` 4, `prefix-counting` 4, `subsequence-counting` 4, `grouping` 7, `window-functions` 3, `order-by` 3 |
| `bit-manipulation` | 56 | `bit-counting` 10, `bitwise-xor` 9, `xor` 7, `binary-representation` 7, `xor-properties` 6, `bitwise-or` 5 |
| `brute-force` | 47 | `linear-scan` 10, `substring-enumeration` 10, `permutation-enumeration` 8, `brute-force-enumeration` 5, `digit-enumeration` 5 |
| `prefix-sum` | 36 | `prefix-processing` 10, `prefix-computation` 8, `2d-prefix-sum` 5, `prefix-frequency` 3 |
| `expression-parsing` | 36 | `string-parsing` 13, `parsing` 8, `expression-evaluation` 7, `stack-based-evaluation` 4, `recursive-parsing` 3 |
| `subset-dp` | 29 | `dp-on-subsets` 14, `subset-enumeration` 11, `state-enumeration` 3 |
| `combinatorics` | 29 | `combinatorial-enumeration` 13, `factorial-precomputation` 5, `binomial-coefficient` 3, `combinatorial-sum` 3 |
| `hash-map` | 25 | `hash-set` 10, `set` 5, `hash-set-lookup` 3, `set-operations` 3 |
| `gcd` | 21 | `gcd-computation` 6, `lcm` 4, `gcd-lcm-properties` 4, `prefix-gcd` 3, `lcm-computation` 3 |
| `kmp` | 17 | `prefix-function` 12, `kmp-algorithm` 3, `knuth-morris-pratt` 2 |
| `game-theory` | 20 | `minimax` 8, `optimal-strategy` 4, `combinatorial-game` 3, `optimal-play` 3 |
| `geometry` | 20 | `distance-calculation` 9, `distance-check` 4, `coordinate-geometry` 3, `angle-calculation` 2 |
| Assorted 1:1 misses | ~40 | `0-1-bfs` 3 (`01-bfs` is an alias but `0-1-bfs` is not), `disjoint-set` 3 (`disjoint-set-union` is), `all-pairs-shortest-path` 4, `binary-exponentiation` 3, `hierholzer-algorithm` 3, `condensation-graph` 3, `top-down-dp` 7, `binary-trie` 4 (`bit-trie` is), `interactive-problem` 4, `pruning` 14, `merge-sort` 5, `online-queries`/`online-query` 6 |

### 3b. Near-duplicates *inside* the canonical vocabulary

These are not drift — they are two canonical labels for one idea, splitting the index:

| Pair | Counts | Overlap | Diagnosis |
|---|---|---:|---|
| `dp-on-dag` / `dag-dp` | 47 / 2 | **0 problems** | Same three words rearranged. `dag-dp` should be an alias. |
| `tree-flattening` / `euler-tour` | 14 / 7 | 7 (Jaccard 0.50) | `euler-tour` is a strict subset — every euler-tour problem also carries tree-flattening. |
| `rolling-hash` / `string-hashing` / `rabin-karp` | 44 / 26 / 4 | Jaccard 0.03–0.09 | Three labels, one technique, and they almost never co-occur — a query hits one third of the set. |
| `modular-exponentiation` / `fast-exponentiation` | 28 / 13 | 5 | Same algorithm; the modulus is incidental. |
| `state-compression` / `bitmask-dp` | **163** / 100 | 59 | See below. |
| `minimum-spanning-tree` / `kruskal` | 9 / 14 | 5 | `kruskal` is used more than the concept it implements. |
| `bridges` / `articulation-points` | 10 / 5 | 3 | Alias `articulation-points-and-bridges` already exists but points only at one of them. |

### 3c. `state-compression` is a filler label and should be audited or removed

At **163 uses it is the 8th most common label in the corpus**, ahead of `hash-map`, `bfs` and
`union-find`. 122 of those 163 are LeetCode. 102 of them carry *no* bitmask label at all, and
the label lands on problems it has nothing to do with: `codeforces-343-a` Rational Resistance
(`fraction-representation, dp-on-rationals, state-compression, number-theory`), `cses-1746` Array
Description (`dynamic-programming, state-compression`), `cses-1159` Book Shop II. The model
appears to be using it to mean "this DP has states", which is true of every DP. This is the
mirror image of the recall problem: a search for `state compression` returns 163 mostly
irrelevant problems. `dp-optimization` (20 uses) has the same smell — it is an umbrella group
name being applied as if it were a technique.

### 3d. Umbrella group bugs

| Group | Bug |
|---|---|
| `combinatorics` | Three of ten members **do not exist**: `binomial-coefficient` and `pigeonhole-principle` are not canonical and not aliases; `catalan-numbers` is an alias, not a label. The group's expansion silently drops them. |
| `geometry` | Only 3 members (`convex-hull`, `rotating-calipers`, `line-sweep`) — omits `geometry` itself (28 uses), `orientation-test`, `rectangle-union-area`, `interval-union`. The umbrella for geometry excludes the geometry label. |
| `dp-optimization` | Omits the canonical `dp-optimization` (20 uses) and `state-compression`; includes `bitmask-dp` and `digit-dp`, which are DP *flavours*, not optimizations. |
| `string-algorithms` | Omits `z-function`, `string-matching`, `string-hashing`, `rolling-hash`, `palindrome`, `palindrome-dp`, `expression-parsing` — i.e. 7 of our 16 string labels, including the two most-used ones. |
| `graph-traversal` | Omits `multi-source-bfs`, `zero-one-bfs`, `grid-traversal`, `cycle-detection`, `tarjan`. |
| `number-theory` | Omits `modular-exponentiation` (28) and `fast-exponentiation` (13). |
| `flows-and-matching` | Omits `min-cost-flow`, `hungarian-algorithm`, `hall-theorem`. |
| `data-structures` | Omits `lazy-propagation`, `sqrt-decomposition`, `mo-algorithm`, `persistent-segment-tree`, `merge-sort-tree`, `li-chao-tree`, `link-cut-tree`, `implicit-treap`, `cartesian-tree`. |
| 5 groups | `shortest-path`, `geometry`, `number-theory`, `dp-optimization`, `combinatorics` are simultaneously group ids **and** canonical labels. `/api/patterns` therefore ships the same string as both a leaf and an umbrella. Not currently harmful (groups are browse-only) but it will bite if group expansion ever moves into query time. |

### 3e. What is *fine*

Worth saying plainly, since the brief asked: **0 canonical labels are unused**, **0 aliases point
at a non-canonical target**, **0 strings are both alias and canonical**, and the alias mechanism
does what it claims — after `normalize_patterns.js`, not a single known alias survives in the
corpus. The graph, flow, DP-optimization and advanced-string families are close to complete
against cp-algorithms. The problem is entirely one of *coverage and application*, not of
structural rot.

---

## What to do first

Ordered by problems affected per unit of work. "Affected" = problems that gain a searchable,
canonical technique word they do not have today.

| # | Action | Reason | Problems affected |
|---|---|---|---:|
| 1 | **Alias sweep: add ~90 aliases for the synonym clusters in §3a** | Zero risk, no new concepts, mechanical. `normalize_patterns.js` already exists to apply them. Cuts drift occurrences by ~22% in one commit. | **~570 occurrences across ~500 problems** |
| 2 | **Add `lexicographic-order`** | Largest single unnamed technique; 6 different spellings in use; "lexicographically smallest" is a query people type constantly | 48 (floor); 42 problems contain the word |
| 3 | **Audit `sparse-table` over CF `data structures` + LC `binary-indexed-tree` misses** | 1 use in 3,461 problems is a labelling failure, not a corpus fact. Start with the 166 CF and 10 LC misses | ~20–40 expected |
| 4 | **Add the geometry primitive family**: `polygon-area`, `point-in-polygon`, `segment-intersection`, `closest-pair`, `manhattan-distance`, plus `coordinate-geometry` as a catch-all | Geometry has 99 judge-tagged problems, 7 labels, 40% recall, and 6 consecutive CSES tasks with **zero** canonical labels | ~59 immediately (`cses-2189`–`2194`, `cses-3410`, `cses-3411`, `codeforces-620-a`, the 19 LC geometry misses) |
| 5 | **Alias `prefix-function` / `kmp-algorithm` / `knuth-morris-pratt` → `kmp`** | `cses-1732` "Finding Borders" — the canonical KMP problem — currently has **zero** canonical labels. `prefix function` is what editorials call it | 17, incl. `cses-1112`, `cses-1733`, `cses-2107`, `cses-1753` |
| 6 | **Add `graph-modeling`** | "Build a graph out of this" is a real, teachable technique and 38 problems already say so; today they read as `dfs` | 38 |
| 7 | **Add `interval-scheduling`** | Classic greedy taught by name everywhere; 5 spellings in use; distinct from the existing `interval-union` (5 uses) | 33 |
| 8 | **Add `primality-test` + `divisor-enumeration`** | Two of the three most common number-theory gaps; CF `number theory` recall is 47% | 55 combined |
| 9 | **Audit `tree-centroid`, `tree-center`, `heavy-light-decomposition`, `virtual-tree`, `subtree-dp` over the 60 CF `trees` misses and the 99 tree problems lacking a tree technique** | The audit's trigger. 224 problems say "tree"; only 56% carry a tree technique. Start with the rated-2400+ misses: `codeforces-1795-f`, `codeforces-1623-e`, `codeforces-1935-f`, `codeforces-1284-f` | ~30–60 |
| 10 | **Add `parity-argument`** | 32 problems already name it; parity is the single most common invariant in constructive CF problems, where `constructive-algorithm` (219 uses) is currently the only word available | 32 |
| 11 | **Split or delete `state-compression`; audit its 102 non-bitmask uses** | Precision fix, not recall: 163 uses, the 8th most common label, applied to problems with no state compression in them | 102 |
| 12 | **Fix the 12 group definitions in §3d** — 3 dead members, 8 groups with missing members | `/api/patterns` is the only surface where umbrellas work; `combinatorics` currently expands to 7 of its 10 declared members | Browse-page correctness, not search |
| 13 | **Alias `dag-dp` → `dp-on-dag`, `euler-tour` → `tree-flattening` (or merge), `fast-exponentiation` → `modular-exponentiation`** | Three canonical near-duplicates splitting the index with near-zero overlap | 22 |
| 14 | **Add `inversion-count`, `bipartite-graph`, `reachability`, `grid-dp`, `two-heaps`, `longest-common-subsequence`** | Six more named techniques with 8–17 problems each already spelling them out | ~85 combined |
| 15 | **Add the LeetCode-facing family: `linked-list`, `binary-tree-traversal`, `design`** | LC is 43% of the corpus; LC tags 20 `linked-list`/`doubly-linked-list`, 48 `design`, 18 `binary-tree`, and **we have no word for any of them**. `leetcode-lru-cache` is currently `hash-map, doubly-linked-list, cache-eviction` — every technique word non-canonical | ~70 |

A note on sequencing: **1, 5, 12, 13 need no LLM** — they are taxonomy edits plus
`normalize_patterns.js`. Items 2, 4, 6–8, 10, 14, 15 need the label added to
`pattern_taxonomy.json` and then the *drift spellings aliased onto it*, which retro-fits the
evidence problems for free. Only items 3, 9 and 11 require re-annotation, and per the standing
preference that should be scoped to the listed candidate ids, not the corpus.

Every item that changes indexed text requires `npm run embed` in the same commit.

---

## What I could not determine

1. **The true prevalence of each missing technique.** Every count in Finding 1 is a floor: it
   counts problems where a model wrote a synonym, never problems where it wrote `greedy` and
   moved on. `interval-scheduling` is named by 33 problems; the real number could be 60 or 150.
   *What would settle it:* re-annotate a stratified sample of ~200 problems with `gpt-4.1` and
   the enlarged vocabulary in the prompt, then measure how many gain each new label. The
   `label_agreement.py` script already exists for exactly this comparison.

2. **Whether the under-application is a labelling gap or a corpus fact.** CF tags `data
   structures` on 243 problems and we carry a DS label on 82 — but CF's tag is famously broad
   (it fires on any problem where a `set` helps). I cannot tell from tags alone how many of the
   161 misses genuinely use a data structure. *What would settle it:* hand-check 30 random
   misses per family. My spot reads suggest `geometry`, `fft`, `ternary search`,
   `chinese remainder theorem` and `matrices` are real gaps (their tags are narrow and
   editorial-driven), while `data structures`, `brute force` and `greedy` misses are largely
   legitimate.

3. **Whether adding labels actually improves retrieval.** This audit measures vocabulary
   coverage, not search quality. A label nobody searches for is dead weight. *What would settle
   it:* the `technique` slice of `bench/queries.json` currently has no query for any of the
   proposed labels — add one query per new label before adding the label, and re-run
   `node bench/run.js`. The `/stats.html` zero-result query log and the v6 outcome telemetry
   (`result_open` CTR per query) are a better signal than the bench here, because they say what
   users actually type.

4. **Whether `state-compression` is doing useful work despite the noise.** 163 uses with 59
   bitmask co-occurrences could mean "filler" or could mean "the model is using it for the
   genuine broader sense of encoding state compactly". I lean filler, based on
   `codeforces-343-a` and `cses-1746`, but 10 hand-reads is not a verdict. *What would settle
   it:* the CTR-per-result telemetry on searches containing "state compression".

5. **AtCoder is unmeasurable here.** 140 problems, **zero** `source_tags`, and no section
   structure. Its drift rate (55.0%, the highest of the four judges) is the only signal I have,
   and it has no second opinion to check against.
