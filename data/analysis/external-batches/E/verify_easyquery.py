"""kattis-easyquery -- verification.

Array a[1..n] (a_i <= 1e9).  Query (l, r, u, v): sort a[l..r] into s, look at
the window s[u..v]; t^(i) is the SET of values occurring at least i times in
that window; answer = OR(t^1) + OR(t^2) + OR(t^3)   (OR of the empty set = 0).
sum n, sum q <= 2e5 over all test cases.

brute(...)   -- sort the slice, count, ground truth.

fast(...)    -- the intended solution:

  Let L = s[u] and R = s[v] (u-th and v-th order statistic of a[l..r]).
  If L == R the window is one value repeated v-u+1 times.  Otherwise every
  value x with L < x < R has its WHOLE multiplicity inside the window (its
  sorted block sits strictly between L's block, which reaches position u, and
  R's block, which starts at or before v), so its window count equals its count
  in a[l..r]; only L and R are clipped, and their clipped counts come from two
  rank queries.  So the work splits into O(1) boundary arithmetic plus

      for i = 1,2,3:  OR of all x with L < x < R and cnt_[l,r](x) >= i.

  The published editorial reaches L and R with a wavelet tree; a persistent
  segment tree over the compressed values (used here) answers the same order
  statistic, rank and multiplicity queries, so the wavelet tree is replaceable.

  For the OR, bits are independent: bit k is set in the answer for level i iff
  SOME qualifying x has bit k.  Sweep the queries in decreasing l; maintain
  Mi[x] = position of the i-th occurrence of x at index >= l (INF if none), so
  "x occurs >= i times in [l,r]" is exactly Mi[x] <= r.  Advancing l by one
  shifts M1->M2->M3 for a single value.  For each (i, k) keep a segment tree
  over the compressed value axis holding min Mi[x] over the x that have bit k
  set; the query is one range-min over the compressed range strictly between L
  and R, compared against r.  3*30 trees, O(1) point update and O(log n) query
  each.  Time O(30 (n + q) log n), space O(30 n).
"""
import random
import sys
from bisect import bisect_left

BITS = 30
INF = float('inf')


# ------------------------------------------------------------------ brute
def brute(a, queries):
    out = []
    for (l, r, u, v) in queries:
        s = sorted(a[l - 1:r])
        win = s[u - 1:v]
        cnt = {}
        for x in win:
            cnt[x] = cnt.get(x, 0) + 1
        tot = 0
        for i in (1, 2, 3):
            o = 0
            for x, c in cnt.items():
                if c >= i:
                    o |= x
            tot += o
        out.append(tot)
    return out


# ------------------------------------------ persistent segment tree (values)
class Persistent:
    def __init__(self, comp_seq, m):
        self.m = m
        self.lc = [0]
        self.rc = [0]
        self.cn = [0]
        self.roots = [0]
        for ci in comp_seq:
            self.roots.append(self._upd(self.roots[-1], 0, m - 1, ci))

    def _new(self, l, r, c):
        self.lc.append(l)
        self.rc.append(r)
        self.cn.append(c)
        return len(self.cn) - 1

    def _upd(self, prev, lo, hi, pos):
        if lo == hi:
            return self._new(0, 0, self.cn[prev] + 1)
        mid = (lo + hi) // 2
        if pos <= mid:
            return self._new(self._upd(self.lc[prev], lo, mid, pos),
                             self.rc[prev], self.cn[prev] + 1)
        return self._new(self.lc[prev],
                         self._upd(self.rc[prev], mid + 1, hi, pos),
                         self.cn[prev] + 1)

    def kth(self, l, r, k):                  # k-th smallest (1-based) in a[l..r]
        x, y = self.roots[l - 1], self.roots[r]
        lo, hi = 0, self.m - 1
        while lo < hi:
            mid = (lo + hi) // 2
            c = self.cn[self.lc[y]] - self.cn[self.lc[x]]
            if k <= c:
                x, y, hi = self.lc[x], self.lc[y], mid
            else:
                k -= c
                x, y, lo = self.rc[x], self.rc[y], mid + 1
        return lo                            # compressed index

    def count(self, l, r, ql, qr):           # #{i in [l,r] : comp[i] in [ql,qr]}
        if ql > qr:
            return 0
        return self._cnt(self.roots[r], 0, self.m - 1, ql, qr) - \
               self._cnt(self.roots[l - 1], 0, self.m - 1, ql, qr)

    def _cnt(self, node, lo, hi, ql, qr):
        if node == 0 or qr < lo or hi < ql:
            return 0
        if ql <= lo and hi <= qr:
            return self.cn[node]
        mid = (lo + hi) // 2
        return self._cnt(self.lc[node], lo, mid, ql, qr) + \
               self._cnt(self.rc[node], mid + 1, hi, ql, qr)


# ------------------------------------------------------------- min seg tree
class SegMin:
    __slots__ = ('n', 't')

    def __init__(self, n):
        self.n = n
        self.t = [INF] * (2 * n)

    def chmin(self, i, val):
        i += self.n
        if self.t[i] <= val:
            return
        self.t[i] = val
        i >>= 1
        while i:
            nv = min(self.t[2 * i], self.t[2 * i + 1])
            if self.t[i] == nv:
                break
            self.t[i] = nv
            i >>= 1

    def query(self, l, r):                   # inclusive
        if l > r:
            return INF
        res = INF
        l += self.n
        r += self.n + 1
        while l < r:
            if l & 1:
                if self.t[l] < res:
                    res = self.t[l]
                l += 1
            if r & 1:
                r -= 1
                if self.t[r] < res:
                    res = self.t[r]
            l >>= 1
            r >>= 1
        return res


# ------------------------------------------------------------------- fast
def fast(a, queries):
    n = len(a)
    vals = sorted(set(a))
    m = len(vals)
    comp = [bisect_left(vals, x) for x in a]
    ps = Persistent(comp, m)

    nq = len(queries)
    ans = [0] * nq
    done = [False] * nq                      # answered without the sweep
    mid_lo = [0] * nq
    mid_hi = [-1] * nq
    base = [(0, 0, 0)] * nq                  # per-level OR contributed by L and R
    for qi, (l, r, u, v) in enumerate(queries):
        cl = ps.kth(l, r, u)
        cr = ps.kth(l, r, v)
        L, R = vals[cl], vals[cr]
        if cl == cr:
            c = v - u + 1
            ans[qi] = sum(L for i in (1, 2, 3) if c >= i)
            done[qi] = True
            continue
        lessL = ps.count(l, r, 0, cl - 1)
        cntL = ps.count(l, r, cl, cl)
        loL, hiL = lessL + 1, lessL + cntL
        aL = max(0, min(v, hiL) - max(u, loL) + 1)
        lessR = ps.count(l, r, 0, cr - 1)
        cntR = ps.count(l, r, cr, cr)
        loR, hiR = lessR + 1, lessR + cntR
        aR = max(0, min(v, hiR) - max(u, loR) + 1)
        base[qi] = tuple((L if aL >= i else 0) | (R if aR >= i else 0)
                         for i in (1, 2, 3))
        mid_lo[qi], mid_hi[qi] = cl + 1, cr - 1

    # offline sweep over decreasing l
    trees = [[SegMin(m) for _ in range(BITS)] for _ in range(3)]
    M = [[INF] * m for _ in range(3)]
    by_l = [[] for _ in range(n + 2)]
    for qi, (l, r, u, v) in enumerate(queries):
        if not done[qi]:
            by_l[l].append(qi)

    for l in range(n, 0, -1):
        cx = comp[l - 1]
        M[2][cx] = M[1][cx]
        M[1][cx] = M[0][cx]
        M[0][cx] = l
        x = a[l - 1]
        for k in range(BITS):
            if x >> k & 1:
                for i in range(3):
                    if M[i][cx] is not INF:
                        trees[i][k].chmin(cx, M[i][cx])
        for qi in by_l[l]:
            r = queries[qi][1]
            lo, hi = mid_lo[qi], mid_hi[qi]
            tot = 0
            for i in range(3):
                o = base[qi][i]
                if lo <= hi:
                    for k in range(BITS):
                        if o >> k & 1:
                            continue
                        if trees[i][k].query(lo, hi) <= r:
                            o |= 1 << k
                tot += o
            ans[qi] = tot
    return ans


# ------------------------------------------------------------------ driver
def main():
    a = [123, 3, 2, 2, 7, 2, 1, 5, 5, 7, 456]
    qs = [(2, 10, 2, 8), (1, 1, 1, 1), (1, 4, 1, 3)]
    want = [16, 123, 5]
    assert brute(a, qs) == want, brute(a, qs)
    got = fast(a, qs)
    assert got == want, got
    print("sample OK ->", got)

    rng = random.Random(20260913)
    for it in range(3000):
        n = rng.randint(1, 12)
        hi = rng.choice([1, 2, 3, 4, 8, 40, 10 ** 9])
        a = [rng.randint(1, hi) for _ in range(n)]
        qs = []
        for _ in range(rng.randint(1, 8)):
            l = rng.randint(1, n)
            r = rng.randint(l, n)
            u = rng.randint(1, r - l + 1)
            v = rng.randint(u, r - l + 1)
            qs.append((l, r, u, v))
        b, f = brute(a, qs), fast(a, qs)
        if b != f:
            print("MISMATCH")
            print("a =", a)
            print("q =", qs)
            print("brute", b)
            print("fast ", f)
            sys.exit(1)
    print("random small: 3000 arrays x up to 8 queries, fast == brute")

    for it in range(200):
        n = rng.randint(20, 80)
        hi = rng.choice([2, 3, 5, 1000, 10 ** 9])
        a = [rng.randint(1, hi) for _ in range(n)]
        qs = []
        for _ in range(30):
            l = rng.randint(1, n)
            r = rng.randint(l, n)
            u = rng.randint(1, r - l + 1)
            v = rng.randint(u, r - l + 1)
            qs.append((l, r, u, v))
        if brute(a, qs) != fast(a, qs):
            print("MISMATCH medium")
            print("a =", a)
            print("q =", qs)
            sys.exit(1)
    print("random medium: 200 arrays x 30 queries, fast == brute")

    # shapes that stress the boundary clipping: many duplicates, u==v,
    # windows entirely inside one value's block, full-range windows
    for it in range(1500):
        n = rng.randint(2, 14)
        a = [rng.choice([1, 1, 1, 2, 2, 6, 7]) for _ in range(n)]
        qs = []
        for _ in range(10):
            l = rng.randint(1, n)
            r = rng.randint(l, n)
            w = r - l + 1
            style = rng.randrange(4)
            if style == 0:
                u = v = rng.randint(1, w)
            elif style == 1:
                u, v = 1, w
            else:
                u = rng.randint(1, w)
                v = rng.randint(u, w)
            qs.append((l, r, u, v))
        if brute(a, qs) != fast(a, qs):
            print("MISMATCH dup-heavy")
            print("a =", a)
            print("q =", qs)
            sys.exit(1)
    print("duplicate-heavy / boundary shapes: 1500 cases OK")
    print("NOTE: the C++ cost is O(30 (n+q) log n) time, O(30 n) memory; this "
          "Python transcription is the same algorithm, run only at small n.")


if __name__ == "__main__":
    main()
