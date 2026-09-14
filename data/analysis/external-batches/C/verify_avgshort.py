"""codechef-avgshort / "Short in Average".

Minimum average-weight walk from A to B in a directed weighted digraph.
Walks may repeat edges and need not be finite, so the answer is an INFIMUM.

Intended solution (solve()):
    Binary search on the answer lambda.  Reweight every edge w -> w - lambda.
    A walk with average < lambda exists iff the shortest *walk* from A to B
    under the reweighted costs is negative -- which is the case either when
    some A->B path has negative reweighted cost, or when a negative cycle sits
    on some A->B route (loop it forever; the average tends to the cycle mean).
    The feasibility test is therefore Bellman-Ford with negative-cycle
    detection, run on the subgraph of vertices reachable from A *and* able to
    reach B.  O(log(1/eps) * N * M).

Brute force (brute()):
    Any walk decomposes into one simple A->B path plus a multiset of cycles,
    and by the mediant inequality (a1+a2)/(b1+b2) >= min(a1/b1, a2/b2) its
    ratio is at least the smallest ratio among those pieces.  So the infimum
    equals min(best simple A->B path ratio, best simple-cycle mean inside the
    reachable/co-reachable subgraph).  Both enumerated exhaustively with exact
    Fractions.  Exponential -- tiny graphs only.
"""
import random
import sys
from fractions import Fraction

INF = float("inf")


# ---------------------------------------------------------------- intended

def _restrict(n, edges, A, B):
    """Vertices reachable from A and co-reachable to B."""
    adj = [[] for _ in range(n + 1)]
    radj = [[] for _ in range(n + 1)]
    for x, y, z in edges:
        adj[x].append(y)
        radj[y].append(x)

    def bfs(src, g):
        seen = [False] * (n + 1)
        seen[src] = True
        stack = [src]
        while stack:
            u = stack.pop()
            for v in g[u]:
                if not seen[v]:
                    seen[v] = True
                    stack.append(v)
        return seen

    fwd = bfs(A, adj)
    bwd = bfs(B, radj)
    return [fwd[v] and bwd[v] for v in range(n + 1)]


def solve(n, edges, A, B):
    keep = _restrict(n, edges, A, B)
    if not keep[B]:
        return None  # -1: no path at all
    sub = [(x, y, z) for x, y, z in edges if keep[x] and keep[y]]
    nodes = [v for v in range(1, n + 1) if keep[v]]

    def feasible(lam):
        """True iff some A->B walk has average < lam."""
        dist = [INF] * (n + 1)
        dist[A] = 0.0
        upd = False
        for it in range(len(nodes)):
            upd = False
            for x, y, z in sub:
                if dist[x] < INF:
                    nd = dist[x] + (z - lam)
                    if nd < dist[y] - 1e-13:
                        dist[y] = nd
                        upd = True
            if not upd:
                break
        if upd:  # still relaxing after |V| rounds -> usable negative cycle
            return True
        return dist[B] < -1e-12

    lo, hi = 1.0, 100.0  # 1 <= Z_i <= 100, so the answer lies in [1, 100]
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if feasible(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


# ------------------------------------------------------------- brute force

def brute(n, edges, A, B):
    keep = _restrict(n, edges, A, B)
    if not keep[B]:
        return None
    adj = [[] for _ in range(n + 1)]
    for x, y, z in edges:
        adj[x].append((y, z))

    best = None

    # all simple paths A -> B
    seen = [False] * (n + 1)

    def dfs_path(u, wsum, elen):
        nonlocal best
        if u == B and elen > 0:
            r = Fraction(wsum, elen)
            if best is None or r < best:
                best = r
            return  # a longer walk through B decomposes into path+cycles
        for v, z in adj[u]:
            if not seen[v]:
                seen[v] = True
                dfs_path(v, wsum + z, elen + 1)
                seen[v] = False

    seen[A] = True
    dfs_path(A, 0, 0)

    # all simple cycles inside the reachable/co-reachable subgraph
    onpath = [False] * (n + 1)

    def dfs_cycle(start, u, wsum, elen):
        nonlocal best
        for v, z in adj[u]:
            if not keep[v] or v < start:
                continue
            if v == start:
                r = Fraction(wsum + z, elen + 1)
                if best is None or r < best:
                    best = r
            elif not onpath[v]:
                onpath[v] = True
                dfs_cycle(start, v, wsum + z, elen + 1)
                onpath[v] = False

    for s in range(1, n + 1):
        if keep[s]:
            onpath[s] = True
            dfs_cycle(s, s, 0, 0)
            onpath[s] = False

    return float(best)


# ------------------------------------------------------------------ checks

SAMPLE = """2
3 3
1 2 1
2 3 2
3 2 3
1 3
3 3
1 2 10
2 3 1
3 2 1
1 3
"""
SAMPLE_OUT = [1.5, 1.0]


def run_samples():
    it = iter(SAMPLE.split())
    t = int(next(it))
    ok = True
    for case in range(t):
        n = int(next(it)); m = int(next(it))
        edges = [(int(next(it)), int(next(it)), int(next(it))) for _ in range(m)]
        A = int(next(it)); B = int(next(it))
        got = solve(n, edges, A, B)
        exp = SAMPLE_OUT[case]
        good = got is not None and abs(got - exp) < 1e-9
        ok &= good
        print(f"sample {case + 1}: got {got!r} expected {exp} {'OK' if good else 'FAIL'}")
    return ok


def run_random(trials=800, seed=1):
    rng = random.Random(seed)
    for t in range(trials):
        n = rng.randint(2, 6)
        pairs = [(x, y) for x in range(1, n + 1) for y in range(1, n + 1) if x != y]
        rng.shuffle(pairs)
        m = rng.randint(1, min(len(pairs), 9))
        edges = [(x, y, rng.randint(1, 12)) for x, y in pairs[:m]]
        A = rng.randint(1, n)
        B = rng.randint(1, n)
        while B == A:
            B = rng.randint(1, n)
        a = solve(n, edges, A, B)
        b = brute(n, edges, A, B)
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-6):
            print("MISMATCH", n, edges, A, B, "solve=", a, "brute=", b)
            return False
    print(f"random: {trials} trials OK")
    return True


if __name__ == "__main__":
    ok = run_samples()
    ok &= run_random()
    print("ALL OK" if ok else "FAILURES")
    sys.exit(0 if ok else 1)
