"""Cu Chi Tunnels: tree on N nodes rooted at 1, parent index < child index (paths
from 1 have increasing labels).  Given degree array D, decide feasibility.

Solution: child counts are c_1 = D_1, c_i = D_i - 1 (i>=2).  Feasible iff
sum(c) == N-1 and every prefix leaves an open slot: S_i = sum_{j<=i} c_j - (i-1) >= 1
for i = 1..N-1 (node i+1 needs a parent <= i with a free slot).  S_N == 0 follows.
O(N) time, O(1) extra space.

Brute force: enumerate every parent array p[2..N] with p[i] < i, collect degree
multisets, compare.
"""
from itertools import product
import random

def solve(N, D):
    if any(d < 1 or d > N - 1 for d in D):
        return False
    c = [D[0]] + [d - 1 for d in D[1:]]
    if sum(c) != N - 1:
        return False
    s = 0
    for i in range(N):            # after processing node i+1 (0-indexed i)
        s += c[i]
        if i >= 1:
            s -= 1                # node i+1 consumed a slot
        if i < N - 1 and s < 1:
            return False
    return s == 0

def brute_all(N):
    """set of achievable degree tuples"""
    out = set()
    for p in product(*[range(1, i) for i in range(2, N + 1)]):
        deg = [0] * (N + 1)
        for i, par in enumerate(p, start=2):
            deg[i] += 1
            deg[par] += 1
        out.add(tuple(deg[1:]))
    return out

def main():
    # samples
    assert solve(8, [3,2,2,1,1,3,1,1]) is True
    assert solve(4, [3,3,3,3]) is False
    for N in range(2, 8):
        ach = brute_all(N)
        # every degree tuple in range [1, N-1]^N
        bad = 0
        for D in product(range(1, N), repeat=N):
            exp = D in ach
            got = solve(N, list(D))
            if exp != got:
                bad += 1
                if bad < 5:
                    print("MISMATCH N=%d D=%s expected=%s got=%s" % (N, D, exp, got))
        print("N=%d  tuples=%d  achievable=%d  mismatches=%d" % (N, (N-1)**N, len(ach), bad))
        assert bad == 0
    print("cuchitunnels: OK (samples + exhaustive N=2..7)")

main()
