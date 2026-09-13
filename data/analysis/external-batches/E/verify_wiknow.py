"""kattis-wiknow -- verification.

Sequence S of N positive integers <= N.  Find the lexicographically smallest
ordered pair (A, B), A != B, such that A,B,A,B occurs as a subsequence, i.e.
indices c<d<e<f with S[c]=S[e]=A, S[d]=S[f]=B.  Print -1 if none.  N <= 4e5.

Implementations:
  brute(S)  -- O(N^4) over all index quadruples, tiny N only.
  fast(S)   -- O(N log N).  Key reduction (the judges' debrief only argues
               existence, not lexicographic minimality, so the minimality
               argument below is ours):

               (A,B) is achievable  iff  there are indices p<u<q with
               p,q CONSECUTIVE occurrences of A and imax(S[u]) > q,
               where imax(x) = last occurrence of x.

               (=>) given c<d<e<f, let p = last occurrence of A before d and
                    q = its successor occurrence; then p<d<q<=e<f<=imax(B),
                    and u=d lies strictly between the consecutive pair p,q.
               (<=) p<u<q<imax(S[u]) with S[p]=S[q]=A, S[u]=B!=A is literally
                    a witness quadruple.

               So A is achievable iff some consecutive-occurrence gap (p,q) of
               A contains a u with IM[u] > q, where IM[u] = imax(S[u]); that is
               one range-maximum query per gap, O(N) queries in total over all
               values (sum of occurrence counts = N).  A sparse table answers
               each in O(1).  Then for the winning A only, a single linear scan
               over [first(A), last(A)] finds the smallest qualifying B.
               Time O(N log N), space O(N log N) (sparse table).
"""
import random
import sys


# ------------------------------------------------------------------ brute
def brute(S):
    n = len(S)
    best = None
    for c in range(n):
        for d in range(c + 1, n):
            if S[c] == S[d]:
                continue
            for e in range(d + 1, n):
                if S[e] != S[c]:
                    continue
                for f in range(e + 1, n):
                    if S[f] == S[d]:
                        cand = (S[c], S[d])
                        if best is None or cand < best:
                            best = cand
    return best


# ------------------------------------------------------------------- fast
class SparseMax:
    def __init__(self, a):
        self.a = a
        n = len(a)
        self.log = [0] * (n + 1)
        for i in range(2, n + 1):
            self.log[i] = self.log[i >> 1] + 1
        k = self.log[n] + 1 if n else 1
        self.t = [a[:]]
        j = 1
        while (1 << j) <= n:
            prev = self.t[-1]
            cur = [0] * (n - (1 << j) + 1)
            half = 1 << (j - 1)
            for i in range(len(cur)):
                x = prev[i]
                y = prev[i + half]
                cur[i] = x if x > y else y
            self.t.append(cur)
            j += 1

    def query(self, lo, hi):          # inclusive, 0-based; lo>hi -> -1
        if lo > hi:
            return -1
        j = self.log[hi - lo + 1]
        x = self.t[j][lo]
        y = self.t[j][hi - (1 << j) + 1]
        return x if x > y else y


def fast(S):
    n = len(S)
    if n < 4:
        return None
    occ = {}
    for i, x in enumerate(S):
        occ.setdefault(x, []).append(i)
    imax = {x: v[-1] for x, v in occ.items()}
    IM = [imax[x] for x in S]
    sp = SparseMax(IM)

    bestA = None
    for x, ps in occ.items():
        if len(ps) < 2:
            continue
        if bestA is not None and x > bestA:
            continue
        ok = False
        for t in range(len(ps) - 1):
            p, q = ps[t], ps[t + 1]
            if p + 1 <= q - 1 and sp.query(p + 1, q - 1) > q:
                ok = True
                break
        if ok and (bestA is None or x < bestA):
            bestA = x
    if bestA is None:
        return None

    ps = occ[bestA]
    bestB = None
    t = 0                              # ps[t] = last occurrence of A seen
    for u in range(ps[0] + 1, ps[-1]):
        while ps[t + 1] < u:
            t += 1
        if ps[t + 1] == u:             # u is itself an occurrence of A
            continue
        q = ps[t + 1]
        b = S[u]
        if imax[b] > q and (bestB is None or b < bestB):
            bestB = b
    assert bestB is not None
    return (bestA, bestB)


# ------------------------------------------------------------------ driver
def fmt(r):
    return "-1" if r is None else "%d %d" % r


SAMPLES = [
    ([1, 3, 2, 4, 1, 5, 2, 4], "1 2"),
    ([1, 2, 3, 4, 5, 6, 7, 1], "-1"),
    ([2, 1, 2, 1], "2 1"),
]


def main():
    for S, want in SAMPLES:
        got = fmt(fast(S))
        assert got == want, (S, got, want)
        assert fmt(brute(S)) == want, (S, fmt(brute(S)), want)
    print("samples OK (%d)" % len(SAMPLES))

    random.seed(20260913)
    for it in range(40000):
        n = random.randint(4, 11)
        hi = random.choice([2, 3, 4, n])
        S = [random.randint(1, min(hi, n)) for _ in range(n)]
        b, f = brute(S), fast(S)
        if b != f:
            print("MISMATCH", S, "brute", b, "fast", f)
            sys.exit(1)
    print("random small: 40000 cases, fast == brute")

    # larger randoms against an O(N^2) reference built from the same
    # reduction but with an independent (naive) minimality search
    def ref(S):
        n = len(S)
        occ = {}
        for i, x in enumerate(S):
            occ.setdefault(x, []).append(i)
        imax = {x: v[-1] for x, v in occ.items()}
        best = None
        for i in range(n):
            for u in range(i + 1, n):
                if S[u] == S[i]:
                    continue
                # need j>u with S[j]==S[i] and imax[S[u]]>j
                for j in range(u + 1, n):
                    if S[j] == S[i] and imax[S[u]] > j:
                        cand = (S[i], S[u])
                        if best is None or cand < best:
                            best = cand
                        break
        return best

    for it in range(400):
        n = random.randint(4, 60)
        hi = random.choice([2, 3, 5, 8, n])
        S = [random.randint(1, min(hi, n)) for _ in range(n)]
        if ref(S) != fast(S):
            print("MISMATCH(ref)", S, ref(S), fast(S))
            sys.exit(1)
    print("random medium: 400 cases, fast == O(N^3) reference")

    # stress the adversarial shapes: one value spanning the whole array
    for it in range(2000):
        n = random.randint(6, 40)
        S = [random.randint(2, 4) for _ in range(n)]
        S[0] = 1
        S[-1] = 1
        if brute(S) != fast(S) if n <= 11 else ref(S) != fast(S):
            print("MISMATCH(span)", S)
            sys.exit(1)
    print("spanning-value shapes OK")

    # scale check
    import time
    n = 400000
    S = [random.randint(1, n) for _ in range(n)]
    t0 = time.time()
    fast(S)
    print("N=400000 random: %.2fs" % (time.time() - t0))
    S = [random.randint(1, 3) for _ in range(n)]
    t0 = time.time()
    print("N=400000 few-values ->", fmt(fast(S)), "%.2fs" % (time.time() - t0))
    S = list(range(1, n + 1))          # all distinct -> -1, worst for gaps
    t0 = time.time()
    print("N=400000 all-distinct ->", fmt(fast(S)), "%.2fs" % (time.time() - t0))
    # worst case for the per-A scan: two values, huge span
    S = [1] + [2, 3] * ((n - 2) // 2) + [1]
    S = S[:n]
    t0 = time.time()
    print("N=%d span-worst ->" % len(S), fmt(fast(S)),
          "%.2fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
