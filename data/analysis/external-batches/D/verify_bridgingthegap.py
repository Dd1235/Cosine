"""Bridging the Gap (Kattis / ICPC WF 2022-23) -- brute force vs candidate DP.

Brute force: Dijkstra over (bitmask of people still on the near side, torch side).
Candidate: O(states * m) DP described in the solution write-up:
  sort ascending; repeatedly apply a "shuttle cycle" with parameter m
  (the m fastest act as shuttles: one trip carries those m plus the c-m
  fastest of the current slow batch, then m-1 trips carry c slow people each,
  with one shuttle rowing back after every trip), until <= c remain, which
  cross together.
"""
import heapq, itertools, random, sys


def brute(t, c):
    n = len(t)
    full = (1 << n) - 1
    # state = (mask of people on NEAR side, torch: 0 near / 1 far)
    start = (full, 0)
    dist = {start: 0}
    pq = [(0, full, 0)]
    # precompute subsets of size 1..c for every mask, lazily
    sub_cache = {}

    def subsets(mask):
        if mask in sub_cache:
            return sub_cache[mask]
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
        sub_cache[mask] = out
        return out

    while pq:
        d, mask, side = heapq.heappop(pq)
        if dist.get((mask, side), None) != d:
            continue
        if mask == 0 and side == 1:
            return d
        if side == 0:
            for s, mx in subsets(mask):
                ns = (mask & ~s, 1)
                nd = d + mx
                if dist.get(ns, 1 << 62) > nd:
                    dist[ns] = nd
                    heapq.heappush(pq, (nd, ns[0], 1))
        else:
            far = full & ~mask
            for s, mx in subsets(far):
                ns = (mask | s, 0)
                nd = d + mx
                if dist.get(ns, 1 << 62) > nd:
                    dist[ns] = nd
                    heapq.heappush(pq, (nd, ns[0], 0))
    return None


def candidate(t, c):
    """Sort ascending.  dp[rem] = best time to move the rem fastest people, who are
    the only ones left on the near side.  rem <= c: one final trip.  Otherwise apply a
    "shuttle cycle" with parameter m (1 <= m <= c): the m fastest people act as
    shuttles; one trip carries those m plus either 0 or c-m passengers, and m-1 more
    trips carry up to c passengers each, one shuttle rowing back after every trip, so
    all m shuttles end up back on the near side.  Passengers are always taken from the
    slow end, the full trips getting the slowest people."""
    t = sorted(t)
    n = len(t)
    INF = float('inf')
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + t[i]
    dp = [INF] * (n + 1)
    for rem in range(1, n + 1):
        if rem <= c:
            dp[rem] = t[rem - 1]
            continue
        best = INF
        for m in range(1, min(c, rem) + 1):
            for head_loaded in (False, True):
                avail = rem - m                # people the shuttles may ferry
                if avail <= 0:
                    continue
                cost = pre[m]                  # each shuttle rows back once
                idx = rem - 1                  # slowest person still on the near side
                left = avail
                moved = 0
                ok = True
                for _ in range(m - 1):         # m-1 passenger-only trips, capacity c
                    if left <= 0:
                        ok = False             # empty trip: covered by a smaller m
                        break
                    cost += t[idx]
                    take = min(c, left)
                    idx -= take
                    left -= take
                    moved += take
                if not ok:
                    continue
                if head_loaded and left > 0 and c - m > 0:
                    cost += t[idx]             # slowest passenger on the shuttle trip
                    take = min(c - m, left)
                    idx -= take
                    left -= take
                    moved += take
                else:
                    cost += t[m - 1]           # shuttles travel alone
                if moved == 0:
                    continue
                if dp[rem - moved] + cost < best:
                    best = dp[rem - moved] + cost
        dp[rem] = best
    return dp[n]


def main():
    # samples
    assert candidate([1, 2, 10, 5], 2) == 17, candidate([1, 2, 10, 5], 2)
    assert candidate([1, 2, 10, 5], 6) == 10
    print("samples OK")
    random.seed(20260912)
    bad = 0
    trials = 0
    for it in range(4000):
        n = random.randint(2, 8)
        c = random.randint(2, max(2, n + 1))
        hi = random.choice([3, 6, 20, 100])
        t = [random.randint(1, hi) for _ in range(n)]
        b = brute(t, c)
        a = candidate(t, c)
        trials += 1
        if a != b:
            bad += 1
            print("MISMATCH n=%d c=%d t=%s brute=%s cand=%s" % (n, c, sorted(t), b, a))
            if bad > 12:
                break
    print("random trials: %d, mismatches: %d" % (trials, bad))


if __name__ == "__main__":
    main()
