"""Brute force check for kattis-perfecttree.

A subgraph of a tree that is a perfect k-ary tree is a connected vertex subset,
and for k >= 2 its root is the only vertex of degree k (internal nodes have
degree k+1, leaves degree 1), so rooting each candidate at its centre counts it
exactly once.  DP over directed edges: down[h][v][p] = number of perfect k-ary
subtrees of height h hanging at v away from p, which is the elementary symmetric
polynomial of degree k in {down[h-1][u][v] : u in N(v) \\ {p}}; the answer is N
(the single-vertex trees) plus, for every h >= 1 and every v, e_k over all of
v's neighbours.  Heights stop at log_k N, and each vertex evaluates e_k with one
element removed via prefix/suffix polynomials, so the real solution is
O(N k log_k N).  Here the same recurrence is computed the slow way and compared
with an exhaustive scan of all connected subsets.
"""
import random
from itertools import combinations

MOD = 10 ** 9 + 7


def e_k(vals, k):
    """Elementary symmetric polynomial of degree k."""
    poly = [1] + [0] * k
    for x in vals:
        for i in range(k, 0, -1):
            poly[i] = (poly[i] + poly[i - 1] * x) % MOD
    return poly[k]


def solve(n, edges, k):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    # down[(v,p)] for the current height
    cur = {}
    for v in range(n):
        cur[(v, -1)] = 1
        for p in adj[v]:
            cur[(v, p)] = 1
    ans = n % MOD
    h = 1
    while True:
        nxt = {}
        total = 0
        for v in range(n):
            for p in [-1] + adj[v]:
                vals = [cur[(u, v)] for u in adj[v] if u != p]
                nxt[(v, p)] = e_k(vals, k)
            total = (total + nxt[(v, -1)]) % MOD
        if total == 0 and all(x == 0 for x in nxt.values()):
            break
        ans = (ans + total) % MOD
        cur = nxt
        h += 1
        if h > n + 2:
            break
    return ans % MOD


def brute(n, edges, k):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    cnt = 0
    for mask in range(1, 1 << n):
        verts = [v for v in range(n) if mask >> v & 1]
        sub = set(verts)
        # connectivity
        seen = {verts[0]}
        st = [verts[0]]
        while st:
            v = st.pop()
            for u in adj[v]:
                if u in sub and u not in seen:
                    seen.add(u)
                    st.append(u)
        if len(seen) != len(sub):
            continue
        if is_perfect(sub, adj, k):
            cnt += 1
    return cnt % MOD


def is_perfect(sub, adj, k):
    for root in sub:
        depth = {root: 0}
        st = [root]
        ok = True
        leaves = []
        while st:
            v = st.pop()
            kids = [u for u in adj[v] if u in sub and u not in depth]
            if kids:
                if len(kids) != k:
                    ok = False
                    break
                for u in kids:
                    depth[u] = depth[v] + 1
                    st.append(u)
            else:
                leaves.append(v)
        if not ok or len(depth) != len(sub):
            continue
        if len({depth[x] for x in leaves}) == 1:
            return True
    return False


def main():
    # statement sample: path 1-2-3-4, k = 2 -> 6
    assert solve(4, [(0, 1), (1, 2), (2, 3)], 2) == 6, solve(4, [(0, 1), (1, 2), (2, 3)], 2)
    print("sample OK")
    rng = random.Random(21)
    bad = 0
    for _ in range(200):
        n = rng.randint(1, 10)
        edges = [(i, rng.randrange(i)) for i in range(1, n)]
        k = rng.randint(2, 5)
        a, b = solve(n, edges, k), brute(n, edges, k)
        if a != b:
            bad += 1
            print("MISMATCH n=%d k=%d edges=%s mine=%d brute=%d" % (n, k, edges, a, b))
            if bad > 5:
                return
    # some deliberately bushy trees (stars, complete k-ary trees)
    for k in range(2, 6):
        for depth in (1, 2):
            nodes = 1
            edges = []
            frontier = [0]
            for _ in range(depth):
                nf = []
                for v in frontier:
                    for _ in range(k):
                        edges.append((nodes, v))
                        nf.append(nodes)
                        nodes += 1
                frontier = nf
            if nodes > 12:
                continue
            a, b = solve(nodes, edges, k), brute(nodes, edges, k)
            if a != b:
                bad += 1
                print("MISMATCH perfect k=%d depth=%d mine=%d brute=%d" % (k, depth, a, b))
    print("random + structured trees %s" % ("OK" if bad == 0 else "%d FAILURES" % bad))


if __name__ == "__main__":
    main()
