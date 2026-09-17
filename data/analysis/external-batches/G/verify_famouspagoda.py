"""Famous Pagoda: partition a sorted array a[1..N] into G consecutive segments,
cost of a segment = min over INTEGER v of sum |a_s - v|^k, k in {1,2}.  N<=2000,G<=N.

Solution: layered DP dp[g][j] with divide-and-conquer optimisation (the cost w(i,j)
satisfies the quadrangle inequality), O(G*N*log N) time, O(N) space per layer.
Segment cost in O(1) from prefix sums of a and a^2 (median for k=1, round(mean)
for k=2 -- check both floor and ceil).

Check: D&C-optimised DP against the plain O(G*N^2) DP on random sorted arrays,
plus the three samples.
"""
import random
from functools import lru_cache

def make_cost(a, k):
    n = len(a)
    P = [0]*(n+1); P2 = [0]*(n+1)
    for i, v in enumerate(a):
        P[i+1] = P[i] + v
        P2[i+1] = P2[i] + v*v
    def cost(i, j):          # inclusive 0-indexed
        if i > j: return 0
        m = j - i + 1
        if k == 1:
            mid = (i + j)//2
            v = a[mid]
            left = v*(mid - i) - (P[mid] - P[i])
            right = (P[j+1] - P[mid+1]) - v*(j - mid)
            return left + right
        s = P[j+1] - P[i]; s2 = P2[j+1] - P2[i]
        best = None
        q = s // m
        for v in (q, q+1):
            c = s2 - 2*v*s + m*v*v
            if best is None or c < best: best = c
        return best
    return cost

def brute(a, G, k):
    n = len(a); cost = make_cost(a, k)
    INF = float('inf')
    dp = [INF]*(n+1); dp[0] = 0
    for g in range(1, G+1):
        nd = [INF]*(n+1)
        for j in range(g, n+1):
            for i in range(g-1, j):
                if dp[i] < INF:
                    c = dp[i] + cost(i, j-1)
                    if c < nd[j]: nd[j] = c
        dp = nd
    return dp[n]

def fast(a, G, k):
    n = len(a); cost = make_cost(a, k)
    INF = float('inf')
    dp = [INF]*(n+1); dp[0] = 0
    for g in range(1, G+1):
        nd = [INF]*(n+1)
        def rec(lo, hi, olo, ohi):
            if lo > hi: return
            mid = (lo+hi)//2
            best = INF; arg = olo
            for i in range(olo, min(mid-1, ohi)+1):
                if dp[i] < INF:
                    c = dp[i] + cost(i, mid-1)
                    if c < best: best, arg = c, i
            nd[mid] = best
            rec(lo, mid-1, olo, arg); rec(mid+1, hi, arg, ohi)
        rec(1, n, 0, n-1)
        dp = nd
    return dp[n]

def main():
    assert fast([1,2,3,4,5],1,1) == 6, fast([1,2,3,4,5],1,1)
    assert fast([1,2,3,4,5],1,2) == 10
    assert fast([1,2,3,4,5],2,2) == 3
    print("samples OK")
    random.seed(7)
    bad = 0
    for t in range(400):
        n = random.randint(1, 9)
        a = sorted(random.randint(1, 12) for _ in range(n))
        G = random.randint(1, n)
        k = random.choice([1,2])
        b = brute(a, G, k); f = fast(a, G, k)
        if b != f:
            bad += 1
            if bad < 6: print("MISMATCH", a, G, k, b, f)
    print("random small: mismatches =", bad)
    assert bad == 0
    # bigger randoms with heavy ties / plateaus
    bad = 0
    for t in range(60):
        n = random.randint(10, 26)
        a = sorted(random.randint(1, 6) for _ in range(n))
        G = random.randint(1, n); k = random.choice([1,2])
        if brute(a,G,k) != fast(a,G,k):
            bad += 1; print("MISMATCH", a, G, k)
    print("random plateau: mismatches =", bad)
    assert bad == 0
    print("famouspagoda: OK")

main()
