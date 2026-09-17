"""Brute force check for kattis-peaktram.

Building i is visible iff h_i is strictly greater than every earlier height, so
the state after processing a prefix is (running maximum, number of visible so
far) and the cost of building i is c_i*|h_i - p_i|.  Given a running maximum H,
an invisible building is cheapest at h_i = min(p_i, H) (cost c_i*max(0, p_i-H),
and it is illegal while H = 0 since heights must be positive).  A visible one may
take ANY height above H, not merely max(p_i, H+1): pushing a visible building
BELOW its preferred height can be worth it so that a later, cheaper building can
still exceed it.  Candidate heights are therefore p_j + d for |d| <= n, O(n^2) of
them, and the visible transition is a prefix minimum over the running maximum, so
the real solution is O(n^2) states times O(n^2) heights = O(n^4) at n = 70.
"""
import random
from itertools import product


def solve(n, k, P, C):
    """DP over (running maximum, number visible).  A visible building may be set
    to ANY height above the running maximum - including below its own preferred
    height, to leave room for later buildings - so the candidate heights are
    p_j + d for |d| <= n, and the transition uses a prefix minimum over the
    running maximum."""
    cands = sorted({p + d for p in P for d in range(-n, n + 1) if p + d >= 1})
    idx = {v: i for i, v in enumerate(cands)}
    m = len(cands)
    INF = float("inf")
    # dp[j][cnt]: j = index of running maximum, j = -1 encodes "nothing built"
    dp = {(-1, 0): 0}
    for i in range(n):
        nd = {}

        def put(key, v):
            if v < nd.get(key, INF):
                nd[key] = v

        for (hi, cnt), cost in dp.items():
            H = 0 if hi < 0 else cands[hi]
            if H >= 1:  # invisible: h_i = min(p_i, H)
                put((hi, cnt), cost + C[i] * max(0, P[i] - H))
            for j in range(m):      # visible: any candidate height above H
                if cands[j] > H:
                    put((j, cnt + 1), cost + C[i] * abs(cands[j] - P[i]))
        dp = nd
    return min([v for (hi, cnt), v in dp.items() if cnt >= k], default=INF)


def brute(n, k, P, C):
    hi = max(P) + n + 1
    best = None
    for hs in product(range(1, hi + 1), repeat=n):
        vis = 0
        mx = 0
        for h in hs:
            if h > mx:
                vis += 1
                mx = h
        if vis < k:
            continue
        cost = sum(C[i] * abs(hs[i] - P[i]) for i in range(n))
        if best is None or cost < best:
            best = cost
    return best


def main():
    assert solve(5, 3, [5, 3, 4, 9, 6], [3, 2, 8, 4, 2]) == 6, \
        solve(5, 3, [5, 3, 4, 9, 6], [3, 2, 8, 4, 2])
    print("sample OK (6)")
    rng = random.Random(4)
    bad = 0
    for _ in range(300):
        n = rng.randint(1, 5)
        k = rng.randint(1, n)
        P = [rng.randint(1, 6) for _ in range(n)]
        C = [rng.randint(1, 4) for _ in range(n)]
        a, b = solve(n, k, P, C), brute(n, k, P, C)
        if a != b:
            bad += 1
            print("MISMATCH n=%d k=%d P=%s C=%s mine=%s brute=%s" % (n, k, P, C, a, b))
            if bad > 5:
                return
    print("random trials %s" % ("OK" if bad == 0 else "%d FAILURES" % bad))


if __name__ == "__main__":
    main()
