"""
Kattis "doubleshorsebackwrestling" (ICPC WF 2024) -- solution + brute-force cross-check.

Problem: n riders, rider i has rating interval [l_i,u_i]. i,j pairable iff
exists r_i in [l_i,u_i], r_j in [l_j,u_j] with r_i+r_j=s, i.e.
    l_i+l_j <= s  AND  u_i+u_j >= s.
Maximise the number of disjoint pairs (maximum matching).

MODEL
-----
Put lam_i = s-2l_i, rho_i = 2u_i-s.  Then
    pairable(i,j)  <=>  lam_i+lam_j >= 0  AND  rho_i+rho_j >= 0,
and lam_i+rho_i = 2(u_i-l_i) >= 0, so at most one coordinate is negative.
Three classes:
  N (lam<0, i.e. l>s/2): threshold t=-lam=2l-s, capacity y=rho;  t<=y.
  P (rho<0, i.e. u<s/2): threshold u0=-rho=s-2u, capacity x=lam;  u0<=x.
  Z (both >=0, interval straddles s/2): caps x=lam, y=rho.
N-N and P-P are never pairable.  N[t,y] with P[u0,x] is pairable iff the
intervals [t,y] and [u0,x] INTERSECT.  Z pairs with an N iff x_Z >= t, with a
P iff y_Z >= u0, and with any Z always -- i.e. a Z is a joker that may act as a
P-side interval [0,x_Z] or an N-side interval [0,y_Z] (but only one of them).

So: maximum bipartite matching of intervals under intersection, with jokers
that pick their side.  Greedy sweep of the coordinate c downwards; every
compatible pair is "live" at c = max(left endpoints), and at any c all active
intervals of opposite sides are mutually compatible.  At each c, expiring
elements must be matched now or never: pair expiring-N with expiring-P first,
then take the active opposite-side element with the largest left endpoint
(soonest to expire); only if no real one is left take a joker -- the joker with
the smallest capacity in its *other* role.  Leftover jokers pair up in twos.
O(n log n).
"""
import heapq, random, sys
from collections import defaultdict


def pairable(a, b, s):
    (la, ua), (lb, ub) = a, b
    return la + lb <= s <= ua + ub


# ---------------------------------------------------------------- greedy
def solve(n, s, riders):
    Ns, Ps, Zs = [], [], []          # N:(t,y,idx)  P:(u0,x,idx)  Z:(x,y,idx)
    for i, (l, u) in enumerate(riders, 1):
        lam, rho = s - 2 * l, 2 * u - s
        if lam < 0:
            Ns.append((-lam, rho, i))
        elif rho < 0:
            Ps.append((-rho, lam, i))
        else:
            Zs.append((lam, rho, i))

    actN, actP, actZX, actZY = (defaultdict(list) for _ in range(4))
    coords = set()
    for t, y, i in Ns:
        actN[y].append((t, i)); coords.add(y); coords.add(t)
    for u0, x, i in Ps:
        actP[x].append((u0, i)); coords.add(x); coords.add(u0)
    for k, (x, y, i) in enumerate(Zs):
        actZX[x].append(k); actZY[y].append(k); coords.add(x); coords.add(y)

    heapN, heapP = [], []            # max-heaps by left endpoint
    poolPX, poolNY = [], []          # jokers: P-role keyed by y, N-role keyed by x
    dead = [False] * len(Zs)
    pairs = []

    for c in sorted(coords, reverse=True):
        for t, i in actN.get(c, ()):
            heapq.heappush(heapN, (-t, i))
        for u0, i in actP.get(c, ()):
            heapq.heappush(heapP, (-u0, i))
        for k in actZX.get(c, ()):
            heapq.heappush(poolPX, (Zs[k][1], k))
        for k in actZY.get(c, ()):
            heapq.heappush(poolNY, (Zs[k][0], k))

        EN, EP = [], []
        while heapN and -heapN[0][0] == c:
            EN.append(heapq.heappop(heapN)[1])
        while heapP and -heapP[0][0] == c:
            EP.append(heapq.heappop(heapP)[1])
        while EN and EP:
            pairs.append((EN.pop(), EP.pop()))
        for i in EN:
            if heapP:
                pairs.append((i, heapq.heappop(heapP)[1]))
            else:
                while poolPX and dead[poolPX[0][1]]:
                    heapq.heappop(poolPX)
                if poolPX:
                    k = heapq.heappop(poolPX)[1]
                    dead[k] = True
                    pairs.append((i, Zs[k][2]))
        for j in EP:
            if heapN:
                pairs.append((heapq.heappop(heapN)[1], j))
            else:
                while poolNY and dead[poolNY[0][1]]:
                    heapq.heappop(poolNY)
                if poolNY:
                    k = heapq.heappop(poolNY)[1]
                    dead[k] = True
                    pairs.append((Zs[k][2], j))

    alive = [k for k in range(len(Zs)) if not dead[k]]
    for a in range(0, len(alive) - 1, 2):
        pairs.append((Zs[alive[a]][2], Zs[alive[a + 1]][2]))
    return pairs


# ------------------------------------------------------------ brute force
def brute(n, s, riders):
    ok = [[pairable(riders[i], riders[j], s) for j in range(n)] for i in range(n)]
    full = 1 << n
    dp = [0] * full
    for mask in range(full):
        i = -1
        for b in range(n):
            if mask >> b & 1:
                i = b
                break
        if i < 0:
            continue
        best = dp[mask ^ (1 << i)]
        for j in range(i + 1, n):
            if mask >> j & 1 and ok[i][j]:
                v = 1 + dp[mask ^ (1 << i) ^ (1 << j)]
                if v > best:
                    best = v
        dp[mask] = best
    return dp[full - 1]


def check_pairs(n, s, riders, pairs):
    used = set()
    for a, b in pairs:
        assert a != b and a not in used and b not in used, "reused rider"
        used.add(a); used.add(b)
        assert pairable(riders[a - 1], riders[b - 1], s), f"bad pair {a},{b}"
    return len(pairs)


# ------------------------------------------------------------------ tests
def sample():
    n, s = 6, 10
    riders = [(6, 7), (1, 4), (2, 2), (3, 8), (5, 7), (9, 9)]
    got = check_pairs(n, s, riders, solve(n, s, riders))
    exp = brute(n, s, riders)
    print(f"sample 1: greedy={got} brute={exp} (expected 2)")
    assert got == exp == 2


def random_tests(iters=4000, maxn=9, maxv=12, seed=1):
    rng = random.Random(seed)
    worst = None
    for it in range(iters):
        n = rng.randint(2, maxn)
        s = rng.randint(1, maxv)
        riders = []
        for _ in range(n):
            l = rng.randint(1, maxv)
            u = rng.randint(l, maxv)
            riders.append((l, u))
        got = check_pairs(n, s, riders, solve(n, s, riders))
        exp = brute(n, s, riders)
        if got != exp:
            worst = (n, s, riders, got, exp)
            break
    if worst:
        print("MISMATCH:", worst)
        sys.exit(1)
    print(f"random(maxn={maxn},maxv={maxv},seed={seed}): {iters} tests OK")


def stress_big():
    import time
    rng = random.Random(7)
    n, s = 200000, 10 ** 9
    riders = []
    for _ in range(n):
        l = rng.randint(1, 10 ** 9)
        u = rng.randint(l, 10 ** 9)
        riders.append((l, u))
    t0 = time.time()
    pairs = solve(n, s, riders)
    dt = time.time() - t0
    check_pairs(n, s, riders, pairs)
    print(f"n=2e5 random: {len(pairs)} pairs in {dt:.2f}s")


if __name__ == "__main__":
    sample()
    random_tests(4000, 9, 12, seed=1)
    random_tests(3000, 8, 6, seed=2)     # tiny value range -> many ties / Z riders
    random_tests(1500, 10, 20, seed=3)
    random_tests(1500, 7, 4, seed=4)
    stress_big()
    print("ALL OK")
