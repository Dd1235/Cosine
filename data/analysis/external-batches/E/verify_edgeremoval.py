"""kattis-edgeremoval -- 'Edge Removal' (ICPC Asia Can Tho 2020).

Remove the fewest edges from a connected weighted graph so the remaining graph
has EXACTLY ONE minimum spanning tree.

Claimed solution (Kruskal by weight class):
  Process weight classes in increasing order with a DSU holding all edges of
  strictly smaller weight.
    * an edge whose endpoints are already joined by strictly lighter edges is a
      "loop" edge: it is in no MST and can never break uniqueness -> KEEP it free.
    * among the remaining class-w edges (which join distinct contracted nodes),
      the MST takes a spanning forest; since all have equal weight, uniqueness
      forces that graph to already BE a forest -> keep a spanning forest of the
      class, REMOVE every class-w edge that closes a cycle inside its own class.
  Answer = m - (n-1) - L, where L = #loop edges.  (-1 if the graph is disconnected.)

Lower bound proof: in any kept set S that is connected with a unique MST, every
non-tree edge (u,v,w) must be strictly heavier than the whole tree path u..v
(otherwise swapping gives a second MST), so u,v are joined by edges of weight < w
in S and hence in the original graph -> that edge is a loop edge.  So
|S| <= (n-1) + L.  The construction attains it, and it keeps the exact same
Kruskal connectivity at every weight prefix, so each class is a forest -> unique.

Brute force: for k = 0,1,2,... try every subset of k edges to delete; a graph is
accepted iff it is connected and the number of minimum-weight spanning trees
(enumerated over all C(m, n-1) edge subsets) equals 1.
"""
import random
from itertools import combinations


# ---------------------------------------------------------------- solution
class DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        self.p[a] = b
        return True


def solve(n, edges):
    """edges: list of (u, v, w) 0-indexed vertices. Returns None if disconnected,
    else the list of 1-based indices of edges to remove."""
    order = sorted(range(len(edges)), key=lambda i: edges[i][2])
    dsu = DSU(n)
    removed = []
    i = 0
    while i < len(order):
        j = i
        w = edges[order[i]][2]
        while j < len(order) and edges[order[j]][2] == w:
            j += 1
        klass = order[i:j]
        local = DSU(n)          # only same-weight edges are unioned here
        pending = []
        for idx in klass:
            u, v, _ = edges[idx]
            ru, rv = dsu.find(u), dsu.find(v)
            if ru == rv:
                continue        # loop edge: free to keep
            if not local.union(ru, rv):
                removed.append(idx + 1)   # closes a cycle within its own class
            else:
                pending.append((u, v))
        for u, v in pending:
            dsu.union(u, v)
        i = j
    root = dsu.find(0)
    if any(dsu.find(x) != root for x in range(n)):
        return None
    return removed


def formula(n, m, edges):
    """m - (n-1) - L, independent recomputation of the count only."""
    order = sorted(range(m), key=lambda i: edges[i][2])
    dsu = DSU(n)
    loops = 0
    i = 0
    while i < m:
        j = i
        w = edges[order[i]][2]
        while j < m and edges[order[j]][2] == w:
            j += 1
        for idx in order[i:j]:
            u, v, _ = edges[idx]
            if dsu.find(u) == dsu.find(v):
                loops += 1
        for idx in order[i:j]:
            u, v, _ = edges[idx]
            dsu.union(u, v)
        i = j
    if len({dsu.find(x) for x in range(n)}) != 1:
        return None
    return m - (n - 1) - loops


# ---------------------------------------------------------------- brute force
def is_connected(n, es):
    if n == 1:
        return True
    adj = [[] for _ in range(n)]
    for u, v, _ in es:
        adj[u].append(v)
        adj[v].append(u)
    seen = {0}
    st = [0]
    while st:
        x = st.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                st.append(y)
    return len(seen) == n


def count_msts(n, es):
    """Number of minimum-weight spanning trees, by literal enumeration."""
    if n == 1:
        return 1
    best, cnt = None, 0
    for comb in combinations(range(len(es)), n - 1):
        sub = [es[i] for i in comb]
        d = DSU(n)
        ok = True
        for u, v, _ in sub:
            if not d.union(u, v):
                ok = False
                break
        if not ok:
            continue
        tot = sum(e[2] for e in sub)
        if best is None or tot < best:
            best, cnt = tot, 1
        elif tot == best:
            cnt += 1
    return cnt


def good(n, es):
    return is_connected(n, es) and count_msts(n, es) == 1


def brute(n, edges):
    m = len(edges)
    if not is_connected(n, edges):
        return None
    for k in range(m + 1):
        for rem in combinations(range(m), k):
            keep = [edges[i] for i in range(m) if i not in rem]
            if good(n, keep):
                return k
    raise AssertionError("unreachable: empty-ish graph always terminates")


# ---------------------------------------------------------------- sample
def check_sample():
    edges = [(1, 6, 1), (1, 2, 2), (4, 5, 3), (3, 4, 4), (5, 6, 5), (2, 3, 5),
             (0, 6, 6), (0, 1, 9), (0, 2, 9), (0, 3, 9), (0, 4, 9), (0, 5, 9)]
    rem = solve(7, edges)
    assert rem is not None and len(rem) == 1, rem
    assert formula(7, 12, edges) == 1
    keep = [edges[i] for i in range(12) if (i + 1) not in rem]
    assert good(7, keep), "constructed removal does not give a unique MST"
    print("sample: k=1 removing edge index", rem, "(judge accepts any optimal set)")


# ---------------------------------------------------------------- random tests
def rand_test(trials=400, seed=7):
    rng = random.Random(seed)
    checked = disc = 0
    for _ in range(trials):
        n = rng.randint(1, 6)
        allp = [(u, v) for u in range(n) for v in range(u + 1, n)]
        rng.shuffle(allp)
        m = rng.randint(0, min(len(allp), 8))
        maxw = rng.choice([1, 2, 3, 5])
        edges = [(u, v, rng.randint(0, maxw)) for u, v in allp[:m]]
        got = solve(n, edges)
        f = formula(n, len(edges), edges)
        exp = brute(n, edges)
        if exp is None:
            assert got is None and f is None, (n, edges, got, f)
            disc += 1
            continue
        assert got is not None, (n, edges)
        assert len(got) == exp, ("count mismatch", n, edges, len(got), exp)
        assert f == exp, ("formula mismatch", n, edges, f, exp)
        keep = [edges[i] for i in range(len(edges)) if (i + 1) not in got]
        assert good(n, keep), ("removal set invalid", n, edges, got)
        checked += 1
    print(f"random: {checked} connected cases matched brute force "
          f"(count AND validity of the emitted set), {disc} disconnected -> -1")


if __name__ == "__main__":
    check_sample()
    rand_test()
    rand_test(trials=250, seed=99)
    print("OK")
