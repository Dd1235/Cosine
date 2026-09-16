"""Brute force check for kattis-playingwithnumbers.

Claim being tested (the O(N) solution):
  numbers are (a,b) = 2^a 3^b; gcd = componentwise min, lcm = componentwise max.
  With exactly k gcd-ops and N-1-k lcm-ops in a binary combining tree,

    MAX(k) = cmax(V)                                  if k <= N-3
           = max_u value( cmax(u, cmin(V \ {u})) )    if k == N-2
           = cmin(V)                                  if k == N-1
    MIN(k) with j = N-1-k lcm-ops, dually
           = cmin(V)                                  if j <= N-3
           = min_u value( cmin(u, cmax(V \ {u})) )    if j == N-2
           = cmax(V)                                  if j == N-1

The brute force enumerates every combining tree for small N and compares the
achievable maxima/minima per k, with values compared as exact integers 2^a 3^b.
"""
import itertools
import random
from functools import lru_cache


def val(p):
    return (2 ** p[0]) * (3 ** p[1])


def cmin(ps):
    return (min(p[0] for p in ps), min(p[1] for p in ps))


def cmax(ps):
    return (max(p[0] for p in ps), max(p[1] for p in ps))


def solve(elems):
    """The O(N log N) solution: returns list over k of (maxpair, minpair).

    A tree with k gcd-ops and N-1-k lcm-ops whose top is an lcm realises exactly
    "partition V into m = N-k blocks, take cmin of each block, cmax the blocks";
    dually for the minimum with m = k+1 blocks (cmax inside, cmin on top).
    m >= 3 lets two singleton blocks carry the two coordinate maxima, so the
    answer is the global cmax; m == 1 is the global cmin; only m == 2 is work,
    and there the Pareto frontier is swept by a-sorted prefixes plus singletons.
    """
    n = len(elems)
    CM, Cm = cmax(elems), cmin(elems)

    def two_block(best_dir):
        """best_dir=+1: maximise value(cmax(cmin P, cmin Q)).
           best_dir=-1: minimise value(cmin(cmax P, cmax Q))."""
        inner = cmin if best_dir > 0 else cmax
        outer = cmax if best_dir > 0 else cmin
        cand = []
        order = sorted(range(n), key=lambda i: elems[i][0], reverse=(best_dir < 0))
        arr = [elems[i] for i in order]
        pre = [None] * (n + 1)
        suf = [None] * (n + 1)
        pre[0] = None
        for i, e in enumerate(arr):
            pre[i + 1] = e if pre[i] is None else inner([pre[i], e])
        suf[n] = None
        for i in range(n - 1, -1, -1):
            suf[i] = arr[i] if suf[i + 1] is None else inner([arr[i], suf[i + 1]])
        for i in range(1, n):
            cand.append(outer([pre[i], suf[i]]))
        # singleton blocks: {e} against the rest
        gpre = [None] * (n + 1)
        gsuf = [None] * (n + 1)
        for i, e in enumerate(elems):
            gpre[i + 1] = e if gpre[i] is None else inner([gpre[i], e])
        for i in range(n - 1, -1, -1):
            gsuf[i] = elems[i] if gsuf[i + 1] is None else inner([elems[i], gsuf[i + 1]])
        for u in range(n):
            rest = gpre[u] if gsuf[u + 1] is None else (
                gsuf[u + 1] if gpre[u] is None else inner([gpre[u], gsuf[u + 1]]))
            if rest is None:
                continue
            cand.append(outer([elems[u], rest]))
        return (max if best_dir > 0 else min)(cand, key=val)

    out = []
    for k in range(n):
        m_max = n - k          # blocks for the maximum scenario
        m_min = k + 1          # blocks for the minimum scenario
        if m_max >= 3:
            mx = CM
        elif m_max == 2:
            mx = two_block(+1)
        else:
            mx = Cm
        if m_min >= 3:
            mn = Cm
        elif m_min == 2:
            mn = two_block(-1)
        else:
            mn = CM
        out.append((mx, mn))
    return out


@lru_cache(maxsize=None)
def brute(state):
    """state: sorted tuple of pairs. returns dict k -> frozenset of results."""
    if len(state) == 1:
        return {0: frozenset([state[0]])}
    res = {}
    lst = list(state)
    for i in range(len(lst)):
        for jj in range(i + 1, len(lst)):
            x, y = lst[i], lst[jj]
            rest = lst[:i] + lst[i + 1:jj] + lst[jj + 1:]
            for op, isgcd in ((lambda a, b: (min(a[0], b[0]), min(a[1], b[1])), 1),
                              (lambda a, b: (max(a[0], b[0]), max(a[1], b[1])), 0)):
                z = op(x, y)
                sub = brute(tuple(sorted(rest + [z])))
                for k, s in sub.items():
                    kk = k + isgcd
                    res.setdefault(kk, set()).update(s)
    return {k: frozenset(v) for k, v in res.items()}


def main():
    random.seed(7)
    # statement sample
    sample = [(0, 0), (1, 2), (2, 0)]
    got = solve(sample)
    exp = [((2, 2), (2, 2)), ((1, 2), (0, 0)), ((0, 0), (0, 0))]
    assert got == exp, (got, exp)
    print("sample 1 OK")

    bad = 0
    for trial in range(600):
        n = random.randint(1, 6)
        hi = random.choice([1, 2, 3, 4])
        elems = [(random.randint(0, hi), random.randint(0, hi)) for _ in range(n)]
        mine = solve(elems)
        b = brute(tuple(sorted(elems)))
        for k in range(n):
            achievable = b[k]
            bmax = max(achievable, key=val)
            bmin = min(achievable, key=val)
            if val(mine[k][0]) != val(bmax) or val(mine[k][1]) != val(bmin):
                bad += 1
                print("MISMATCH", elems, "k=", k, "mine", mine[k], "brute", bmax, bmin)
                if bad > 5:
                    return
    print("random trials OK" if bad == 0 else "FAILURES: %d" % bad)


if __name__ == "__main__":
    main()
