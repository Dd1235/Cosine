"""Divide Doughnut: run the solver against a simulated interactor and count queries.

f(x) = #sprinkles in the half-circle [x, x+HALF-1].  f(x+1)-f(x) is in {-1,0,1}
(one part leaves, one enters) and f(x) + f(x+HALF) = N, so g = f - N/2 satisfies
g(x+HALF) = -g(x): a discrete intermediate-value argument makes a zero always
exist, so the answer is never NO.  Binary search keeps a window [L,R] with
g(L)>=0, g(R)<=0; a probe value v at mid moves L to mid+v (v>0) or R to mid-|v|
(v<0), which is what keeps the worst case inside the 30 + floor(log2(sqrt N))
interaction budget.
"""
import bisect
import math
import random

M = 10 ** 9
HALF = M // 2


class Interactor:
    def __init__(self, pts):
        self.p = sorted(pts)
        self.n = len(self.p)
        self.q = 0

    def _pref(self, v):          # count of sprinkles in [0, v]
        return bisect.bisect_right(self.p, v)

    def query(self, u, v):
        self.q += 1
        if u <= v:
            return self._pref(v) - self._pref(u - 1)
        return self.n - self._pref(u - 1) + self._pref(v)


def solve(N, io):
    half = N // 2

    def g(x):
        x %= M
        return io.query(x, (x + HALF - 1) % M) - half

    v0 = g(0)
    if v0 == 0:
        return 0
    if v0 > 0:
        lo, hi, a, c = 0, HALF, v0, v0
    else:
        lo, hi, a, c = HALF, M, -v0, -v0
    L, R = lo + a, hi - c
    while L < R:
        mid = (L + R) // 2
        v = g(mid)
        if v == 0:
            return mid % M
        if v > 0:
            L = mid + v
        else:
            R = mid + v          # v < 0
    return L % M


def check(pts, N):
    io = Interactor(pts)
    x = solve(N, io)
    cnt = io.query(x, (x + HALF - 1) % M)     # audit query, not counted below
    io.q -= 1
    budget = 30 + int(math.floor(math.log2(math.sqrt(N))))
    assert cnt == N // 2, (N, cnt, x)
    assert io.q + 1 <= budget, (N, io.q + 1, budget)
    return io.q + 1


def main():
    random.seed(3)
    worst = {}
    for trial in range(4000):
        N = random.choice([2, 2, 2, 4, 6, 10, 100, 1000, 99998, 100000])
        if trial % 3 == 0:                     # clustered
            base = random.randrange(M)
            pts = set((base + random.randrange(0, 3000)) % M for _ in range(N))
            while len(pts) < N:
                pts.add(random.randrange(M))
        else:
            pts = set()
            while len(pts) < N:
                pts.add(random.randrange(M))
        used = check(sorted(pts), N)
        worst[N] = max(worst.get(N, 0), used)
    for N in sorted(worst):
        print("  N=%-7d worst interactions=%d  budget=%d"
              % (N, worst[N], 30 + int(math.floor(math.log2(math.sqrt(N))))))
    print("4000 simulated interactions ok, always answered YES correctly")


main()
