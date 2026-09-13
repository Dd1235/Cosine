"""Bridging the Gap (Kattis / ICPC WF 2022-23) -- brute force vs the derived solution.

Model that the solution is built on (all of it checked against `brute` below)
---------------------------------------------------------------------------
Sort the times ascending, t[1] <= ... <= t[n].  In an optimal schedule:

  * every return trip carries exactly one walker;
  * the walkers that ever return are a prefix of the sorted order -- call them the
    k shuttles -- and the forward trip that carries s of them carries exactly
    walkers 1..s, so a trip is fully described by its "shuttle count" s in [0,k]
    and the c-s passengers riding with it;
  * if cnt_i = #{trips with s_j >= i} then walker i returns cnt_i - 1 times, so

        total returns = sum_j (t[1]+...+t[s_j])  -  (t[1]+...+t[k]),

    i.e. a trip pays for the shuttles it carries and one free pass is refunded;
  * feasibility of a multiset {s_j} is exactly  sum_j (s_j - 1) = k - 1  with
    0 <= s_j <= min(k,c) and max_j s_j = k (the last trip carries all k shuttles);
  * the forward cost is the sum of the trip maxima: sort the trips by passenger
    capacity c-s descending and hand them consecutive blocks of the passenger list
    starting from the slowest; a trip carrying no passenger costs t[s] instead.

`solve` is one DP over (passengers ferried, sum_j (s_j - 1)) that ranges over every
such multiset at once -- k never has to be enumerated because k = the number of
walkers still on the near side when the DP stops.  The number of s=0 trips is at
most n/c and k <= that + 1, so the DP is O(n * (n/c) * min(c, n/c)) = O(n^2) in the
worst case (c ~ sqrt(n)), roughly 2*10^8 machine operations at n = c = 10^4, and
far less in practice because most states are unreachable.

TRAPS (both of these passed thousands of random tests before failing):
  * the "repeat a shuttle cycle" greedy -- each round sends the m fastest across,
    then m-1 full trips, m rowing back -- is wrong because trips from *different*
    rounds compete for the slow walkers.  n=9, c=3, t=[5,6,9,11,14,15,17,23,23]:
    that greedy says 76, the optimum is 74.
  * assigning passengers strictly by "largest capacity gets the slowest walkers"
    is wrong once some trip must run empty: the trip left empty should be the one
    with the *fewest* shuttles, not the one with the smallest capacity.
    n=22, c=5, t=[9,13,23,27,35,36,38,69,76,80,112,131,139,143,158,165,166,170,
    172,174,182,196]: that rule says 648, the optimum is 646.
"""
import heapq
import itertools
import random
import sys

INF = float("inf")


# --------------------------------------------------------------------------- #
# exact reference: Dijkstra over (mask still on the near side, torch side)      #
# no structural assumption -- returns may carry any number of walkers           #
# --------------------------------------------------------------------------- #
def brute(t, c):
    n = len(t)
    full = (1 << n) - 1
    cache = {}

    def subsets(mask):
        r = cache.get(mask)
        if r is not None:
            return r
        bits = [i for i in range(n) if mask >> i & 1]
        out = []
        for k in range(1, min(c, len(bits)) + 1):
            for combo in itertools.combinations(bits, k):
                s = 0
                mx = 0
                for i in combo:
                    s |= 1 << i
                    if t[i] > mx:
                        mx = t[i]
                out.append((s, mx))
        cache[mask] = out
        return out

    dist = {(full, 0): 0}
    pq = [(0, full, 0)]
    while pq:
        d, mask, side = heapq.heappop(pq)
        if dist.get((mask, side)) != d:
            continue
        if mask == 0 and side == 1:
            return d
        movable = mask if side == 0 else full & ~mask
        for s, mx in subsets(movable):
            nxt = (mask & ~s, 1) if side == 0 else (mask | s, 0)
            nd = d + mx
            if dist.get(nxt, INF) > nd:
                dist[nxt] = nd
                heapq.heappush(pq, (nd, nxt[0], nxt[1]))
    return None


# --------------------------------------------------------------------------- #
# the solution                                                                  #
# --------------------------------------------------------------------------- #
def solve(t, c):
    t = sorted(t)
    n = len(t)
    if n <= c:
        return t[-1]
    q = [t[n - 1 - p] for p in range(n)]          # slowest walker not yet ferried
    pre = [0] * (n + 2)
    for i in range(n):
        pre[i + 1] = pre[i] + t[i]
    amax = n // c + 2                             # >= number of s=0 trips
    kmax = min(c, amax + 1)                       # >= k

    # extra[k][r] = cheapest passenger-less trips (shuttle count 2..k) whose
    # (s-1) sum to r.  Such a trip costs pre[s] (returns) + t[s-1] (its own max).
    extra = [[INF] * (amax + 1) for _ in range(kmax + 2)]
    for k in range(1, kmax + 2):
        row = extra[k]
        row[0] = 0
        for r in range(1, amax + 1):
            best = INF
            for s in range(2, min(k, kmax) + 1):
                if s - 1 <= r and row[r - s + 1] < INF:
                    v = row[r - s + 1] + pre[s] + t[s - 1]
                    if v < best:
                        best = v
            row[r] = best

    width = 2 * amax + 1
    off = amax
    dp = [[INF] * width for _ in range(n + 1)]
    dp[0][off] = 0
    best = INF
    for sg in range(kmax + 1):                    # trips in ascending shuttle count
        cap = c - sg
        if cap < 1:
            continue
        for p in range(n):
            row = dp[p]
            for di in range(width):
                v = row[di]
                if v == INF:
                    continue
                nd = di - off + sg - 1
                if not (-amax <= nd <= amax):
                    continue
                base = v + pre[sg] + q[p]
                np_ = p + cap
                if np_ <= n:
                    if base < dp[np_][nd + off]:
                        dp[np_][nd + off] = base
                    k = n - np_                   # stop here: last trip takes them all
                    if 1 <= k <= c and nd <= 0 and sg <= k:
                        e = extra[min(k, kmax + 1)][-nd]
                        if e < INF and base + e + t[k - 1] < best:
                            best = base + e + t[k - 1]
                for k in range(max(1, n - p - c), min(c, n - p - 1) + 1):
                    z = n - k - p                 # this trip only partly filled
                    if 1 <= z <= cap and nd <= 0 and sg <= k:
                        e = extra[min(k, kmax + 1)][-nd]
                        if e < INF and base + e + t[k - 1] < best:
                            best = base + e + t[k - 1]
    return best


# --------------------------------------------------------------------------- #
# independent reference with the same theory but a different shape:             #
# k is enumerated, trips are laid down in ascending shuttle count, and a trip    #
# may be left empty or partly filled at any point                               #
# --------------------------------------------------------------------------- #
def reference(t, c):
    t = sorted(t)
    n = len(t)
    if n <= c:
        return t[-1]
    pre = [0] * (n + 2)
    for i in range(n):
        pre[i + 1] = pre[i] + t[i]
    best = INF
    for k in range(1, min(c, n - 1) + 1):
        P = n - k
        q = [t[n - 1 - j] for j in range(P)]
        target = k - 1
        lo = -((P + c - 1) // c) - 2
        W = target - lo + 1

        def relax(src, dst, d):
            s = d + 1
            cap = c - s
            for p in range(P + 1):
                for di in range(W):
                    v = src[p][di]
                    if v == INF:
                        continue
                    nd = di + lo + d
                    if not (lo <= nd <= target):
                        continue
                    if cap > 0 and p < P:
                        for z in range(1, min(cap, P - p) + 1):
                            if v + pre[s] + q[p] < dst[p + z][nd - lo]:
                                dst[p + z][nd - lo] = v + pre[s] + q[p]
                    if s >= 1 and d >= 1:
                        if v + pre[s] + t[s - 1] < dst[p][nd - lo]:
                            dst[p][nd - lo] = v + pre[s] + t[s - 1]

        dp = [[INF] * W for _ in range(P + 1)]
        dp[0][-lo] = 0
        for d in range(-1, target):
            relax(dp, dp, d)
        dp2 = [[INF] * W for _ in range(P + 1)]
        relax(dp, dp2, target)                    # at least one trip carries all k
        relax(dp2, dp2, target)
        v = dp2[P][target - lo]
        if v < INF and v - pre[k] < best:
            best = v - pre[k]
    return best


# --------------------------------------------------------------------------- #
KNOWN = [
    ([1, 2, 10, 5], 2, 17),                       # sample 1
    ([1, 2, 10, 5], 6, 10),                       # sample 2
    ([5, 6, 9, 11, 14, 15, 17, 23, 23], 3, 74),   # kills the shuttle-cycle greedy
    ([1, 2, 2, 2, 3, 3, 4, 4, 10 ** 9], 3, 1000000011),
    ([2, 3, 6, 6, 6, 10, 20, 21, 22, 24, 25, 26], 4, 66),
    ([1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2], 3, 14),
    ([9, 13, 23, 27, 35, 36, 38, 69, 76, 80, 112, 131, 139, 143, 158, 165, 166,
      170, 172, 174, 182, 196], 5, 646),          # kills the "largest cap first" rule
]


def known_cases():
    bad = 0
    for t, c, want in KNOWN:
        got = solve(t, c)
        if got != want:
            bad += 1
            print("BAD  c=%d want=%s got=%s t=%s" % (c, want, got, sorted(t)))
    print("known cases: %d checked, %d wrong" % (len(KNOWN), bad))
    return bad


def vs_brute(seed, iters, nmax, cmax):
    random.seed(seed)
    bad = 0
    for _ in range(iters):
        n = random.randint(2, nmax)
        c = random.randint(2, min(n + 1, cmax))
        hi = random.choice([2, 3, 7, 30, 200, 10 ** 9])
        t = sorted(random.randint(1, hi) for _ in range(n))
        b = brute(t, c)
        a = solve(t, c)
        if a != b:
            bad += 1
            print("MISMATCH n=%d c=%d t=%s brute=%s solve=%s" % (n, c, t, b, a))
            sys.stdout.flush()
            if bad > 5:
                break
    print("vs brute (n<=%d, c<=%d): %d cases, %d mismatches" % (nmax, cmax, iters, bad))
    return bad


def vs_reference(seed, iters, nmax, cmax):
    random.seed(seed)
    bad = 0
    for _ in range(iters):
        n = random.randint(2, nmax)
        c = random.randint(2, min(n + 1, cmax))
        hi = random.choice([2, 3, 7, 30, 200, 10 ** 9])
        t = sorted(random.randint(1, hi) for _ in range(n))
        a = reference(t, c)
        b = solve(t, c)
        if a != b:
            bad += 1
            print("MISMATCH n=%d c=%d t=%s reference=%s solve=%s" % (n, c, t, a, b))
            sys.stdout.flush()
            if bad > 5:
                break
    print("vs reference (n<=%d, c<=%d): %d cases, %d mismatches" % (nmax, cmax, iters, bad))
    return bad


def timing():
    import time
    random.seed(5)
    for n, c in ((1000, 3), (2000, 50), (3000, 100), (4000, 2)):
        t = [random.randint(1, 10 ** 9) for _ in range(n)]
        st = time.time()
        solve(t, c)
        print("  n=%d c=%d -> %.2fs (python)" % (n, c, time.time() - st))


def main():
    bad = 0
    bad += known_cases()
    bad += vs_brute(1, 900, 10, 7)
    bad += vs_brute(2, 150, 12, 5)
    bad += vs_brute(3, 40, 13, 3)
    bad += vs_reference(4, 200, 22, 8)
    bad += vs_reference(5, 80, 45, 15)
    print("timing:")
    timing()
    print("TOTAL MISMATCHES:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
