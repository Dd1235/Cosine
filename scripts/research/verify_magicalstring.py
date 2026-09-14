#!/usr/bin/env python3
"""Verification for kattis-magicalstring (2018 ICPC Asia Singapore Regional, problem U).

Ground truth (`brute`) is a literal simulator of the statement: repeatedly pick a live
position and a replacement letter, require that the maximal run of identical letters through
that position becomes >= 3, replace that whole run by one '*', and recurse, for at most K
operations, maximising the number of characters absorbed into asterisks.

Claim under test (`fast`)
-------------------------
Because characters are never left in a changed state (the changed one is absorbed into the
'*' immediately) and '*' never merges with anything, every operation collapses an interval
of the ORIGINAL string, and the collapsed intervals are pairwise disjoint.  An interval
[l, r] is collapsible at all iff 3 <= r-l+1 <= 5 and exactly one position in it differs from
the common letter x of the rest (lengths 4 and 5 are limited to x x z x / x z x x / x x z x x
because S itself has no run of 3).  Maximality of the run adds an ORDERING constraint:
  needL([l,r]) = (l > 0 and S[l-1] == x)  -- position l-1 must already be a '*', so the
                 chosen interval ending at l-1 must be collapsed first;
  needR([l,r]) = (r < n-1 and S[r+1] == x) -- symmetric.
So the answer is: choose at most K pairwise disjoint collapsible intervals maximising total
length, subject to (i) an interval with needL has a chosen neighbour ending exactly at l-1,
(ii) likewise on the right, (iii) no adjacent pair where the left one has needR and the right
one has needL (that is a 2-cycle in the ordering and is unsatisfiable).  Any other dependency
pattern is a DAG along the chain of adjacent intervals, hence schedulable.  A left-to-right
DP with state (next free position, operations used, b) where b is 0 = nothing ends here,
1 = an interval ends here and does not need its right neighbour, 2 = it does, enforces all
three.  Since every interval eats >= 3 characters, only min(K, n//3) operations matter, so
the DP is O(n * min(K, n/3)) time and memory.

`wisp` is the published debrief's formulation (weighted interval scheduling with a cap of K
over SINGLE plus cut-down "EXTEND" intervals), kept here to compare it with the ground truth.
"""
import random
import sys
from functools import lru_cache

# --------------------------------------------------------------- ground truth
def collapse(s, i, x):
    """Apply 'change s[i] to x'.  Return (new string, absorbed) or None if illegal."""
    if s[i] == '*' or s[i] == x:
        return None
    n = len(s)
    l = i - 1
    while l >= 0 and s[l] == x:
        l -= 1
    r = i + 1
    while r < n and s[r] == x:
        r += 1
    ln = r - l - 1          # run is s[l+1 .. r-1] after the change
    if ln < 3:
        return None
    return s[:l + 1] + '*' + s[r:], ln


def brute(S, K):
    """Exhaustive search over operation sequences."""
    @lru_cache(maxsize=None)
    def go(s, k):
        best = 0
        if k == 0:
            return 0
        letters = set(ch for ch in s if ch != '*')
        for i, c in enumerate(s):
            if c == '*':
                continue
            for x in letters:
                res = collapse(s, i, x)
                if res is None:
                    continue
                ns, gain = res
                v = gain + go(ns, k - 1)
                if v > best:
                    best = v
        return best
    out = go(S, min(K, len(S) // 3))
    go.cache_clear()
    return out


# --------------------------------------------------------------------- claim
def candidates(S):
    """All collapsible intervals as (l, r, needL, needR)."""
    n = len(S)
    out = []
    for l in range(n):
        for L in (3, 4, 5):
            r = l + L - 1
            if r >= n:
                break
            sub = S[l:r + 1]
            x = None
            for m in range(L):                      # m = index of the odd one out
                rest = sub[:m] + sub[m + 1:]
                if len(set(rest)) == 1 and rest[0] != sub[m]:
                    x = rest[0]
                    break
            if x is None:
                continue
            needL = l > 0 and S[l - 1] == x
            needR = r < n - 1 and S[r + 1] == x
            out.append((l, r, needL, needR))
    return out


def fast(S, K):
    n = len(S)
    J = min(K, n // 3)
    if J == 0:
        return 0
    starts = [[] for _ in range(n)]
    for (l, r, nl, nr) in candidates(S):
        starts[l].append((r, nl, nr))
    W = (J + 1) * 3                       # flat dp indexed by (i * W + j * 3 + b)
    NEG = -1
    dp = [NEG] * ((n + 1) * W)
    dp[0] = 0
    for i in range(n):
        base = i * W
        nxt = base + W
        st = starts[i]
        for j in range(J + 1):
            o = base + j * 3
            for b in range(3):
                cur = dp[o + b]
                if cur < 0:
                    continue
                if b != 2:                                   # leave position i uncovered
                    t = nxt + j * 3
                    if cur > dp[t]:
                        dp[t] = cur
                if j == J:
                    continue
                for (r, nl, nr) in st:
                    if nl and b != 1:
                        continue    # b == 0: no blocker;  b == 2: mutual deadlock
                    t = (r + 1) * W + (j + 1) * 3 + (2 if nr else 1)
                    v = cur + (r - i + 1)
                    if v > dp[t]:
                        dp[t] = v
    best = 0
    base = n * W
    for j in range(J + 1):
        for b in (0, 1):
            v = dp[base + j * 3 + b]
            if v > best:
                best = v
    return best


# ------------------------------------------------- the debrief's formulation
def wisp(S, K):
    """SINGLE = intervals with no ordering need; EXTEND = SINGLE plus every >=3 piece of a
    SINGLE interval whose cut ends abut another SINGLE interval.  Then weighted interval
    scheduling with at most K intervals, ignoring whether the cutter is actually chosen."""
    n = len(S)
    cand = candidates(S)
    single = [(l, r) for (l, r, nl, nr) in cand if not nl and not nr]
    endsAt = set(r for (l, r) in single)
    startsAt = set(l for (l, r) in single)
    ext = set()
    for (L, R) in single:
        for a in range(L, R + 1):
            for b in range(a + 2, R + 1):
                if (a == L or (a - 1) in endsAt) and (b == R or (b + 1) in startsAt):
                    ext.add((a, b))
    J = min(K, n // 3)
    by_start = [[] for _ in range(n + 1)]
    for (a, b) in ext:
        by_start[a].append(b)
    dp = [[-1] * (J + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(n):
        for j in range(J + 1):
            if dp[i][j] < 0:
                continue
            if dp[i][j] > dp[i + 1][j]:
                dp[i + 1][j] = dp[i][j]
            if j < J:
                for b in by_start[i]:
                    if dp[i][j] + (b - i + 1) > dp[b + 1][j + 1]:
                        dp[b + 1][j + 1] = dp[i][j] + (b - i + 1)
    return max(max(row) for row in dp)


def naive(S, K):
    """The tempting WRONG relaxation: take any collapsible intervals, disjoint, ignoring the
    ordering constraints entirely.  Kept to document why the constraints are load-bearing."""
    n = len(S)
    J = min(K, n // 3)
    by_start = [[] for _ in range(n + 1)]
    for (l, r, nl, nr) in candidates(S):
        by_start[l].append(r)
    dp = [[-1] * (J + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(n):
        for j in range(J + 1):
            if dp[i][j] < 0:
                continue
            if dp[i][j] > dp[i + 1][j]:
                dp[i + 1][j] = dp[i][j]
            if j < J:
                for r in by_start[i]:
                    if dp[i][j] + (r - i + 1) > dp[r + 1][j + 1]:
                        dp[r + 1][j + 1] = dp[i][j] + (r - i + 1)
    return max(max(row) for row in dp)


def trap():
    """S = aababb, K = 2.  [0,2] = 'aab' needs position 3 collapsed first (S[3] = 'a' would
    extend the run) and [3,5] = 'abb' needs position 2 collapsed first, so the two deadlock
    each other and only one 4-long interval is really available."""
    s, k = "aababb", 2
    g, f, w, nv = brute(s, k), fast(s, k), wisp(s, k), naive(s, k)
    print("  S=%s K=%d  brute=%d fast=%d wisp=%d  naive-relaxation=%d (over-counts)" % (s, k, g, f, w, nv))
    return g == f == w == 4 and nv == 6


# --------------------------------------------------------------------- tests
def magical(s):
    return all(not (i >= 2 and s[i] == s[i - 1] == s[i - 2]) for i in range(len(s)))


def rand_magical(rnd, n, alpha):
    """Uniform over magical strings, by rejection -- only usable for small n."""
    while True:
        s = "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz"[:alpha]) for _ in range(n))
        if magical(s):
            return s


def rand_magical_runs(rnd, n, alpha):
    """Magical string of length exactly n, built run by run (rejection dies for large n)."""
    letters = "abcdefghijklmnopqrstuvwxyz"[:alpha]
    out = []
    prev = None
    while len(out) < n:
        c = rnd.choice([x for x in letters if x != prev])
        for _ in range(min(rnd.randint(1, 2), n - len(out))):
            out.append(c)
        prev = c
    s = "".join(out)
    assert magical(s) and len(s) == n
    return s


def samples():
    cases = [("cabacbc", 2, 6), ("aabaacad", 1, 5), ("aabaacad", 2, 7)]
    ok = True
    for s, k, want in cases:
        g, f = brute(s, k), fast(s, k)
        print("  S=%-10s K=%d  want=%d brute=%d fast=%d wisp=%d" % (s, k, want, g, f, wisp(s, k)))
        if want != g or want != f:
            ok = False
            print("    MISMATCH")
    return ok


def stress(trials=3000, seed=99, nmax=11, kmax=3):
    rnd = random.Random(seed)
    badf = badw = 0
    for _ in range(trials):
        n = rnd.randint(3, nmax)
        s = rand_magical(rnd, n, rnd.choice([2, 2, 3, 4]))
        k = rnd.randint(1, kmax)
        g = brute(s, k)
        f = fast(s, k)
        w = wisp(s, k)
        if f != g:
            badf += 1
            if badf <= 5:
                print("  DP FAIL  S=%r K=%d brute=%d fast=%d" % (s, k, g, f))
        if w != g:
            badw += 1
            if badw <= 5:
                print("  wisp differs S=%r K=%d brute=%d wisp=%d" % (s, k, g, w))
    print("  %d random cases: DP mismatches=%d, debrief-wisp mismatches=%d" % (trials, badf, badw))
    return badf == 0


def stress_big(trials=250, seed=5, nmax=13):
    """Longer strings, K large enough to be unconstraining, 2-letter alphabet (densest)."""
    rnd = random.Random(seed)
    bad = 0
    for _ in range(trials):
        n = rnd.randint(8, nmax)
        s = rand_magical(rnd, n, 2)
        k = rnd.randint(1, 4)
        g, f = brute(s, k), fast(s, k)
        if f != g:
            bad += 1
            if bad <= 5:
                print("  DP FAIL  S=%r K=%d brute=%d fast=%d" % (s, k, g, f))
    print("  %d dense cases (|S| up to %d): mismatches=%d" % (trials, nmax, bad))
    return bad == 0


def timing():
    import time
    rnd = random.Random(3)
    worst = 0.0
    for _ in range(5):
        s = rand_magical_runs(rnd, 1000, 2)   # 2 letters = densest possible candidate set
        t0 = time.time()
        v = fast(s, 1000)
        worst = max(worst, time.time() - t0)
    print("  |S|=1000 K=1000 (worst shape): %.3fs per case in python, answer ~%d" % (worst, v))
    print("  DP is O(n*min(K,n/3)) = about 10^6 states of 3 flags, trivial in C++ for T=50 cases")
    return True


if __name__ == "__main__":
    print("samples:")
    a = samples()
    print("deadlock case (why the ordering constraints matter):")
    e = trap()
    print("randomized vs exhaustive simulator:")
    b = stress()
    print("dense 2-letter strings:")
    c = stress_big()
    print("limits:")
    d = timing()
    ok = a and b and c and d and e
    print("ALL OK" if ok else "FAILURES")
    sys.exit(0 if ok else 1)
