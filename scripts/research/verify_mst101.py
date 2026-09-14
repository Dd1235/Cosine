"""
codechef-mst101  "MST Problem"
Given N, K: build a symmetric N x N matrix, zero diagonal, whose C(N,2) upper
entries are a permutation of 1..C(N,2), such that the MST of the induced
complete graph has weight exactly K.  Or report -1.

THEORY (what this script checks)
--------------------------------
Weights are exactly the ranks 1..M (M = C(N,2)), so f(W) = sum of the ranks
Kruskal picks.  Kruskal takes rank t iff it joins two components.  Let the
picked ranks be r_1<...<r_{N-1}.  Before r_i there are r_i-1 edges, all of
them lying inside components built by the i-1 earlier merges; the most edges
those components can hold is C(i,2) (one blob of size i).  Hence
        i <= r_i <= C(i,2)+1 ,   r strictly increasing.
Conversely every such r is realizable: grow one blob 1,2,...,N, spend r_i on
the edge joining the (i+1)-st vertex to the blob and every other rank on a
free pair inside the blob.  So the achievable K are exactly the integers in
        [ N(N-1)/2 , (N-1) + N(N-1)(N-2)/6 ]
(min = all r_i=i, max = all r_i=C(i,2)+1), and the range is contiguous
because the caps grow, so the r_i can be raised one unit at a time.
"""
from itertools import permutations, combinations
from math import comb

# ---------------------------------------------------------------- reference
def lo(N): return N * (N - 1) // 2
def hi(N): return (N - 1) + N * (N - 1) * (N - 2) // 6

def ranks_for(N, K):
    """MST edge ranks r_1..r_{N-1} summing to K, or None."""
    if N == 1:
        return [] if K == 0 else None
    if not (lo(N) <= K <= hi(N)):
        return None
    r = list(range(1, N))                     # minimum vector, sum = lo(N)
    need = K - lo(N)
    for i in range(N - 1, 1, -1):             # raise from the top down
        if need == 0:
            break
        cap = min(comb(i, 2) + 1, r[i] - 1 if i < N - 1 else 10**9)
        room = cap - r[i - 1]
        take = min(room, need)
        r[i - 1] += take
        need -= take
    assert need == 0 and r == sorted(set(r)) and sum(r) == K
    return r

def build(N, K):
    """good matrix with f(W)=K, or None"""
    r = ranks_for(N, K)
    if r is None:
        return None
    M = comb(N, 2)
    W = [[0] * N for _ in range(N)]
    rset = {t: i for i, t in enumerate(r)}     # rank -> which merge
    blob = 1                                   # vertices 0..blob-1 are joined
    free = []                                  # unused pairs inside the blob
    fi = 0
    for t in range(1, M + 1):
        if t in rset:
            u, v = 0, blob                     # join new vertex to the blob
            W[u][v] = W[v][u] = t
            for j in range(1, blob):           # new internal pairs appear
                free.append((j, blob))
            blob += 1
        else:
            u, v = free[fi]; fi += 1
            W[u][v] = W[v][u] = t
    return W

# --------------------------------------------------------------- validation
def mst(W):
    """independent Kruskal on the dense matrix"""
    N = len(W)
    p = list(range(N))
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    es = sorted((W[i][j], i, j) for i in range(N) for j in range(i + 1, N))
    tot = 0
    for w, i, j in es:
        a, b = f(i), f(j)
        if a != b:
            p[a] = b; tot += w
    return tot

def is_good(W, N):
    if len(W) != N or any(len(r) != N for r in W):
        return False
    if any(W[i][i] != 0 for i in range(N)):
        return False
    if any(W[i][j] != W[j][i] for i in range(N) for j in range(N)):
        return False
    up = sorted(W[i][j] for i in range(N) for j in range(i + 1, N))
    return up == list(range(1, comb(N, 2) + 1))

# ------------------------------------------------- exhaustive ground truth 1
def brute_perm(N):
    """every permutation of weights -> set of achievable MST weights"""
    pairs = list(combinations(range(N), 2))
    seen = set()
    for perm in permutations(range(1, len(pairs) + 1)):
        W = [[0] * N for _ in range(N)]
        for (i, j), w in zip(pairs, perm):
            W[i][j] = W[j][i] = w
        seen.add(mst(W))
    return seen

# ------------------------------------------------- exhaustive ground truth 2
def brute_dp(N):
    """
    exact search over (component sizes, edges already inside each component).
    Adding rank t either merges two components (cost t) or fills a free slot
    inside one component.  State is the multiset of (size, used) pairs, which
    is all Kruskal can see.
    """
    M = comb(N, 2)
    start = tuple(sorted([(1, 0)] * N))
    cur = {start: {0}}
    for t in range(1, M + 1):
        nxt = {}
        for st, sums in cur.items():
            L = list(st)
            # merge i,j
            for a in range(len(L)):
                for b in range(a + 1, len(L)):
                    (sa, ua), (sb, ub) = L[a], L[b]
                    nl = [L[k] for k in range(len(L)) if k not in (a, b)]
                    nl.append((sa + sb, ua + ub + 1))
                    key = tuple(sorted(nl))
                    nxt.setdefault(key, set()).update(s + t for s in sums)
            # internal edge
            for a in range(len(L)):
                s, u = L[a]
                if u + 1 <= comb(s, 2):
                    nl = list(L); nl[a] = (s, u + 1)
                    key = tuple(sorted(nl))
                    nxt.setdefault(key, set()).update(sums)
        cur = nxt
    out = set()
    for st, sums in cur.items():
        if len(st) == 1:
            out |= sums
    return out

# ------------------------------------------------------------------- checks
def main():
    # 0. samples from the statement
    assert build(2, 1) is not None and mst(build(2, 1)) == 1
    assert build(2, 8) is None
    assert build(3, 2) is None
    assert build(3, 3) is not None and mst(build(3, 3)) == 3
    assert build(3, 4) is None
    print("samples ok")

    # 1. permutation brute force vs formula (N=2..5)
    for N in (2, 3, 4, 5):
        if N == 5:
            continue  # 10! handled by the DP; permutation loop too slow
        got = brute_perm(N)
        want = set(range(lo(N), hi(N) + 1))
        assert got == want, (N, sorted(got), sorted(want))
        print(f"perm brute N={N}: achievable {sorted(got)} == [{lo(N)},{hi(N)}]")

    # 2. state DP vs formula (N=2..7) and vs permutation brute force
    for N in range(2, 8):
        got = brute_dp(N)
        want = set(range(lo(N), hi(N) + 1))
        assert got == want, (N, sorted(got)[:20], lo(N), hi(N))
        print(f"dp   brute N={N}: achievable == [{lo(N)},{hi(N)}]  ({len(got)} values)")
    for N in (4,):
        assert brute_dp(N) == brute_perm(N)

    # 3. constructor: every N<=12, every K in 1..N^3
    for N in range(2, 13):
        for K in range(1, N ** 3 + 1):
            W = build(N, K)
            if lo(N) <= K <= hi(N):
                assert W is not None and is_good(W, N) and mst(W) == K, (N, K)
            else:
                assert W is None, (N, K)
        print(f"construct N={N}: all K in 1..{N**3} agree")

    # 4. large N spot checks incl. the real limits
    import random
    for N in (13, 20, 33, 49, 50):
        ks = {lo(N), hi(N), lo(N) + 1, hi(N) - 1, min(N ** 3, hi(N))}
        ks |= {random.randint(1, N ** 3) for _ in range(200)}
        for K in ks:
            W = build(N, K)
            if lo(N) <= K <= hi(N):
                assert W is not None and is_good(W, N) and mst(W) == K, (N, K)
            else:
                assert W is None, (N, K)
        print(f"construct N={N}: range [{lo(N)},{hi(N)}], N^3={N**3} ok")

    # 5. random permutations never escape the range (sanity for N=6..9)
    for N in range(6, 10):
        pairs = list(combinations(range(N), 2))
        for _ in range(4000):
            perm = list(range(1, len(pairs) + 1)); random.shuffle(perm)
            W = [[0] * N for _ in range(N)]
            for (i, j), w in zip(pairs, perm):
                W[i][j] = W[j][i] = w
            assert lo(N) <= mst(W) <= hi(N), (N, mst(W))
        print(f"random perms N={N}: all MST weights inside [{lo(N)},{hi(N)}]")

    # 6. worst-case timing for the real limits
    import time
    t0 = time.time()
    for _ in range(500):
        build(50, 19649)
    print("500 worst-case builds: %.2fs" % (time.time() - t0))
    print("ALL OK")

main()
