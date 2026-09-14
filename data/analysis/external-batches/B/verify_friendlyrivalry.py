"""
kattis-friendlyrivalry -- "Friendly Rivalry" (ICPC World Finals 2024)

Task: split 2n distinct planar points into two teams of exactly n each so that the
minimum Euclidean distance between a point of one team and a point of the other
(the bichromatic closest pair) is as LARGE as possible.  n <= 500, |coord| <= 1e9.

Derived solution
----------------
Answer is achieved at some pairwise distance d.  A partition has bichromatic
closest pair >= d iff every pair at distance < d is monochromatic, i.e. iff every
connected component of the threshold graph G_{<d} (all edges of length < d) lies
entirely in one team.  So d is feasible  <=>  the multiset of component sizes of
G_{<d} has a sub-multiset summing to exactly n (subset sum).

Merging components only shrinks the achievable-sum set, so feasibility is
monotone in d: we can sweep d upward instead of binary searching.  Components of
G_{<d} for every d are exactly the components of any MST of the complete graph
restricted to edges < d (cut property / minimum bottleneck tree), so only the
2n-1 MST edges matter, not all C(2n,2) of them.

Algorithm: Prim O((2n)^2) on squared distances -> sort the 2n-1 MST edges ->
Kruskal sweep with DSU; before unioning each distinct weight w, test subset sum
n over the current component sizes with a bitset DP; the largest w that passes is
the answer, and the DP's reconstruction gives the blue team.  Exact integer
squared distances throughout (max 8e18, fits in int64); sqrt only at output.

Complexity O(n^2 log n) time (Prim n^2, sort of n edges, <= 2n subset-sum checks
each O(n * n / 64)), O(n^2) or O(n) memory depending on Prim variant.
"""

import itertools, math, random, sys
from math import isqrt


# ---------------------------------------------------------------- helpers
def d2(p, q):
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


class DSU:
    def __init__(self, n):
        self.p = list(range(n))
        self.sz = [1] * n

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.sz[a] < self.sz[b]:
            a, b = b, a
        self.p[b] = a
        self.sz[a] += self.sz[b]
        return True


def subset_sum_pick(sizes, target):
    """sizes: list of ints.  Return list of indices summing to target, or None."""
    # dp[s] = index of the item that first reached sum s ; prev[s] = sum before it
    dp = [-1] * (target + 1)
    prev = [-1] * (target + 1)
    dp[0] = -2
    for i, v in enumerate(sizes):
        if v > target:
            continue
        for s in range(target, v - 1, -1):
            if dp[s] == -1 and dp[s - v] != -1 and dp[s - v] != -3:
                dp[s] = i
                prev[s] = s - v
        # mark items already used: standard 0/1 knapsack backward loop already
        # guarantees each item used once, no extra marking needed
    if dp[target] == -1:
        return None
    picked, s = [], target
    while s > 0:
        picked.append(dp[s])
        s = prev[s]
    return picked


def feasible(sizes, target):
    """Fast bitset feasibility for 0/1 subset sum."""
    mask = (1 << (target + 1)) - 1
    bits = 1
    for v in sizes:
        if v > target:
            continue
        bits |= (bits << v) & mask
        if (bits >> target) & 1:
            return True
    return (bits >> target) & 1 == 1


# ---------------------------------------------------------------- MST (Prim, O(V^2))
def prim_edges(pts):
    m = len(pts)
    INF = float('inf')
    best = [INF] * m
    bestfrom = [-1] * m
    used = [False] * m
    best[0] = 0
    edges = []
    for _ in range(m):
        u = -1
        for v in range(m):
            if not used[v] and (u == -1 or best[v] < best[u]):
                u = v
        used[u] = True
        if bestfrom[u] != -1:
            edges.append((best[u], bestfrom[u], u))
        pu = pts[u]
        for v in range(m):
            if not used[v]:
                w = d2(pu, pts[v])
                if w < best[v]:
                    best[v] = w
                    bestfrom[v] = u
    return edges


# ---------------------------------------------------------------- main solvers
def solve(pts, n, use_mst=True):
    """Return (answer_squared_distance, blue_team_indices_0based)."""
    m = len(pts)
    assert m == 2 * n
    if use_mst:
        edges = sorted(prim_edges(pts))
    else:
        edges = sorted((d2(pts[i], pts[j]), i, j)
                       for i in range(m) for j in range(i + 1, m))

    dsu = DSU(m)
    best_w = None
    best_state = None  # snapshot of roots at the best moment

    k = 0
    while k < len(edges):
        w = edges[k][0]
        # state = components of G_{< w}
        roots = {}
        for v in range(m):
            roots.setdefault(dsu.find(v), []).append(v)
        sizes = [len(g) for g in roots.values()]
        if feasible(sizes, n):
            best_w = w
            best_state = list(roots.values())
        while k < len(edges) and edges[k][0] == w:
            dsu.union(edges[k][1], edges[k][2])
            k += 1

    assert best_w is not None, "n>=1 => singletons are always feasible at the smallest weight"
    groups = best_state
    picked = subset_sum_pick([len(g) for g in groups], n)
    assert picked is not None
    blue = sorted(v for i in picked for v in groups[i])
    return best_w, blue


def min_cross(pts, blue_set):
    m = len(pts)
    return min(d2(pts[i], pts[j])
               for i in range(m) for j in range(m)
               if (i in blue_set) != (j in blue_set))


def brute(pts, n):
    """Exhaustive over all balanced partitions.  Returns best squared distance."""
    m = len(pts)
    best = -1
    bestblue = None
    for comb in itertools.combinations(range(1, m), n - 1) if n >= 1 else []:
        blue = set(comb) | {0}          # fix point 0 in blue, kills the x2 symmetry
        val = min_cross(pts, blue)
        if val > best:
            best, bestblue = val, sorted(blue)
    return best, bestblue


# ---------------------------------------------------------------- tests
def fmt(w):
    return "%.6f" % math.sqrt(w)


def run_samples():
    samples = [
        (2, [(0, 1), (1, 0), (1, 1), (0, 0)], "1.000000"),
        (2, [(0, 1), (-1, -1), (1, 0), (2, 2)], "2.236068"),
        (3, [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], "1.414214"),
    ]
    ok = True
    for n, pts, expect in samples:
        w, blue = solve(pts, n)
        got = fmt(w)
        # the reported value must also be the true min cross distance of our own output
        real = min_cross(pts, set(blue))
        agree = (got == expect) and (real == w) and len(blue) == n
        ok &= agree
        print(f"  n={n} expect={expect} got={got} blue(1-based)={[b+1 for b in blue]} "
              f"self-consistent={real == w} {'OK' if agree else 'FAIL'}")
    return ok


def run_random(trials=400, seed=1):
    rng = random.Random(seed)
    ok = True
    for t in range(trials):
        n = rng.randint(1, 4)
        m = 2 * n
        span = rng.choice([3, 4, 6, 40])
        pts = set()
        while len(pts) < m:
            pts.add((rng.randint(-span, span), rng.randint(-span, span)))
        pts = list(pts)
        w, blue = solve(pts, n)
        w2, _ = solve(pts, n, use_mst=False)          # all-pairs Kruskal variant
        bw, _ = brute(pts, n)
        real = min_cross(pts, set(blue))
        if not (w == bw == w2 == real and len(blue) == n):
            ok = False
            print("  MISMATCH", n, pts, "mst:", w, "allpairs:", w2, "brute:", bw, "real:", real)
            break
    if ok:
        print(f"  {trials} random small cases: solver == all-pairs variant == brute force, "
              f"and the reported value is the true min cross distance of the emitted team")
    return ok


def run_degenerate():
    ok = True
    cases = [
        (1, [(0, 0), (10 ** 9, 10 ** 9)]),                       # n=1, extreme coords
        (1, [(-10 ** 9, -10 ** 9), (10 ** 9, 10 ** 9)]),
        (2, [(0, 0), (0, 1), (0, 2), (0, 3)]),                   # collinear equal gaps
        (3, [(0, 0), (0, 1), (5, 0), (5, 1), (10, 0), (10, 1)]), # three far pairs, n odd -> must split a pair? no: 2+? 
        (2, [(0, 0), (1, 0), (100, 0), (101, 0)]),
    ]
    for n, pts in cases:
        w, blue = solve(pts, n)
        bw, _ = brute(pts, n)
        real = min_cross(pts, set(blue))
        good = (w == bw == real)
        ok &= good
        print(f"  n={n} pts={pts} -> {fmt(w)} blue={[b+1 for b in blue]} "
              f"brute={fmt(bw)} {'OK' if good else 'FAIL'}")
    # overflow sanity: largest possible squared distance fits in int64
    big = (2 * 10 ** 9) ** 2 * 2
    print(f"  max squared distance {big} < 2^63-1 = {2**63-1}: {big < 2**63 - 1}")
    return ok


def run_timing():
    rng = random.Random(7)
    n = 500
    pts = set()
    while len(pts) < 2 * n:
        pts.add((rng.randint(-10 ** 9, 10 ** 9), rng.randint(-10 ** 9, 10 ** 9)))
    pts = list(pts)
    import time
    t0 = time.time()
    w, blue = solve(pts, n)
    t1 = time.time()
    print(f"  n=500 (worst case) MST-based solve: {t1-t0:.2f}s in CPython, "
          f"answer {fmt(w)}, |blue|={len(blue)}")
    # clustered worst case: many equal distances
    pts2 = []
    for i in range(2 * n):
        pts2.append((i % 50 * 1000, i // 50 * 1000))
    t0 = time.time()
    w2, blue2 = solve(pts2, n)
    t1 = time.time()
    print(f"  n=500 grid (massive ties): {t1-t0:.2f}s, answer {fmt(w2)}, |blue|={len(blue2)}")
    return True


if __name__ == "__main__":
    print("samples:");     s1 = run_samples()
    print("degenerate:");  s3 = run_degenerate()
    print("random vs brute force:"); s2 = run_random()
    print("timing:");      s4 = run_timing()
    print("ALL OK" if (s1 and s2 and s3 and s4) else "FAILURES")
