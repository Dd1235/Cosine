"""Verify the published solution for Kattis 'latinsquare' (2019 ICPC Asia Danang, L).

Problem: an n x n grid is partially filled with k distinct values, each used
exactly n times with no repeat in any row or column (so each value already
occupies a full transversal: exactly one cell per row and one per column).
Complete it to a Latin square, or print NO.

Published solution (transcribed below as `capghep` / `solve_published`):
for every value v in 1..n that does not already appear, build the bipartite
graph rows -> columns with an edge (i,j) for every still-empty cell, find a
maximum matching with Kuhn's algorithm, and write v into the matched cells.

Why it is always possible: since each of the k pre-filled values sits once in
each row and once in each column, every row and every column has exactly k
filled cells, so the empty-cell graph is (n-k)-regular bipartite.  A regular
bipartite graph satisfies Hall's condition and therefore has a perfect
matching, and deleting one perfect matching leaves a (n-k-1)-regular graph.
So the greedy peeling never fails and the answer is never NO -- which is why
the published code has its `cout << "NO"` branch commented out.

Checks below:
  1. the statement's sample;
  2. exhaustive over every legal (n,k) instance for n <= 4 (every Latin square
     of that order, every subset of values kept) -- output is always a valid
     completion and "NO" is never required;
  3. randomised instances up to n = 100 (the stated limit), including k = 0 and
     k = n, checking regularity of the empty graph, perfect matchings at every
     step, and validity of the completed square;
  4. a cross-check that the published Kuhn variant (which keeps its `visited`
     marks across augmentations inside one phase) really returns the maximum
     matching, by comparing with an independent textbook Kuhn on random
     bipartite graphs.
"""
import random
import sys
from itertools import permutations

sys.setrecursionlimit(100000)


# ---------------------------------------------------------------- published
class Published:
    """Faithful transcription of latinsquare.cpp."""

    def __init__(self, n):
        self.n = n
        self.m = n
        self.a = [[] for _ in range(n + 1)]
        self.kt = [0] * (n + 1)
        self.stk = [0] * (n + 2)
        self.top = 0
        self.match = [0] * (n + 1)
        self.link = [0] * (n + 2)
        self.found = False

    def dfs(self, u):
        for v in self.a[u]:
            if self.kt[v] == 0:
                self.kt[v] = 1
                self.top += 1
                self.stk[self.top] = v
                if self.match[v] == 0:
                    self.found = True
                else:
                    self.dfs(self.match[v])
                if self.found:
                    self.match[v] = u
                    return

    def capghep(self):
        n, m = self.n, self.m
        nlink = n
        for i in range(1, n + 1):
            self.link[i] = i
        for j in range(1, m + 1):
            self.match[j] = 0
        while True:
            old = nlink
            for i in range(1, self.top + 1):
                self.kt[self.stk[i]] = 0
            self.top = 0
            i = nlink
            while i >= 1:
                self.found = False
                self.dfs(self.link[i])
                if self.found:
                    self.link[i] = self.link[nlink]
                    nlink -= 1
                i -= 1
            if old == nlink:
                break
        return n - nlink


def solve_published(n, k, grid):
    """grid: 1-indexed (n+1)x(n+1) list of lists, 0 = empty.  Returns (ok, grid)."""
    res = [row[:] for row in grid]
    used = [False] * (n + 2)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if res[i][j]:
                used[res[i][j]] = True
    ok = True
    for val in range(1, n + 1):
        if used[val]:
            continue
        p = Published(n)
        for i in range(1, n + 1):
            p.a[i] = [j for j in range(1, n + 1) if res[i][j] == 0]
        size = p.capghep()
        for j in range(1, n + 1):
            i = p.match[j]
            if i:                      # C++ would write res[0][j], a no-op cell
                res[i][j] = val
        used[val] = True
        ok = ok and size == n
    return ok, res


# ---------------------------------------------------------------- reference
def kuhn_reference(n, adj):
    """Independent textbook Kuhn (visited reset per augmentation)."""
    match = [0] * (n + 1)

    def try_k(u, seen):
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                if match[v] == 0 or try_k(match[v], seen):
                    match[v] = u
                    return True
        return False

    size = 0
    for u in range(1, n + 1):
        if try_k(u, set()):
            size += 1
    return size, match


# ---------------------------------------------------------------- checking
def is_latin(n, g, original):
    for i in range(1, n + 1):
        if sorted(g[i][1:n + 1]) != list(range(1, n + 1)):
            return False
    for j in range(1, n + 1):
        if sorted(g[i][j] for i in range(1, n + 1)) != list(range(1, n + 1)):
            return False
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if original[i][j] and original[i][j] != g[i][j]:
                return False
    return True


def all_latin_squares(n):
    rows = [p for p in permutations(range(1, n + 1))]
    out = []

    def rec(sq):
        if len(sq) == n:
            out.append([list(r) for r in sq])
            return
        for r in rows:
            if all(all(r[j] != s[j] for j in range(n)) for s in sq):
                rec(sq + [r])
    rec([])
    return out


def make_instance(n, square, keep):
    """keep: set of values retained; others blanked."""
    g = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(n):
            if square[i][j] in keep:
                g[i + 1][j + 1] = square[i][j]
    return g


def check_regular(n, g):
    """Empty-cell graph must be (n-k)-regular."""
    rowdeg = [sum(1 for j in range(1, n + 1) if g[i][j] == 0) for i in range(1, n + 1)]
    coldeg = [sum(1 for i in range(1, n + 1) if g[i][j] == 0) for j in range(1, n + 1)]
    return len(set(rowdeg)) == 1 and set(rowdeg) == set(coldeg)


def main():
    random.seed(20190413)

    # ---- 1. sample -----------------------------------------------------
    n, k = 3, 1
    g = [[0] * 4 for _ in range(4)]
    for i, row in enumerate([[2, 0, 0], [0, 2, 0], [0, 0, 2]]):
        for j, v in enumerate(row):
            g[i + 1][j + 1] = v
    ok, out = solve_published(n, k, g)
    print("sample  ok=%s  grid=%s" % (ok, [out[i][1:4] for i in range(1, 4)]))
    assert ok and is_latin(3, out, g)

    # ---- 2. exhaustive n <= 4 -----------------------------------------
    for n in range(1, 5):
        squares = all_latin_squares(n)
        total = 0
        for sq in squares:
            vals = list(range(1, n + 1))
            for mask in range(1 << n):
                keep = {vals[b] for b in range(n) if mask >> b & 1}
                g = make_instance(n, sq, keep)
                assert check_regular(n, g), (n, g)
                ok, out = solve_published(n, len(keep), g)
                assert ok, ("perfect matching failed", n, g)
                assert is_latin(n, out, g), ("bad completion", n, g, out)
                total += 1
        print("n=%d: %d Latin squares x every kept-value subset = %d instances, "
              "all completed, NO never needed" % (n, len(squares), total))

    # ---- 3. random up to the limit ------------------------------------
    def random_latin(n):
        """Cyclic square with rows/cols/symbols randomly permuted."""
        base = [[(i + j) % n + 1 for j in range(n)] for i in range(n)]
        rp = list(range(n)); random.shuffle(rp)
        cp = list(range(n)); random.shuffle(cp)
        sp = list(range(1, n + 1)); random.shuffle(sp)
        return [[sp[base[rp[i]][cp[j]] - 1] for j in range(n)] for i in range(n)]

    for n in (1, 2, 5, 17, 50, 99, 100):
        for trial in range(3 if n >= 50 else 20):
            sq = random_latin(n)
            k = random.randint(0, n)
            keep = set(random.sample(range(1, n + 1), k))
            g = make_instance(n, sq, keep)
            assert check_regular(n, g)
            ok, out = solve_published(n, k, g)
            assert ok, (n, k)
            assert is_latin(n, out, g), (n, k)
        print("n=%d: random instances (all k) completed, every matching perfect" % n)

    # squares that are not merely relabelled cyclic ones
    def backtrack_latin(n):
        sq = [[0] * n for _ in range(n)]

        def rec(i, j):
            if i == n:
                return True
            ni, nj = (i, j + 1) if j + 1 < n else (i + 1, 0)
            cand = [v for v in range(1, n + 1)
                    if v not in sq[i][:j] and all(sq[r][j] != v for r in range(i))]
            random.shuffle(cand)
            for v in cand:
                sq[i][j] = v
                if rec(ni, nj):
                    return True
                sq[i][j] = 0
            return False
        assert rec(0, 0)
        return sq

    for n in range(5, 9):
        for trial in range(30):
            sq = backtrack_latin(n)
            k = random.randint(0, n)
            keep = set(random.sample(range(1, n + 1), k))
            g = make_instance(n, sq, keep)
            assert check_regular(n, g)
            ok, out = solve_published(n, k, g)
            assert ok and is_latin(n, out, g), (n, k, sq)
        print("n=%d: 30 backtracking-random (non-cyclic) squares, all k, completed" % n)

    # worst-case work: k = 0, n = 100 (empty grid, n perfect matchings peeled)
    import time
    g = [[0] * 101 for _ in range(101)]
    t0 = time.time()
    ok, out = solve_published(100, 0, g)
    assert ok and is_latin(100, out, g)
    print("n=100, k=0 (densest case): completed in %.2fs of Python; the matching "
          "loop touches ~2.6*n^3 edges, far under the O(n^4) worst case" %
          (time.time() - t0))

    # ---- 4. the published Kuhn variant is a true maximum matching ------
    worst = 0
    for trial in range(3000):
        n = random.randint(1, 9)
        adj = [[] for _ in range(n + 1)]
        for u in range(1, n + 1):
            for v in range(1, n + 1):
                if random.random() < 0.35:
                    adj[u].append(v)
        p = Published(n)
        p.a = [list(x) for x in adj]
        got = p.capghep()
        exp, _ = kuhn_reference(n, adj)
        assert got == exp, (adj, got, exp)
        worst = max(worst, got)
    print("3000 random bipartite graphs: published CapGhep == textbook Kuhn "
          "(max matching size up to %d)" % worst)

    print("\nAll checks passed.")


main()
