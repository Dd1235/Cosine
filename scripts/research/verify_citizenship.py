"""kattis-citizenship (ICPC WF 2024) -- derive + verify.

Model
-----
Calendar: every year has 365 days, month lengths fixed (no leap years).
So EVERY "12-month period" is exactly 365 days -> map each date to an
integer day index  idx(Y,M,D) = 365*Y + cum[M-1] + (D-1).

Applying on day A, the y periods are
    period k = [A - 365k, A - 365k + 364]   (k = 1..y)
(the example in the statement confirms period 1 = [A-1yr, A-1day]).

Let OUT be the union of the n closed travel intervals (disjoint & sorted
by the input guarantee).  Let f(x) = #OUT-days in [x, x+364].
Requirement: for all k in 1..y,  365 - f(A-365k) >= d, i.e.
    max_{k=1..y} f(A - 365k) <= C,   C = 365 - d.

A must satisfy A > last input date =: L.  And for A >= L + 1 + 365y every
period is entirely after L, so f = 0 <= C: the answer is in [L+1, L+1+365y],
a window of only 365y+1 <= 365001 candidates.

NOT monotone in A (a period can slide OFF a clean stretch ONTO a trip), so
binary searching the answer is invalid -- we scan.

Fast solve: prefix sums give f(x) in O(1).  The period starts for a fixed A
are A-365, A-730, ...: a block of y CONSECUTIVE terms of the stride-365
subsequence a_j = f(365j + r), r = A mod 365.  So per residue class r a
monotonic-deque sliding-window maximum of width y answers every A at once.
Total O(365y) time.
"""
import random
from collections import deque

MLEN = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
CUM = [0]
for _m in MLEN:
    CUM.append(CUM[-1] + _m)
assert CUM[12] == 365


def to_idx(s):
    y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
    return 365 * y + CUM[m - 1] + (d - 1)


def to_date(i):
    y, r = divmod(i, 365)
    m = 0
    while r >= MLEN[m]:
        r -= MLEN[m]
        m += 1
    return "%04d-%02d-%02d" % (y, m + 1, r + 1)


# ---------------------------------------------------------------- fast
def solve_fast(y, d, iv):
    C = 365 - d
    L = max(r for _, r in iv)
    lo, hi = L + 1, L + 1 + 365 * y
    base = lo - 365 * y            # smallest period start needed
    top = hi + 364                 # largest day ever probed (pad)
    N = top - base + 1
    diff = [0] * (N + 1)
    for l, r in iv:
        a, b = max(l, base), min(r, top)
        if a <= b:
            diff[a - base] += 1
            diff[b - base + 1] -= 1
    pre = [0] * (N + 1)            # pre[i] = #out days in base..base+i-1
    cur = 0
    for i in range(N):
        cur += diff[i]
        pre[i + 1] = pre[i] + (1 if cur > 0 else 0)

    def f(x):                      # out-days in [x, x+364]
        s = x - base
        return pre[s + 365] - pre[s]

    best = None
    for r in range(365):
        # A = 365*m + r, restricted to [lo, hi]
        m_min = (lo - r + 364) // 365
        m_max = (hi - r) // 365
        if m_min > m_max:
            continue
        dq = deque()               # indices j, a_j decreasing
        def push(j):
            v = f(365 * j + r)
            while dq and dq[-1][1] <= v:
                dq.pop()
            dq.append((j, v))
        for j in range(m_min - y, m_min):
            push(j)
        for m in range(m_min, m_max + 1):
            while dq and dq[0][0] < m - y:
                dq.popleft()
            if dq[0][1] <= C:
                A = 365 * m + r
                if best is None or A < best:
                    best = A
                break              # later A in this class are larger
            if m < m_max:
                push(m)
    return to_date(best)


# --------------------------------------------------------------- brute
def solve_brute(y, d, iv):
    """Independent: no prefix sums, counts every day of every period."""
    L = max(r for _, r in iv)
    A = L + 1
    while True:
        good = True
        for k in range(1, y + 1):
            st = A - 365 * k
            out = 0
            for day in range(st, st + 365):
                for l, r in iv:
                    if l <= day <= r:
                        out += 1
                        break
            if 365 - out < d:
                good = False
                break
        if good:
            return to_date(A)
        A += 1


def parse(txt):
    lines = txt.strip().splitlines()
    n, y, d = map(int, lines[0].split())
    iv = []
    for i in range(1, n + 1):
        a, b = lines[i].split()
        iv.append((to_idx(a), to_idx(b)))
    return y, d, iv


S1 = """3 5 240
2022-02-28 2022-10-01
2022-11-11 2022-11-11
2023-12-30 2024-01-01"""
S2 = """3 5 240
2011-11-11 2012-12-12
2022-02-28 2022-10-01
2025-01-01 2025-06-30"""

if __name__ == "__main__":
    # date round-trip sanity
    for i in range(0, 365 * 40, 7):
        assert to_idx(to_date(i)) == i, i
    assert to_date(to_idx("2024-05-31")) == "2024-05-31"

    for txt, exp in ((S1, "2024-05-31"), (S2, "2028-02-26")):
        got = solve_fast(*parse(txt))
        print("sample:", got, "expected", exp, "OK" if got == exp else "FAIL")
        assert got == exp
        assert solve_brute(*parse(txt)) == exp

    random.seed(1)
    for t in range(400):
        y = random.randint(1, 4)
        d = random.randint(1, 365)
        n = random.randint(1, 4)
        pts = sorted(random.sample(range(365 * 3, 365 * 8), 2 * n))
        iv = [(pts[2 * i], pts[2 * i + 1]) for i in range(n)]
        a, b = solve_fast(y, d, iv), solve_brute(y, d, iv)
        if a != b:
            print("MISMATCH", y, d, iv, a, b); raise SystemExit(1)
    print("400 random cross-checks passed")

    # dense/adversarial: many short trips, tight d
    random.seed(7)
    for t in range(150):
        y = random.randint(1, 3)
        d = random.randint(300, 365)
        n = random.randint(3, 6)
        pts = sorted(random.sample(range(365 * 2, 365 * 5), 2 * n))
        iv = [(pts[2 * i], pts[2 * i + 1]) for i in range(n)]
        a, b = solve_fast(y, d, iv), solve_brute(y, d, iv)
        if a != b:
            print("MISMATCH2", y, d, iv, a, b); raise SystemExit(1)
    print("150 adversarial cross-checks passed")

    # non-monotonicity of the predicate => binary-search-answer is INVALID
    iv = [(to_idx("0002-06-07"), to_idx("0002-08-10")),
          (to_idx("0005-01-02"), to_idx("0005-05-14"))]
    y, d, C = 2, 279, 365 - 279
    L = max(r for _, r in iv)
    def out_in(x):
        return sum(1 for day in range(x, x + 365)
                   for l, r in iv if l <= day <= r)
    feas = lambda A: all(out_in(A - 365 * k) <= C for k in range(1, y + 1))
    assert feas(to_idx("0006-03-29")) and not feas(to_idx("0006-03-30"))
    assert solve_fast(y, d, iv) == "0006-02-18" == solve_brute(y, d, iv)
    print("predicate is NOT monotone: feasible 0006-03-29, infeasible 0006-03-30,"
          " answer 0006-02-18 -> cannot binary search the date")

    # worst case (n=500, y=1000, dates up to year 5000): O(365y) holds
    import time
    random.seed(11)
    pts = sorted(random.sample(range(365 * 4000, 365 * 5001 - 1), 1000))
    iv = [(pts[2 * i], pts[2 * i + 1]) for i in range(500)]
    t0 = time.time()
    ans = solve_fast(1000, 365, iv)
    print("worst case n=500 y=1000 d=365 ->", ans,
          "in %.2fs (pure python)" % (time.time() - t0))
    # d=365 forces the proven upper bound L+1+365y exactly
    assert ans == to_date(max(r for _, r in iv) + 1 + 365 * 1000)
