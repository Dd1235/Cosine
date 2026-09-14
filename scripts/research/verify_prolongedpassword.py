#!/usr/bin/env python3
"""Verification for kattis-prolongedpassword (2018 ICPC Asia Singapore Regional, problem H).

Claim under test
----------------
P = f^K(S) where f expands every letter c into T_c (2 <= |T_c| <= 50); queries ask for
single positions m <= LIMIT = 10^15.  The solution is:

  1. Because every |T_c| >= 2, |f^k(c)| >= 2^k.  Let D be the least d with 2^d > LIMIT
     (D = 50 for LIMIT = 10^15).  If K > D then for every character c,
     |f^K(c)| >= 2^K > LIMIT >= m, so the answer always lies inside the expansion of the
     FIRST character of S, and, level by level, inside the expansion of the FIRST character
     of T_c.  So descending K-D levels is the deterministic functional-graph walk
     g(c) = T_c[0], which is folded with rho/cycle detection: tail + cycle <= 26.
     Replace S by g^(K-D)(S[0]) and K by D.
  2. With K <= D, saturating lengths L[k][c] = min(CAP, sum of L[k-1][x] for x in T_c)
     are computed bottom-up, and each query walks down at most D levels, scanning <= 50
     children per level.

The script checks (a) both statement samples, (b) the reduction itself, by running the same
code with an artificially small LIMIT so that a full expansion of f^K(S) is still feasible
and can be compared character by character against the fast routine, over random T tables.
"""
import random
import sys

LIMIT_REAL = 10 ** 15


def depth_for(limit):
    """Least d with 2^d > limit."""
    d = 0
    while (1 << d) <= limit:
        d += 1
    return d


def first_char_walk(c, T, steps):
    """g^steps(c) where g(c) = T[c][0], via rho detection (<= 26 distinct states)."""
    seen = {}
    path = [c]
    seen[c] = 0
    cur = c
    for i in range(1, steps + 1):
        cur = T[cur][0]
        if cur in seen:
            start = seen[cur]
            cyc = i - start
            return path[start + (steps - start) % cyc]
        seen[cur] = i
        path.append(cur)
        if i == steps:
            return cur
    return cur


def solve(S, T, K, queries, limit=LIMIT_REAL):
    """Return the answer characters for the 1-indexed positions in `queries`."""
    D = depth_for(limit)
    if K > D:
        S = first_char_walk(S[0], T, K - D)
        K = D
    CAP = limit + 1
    # L[k][c] = min(CAP, |f^k(c)|)
    L = [dict((chr(97 + i), 1) for i in range(26))]
    for _ in range(K):
        prev = L[-1]
        cur = {}
        for i in range(26):
            ch = chr(97 + i)
            tot = 0
            for x in T[ch]:
                tot += prev[x]
                if tot >= CAP:
                    tot = CAP
                    break
            cur[ch] = tot
        L.append(cur)
    top = L[K]

    # one pass over S: prefix sums (saturating) so queries are answered by binary search
    pref = [0]
    run = 0
    for ch in S:
        run = min(CAP, run + top[ch])
        pref.append(run)

    import bisect

    out = []
    for m in queries:
        idx = bisect.bisect_left(pref, m) - 1   # 0-based index of S's character
        off = m - pref[idx]                      # 1-indexed offset inside f^K(S[idx])
        ch = S[idx]
        k = K
        while k > 0:
            for x in T[ch]:
                sz = L[k - 1][x]
                if off <= sz:
                    ch = x
                    break
                off -= sz
            k -= 1
        out.append(ch)
    return out


# ---------------------------------------------------------------- brute force
def expand(S, T, K):
    cur = S
    for _ in range(K):
        cur = "".join(T[c] for c in cur)
    return cur


def parse(text):
    lines = text.strip().split("\n")
    S = lines[0].strip()
    letters = lines[1].split() + lines[2].split()
    T = dict((chr(97 + i), letters[i]) for i in range(26))
    K = int(lines[3])
    M = int(lines[4])
    q = list(map(int, lines[5].split()))
    assert len(q) == M
    return S, T, K, q


SAMPLE1 = """abca
bc cd da dd ee ff gg hh ii jj kk ll mm
nn oo pp qq rr ss tt uu vv ww xx yy zz
1
2
1 8"""
SAMPLE1_OUT = ["b", "c"]

SAMPLE2 = """ab
ba ab cc dd ee ff gg hh ii jj kk ll mm
nn oo pp qq rr ss tt uu vv ww xx yy zz
2
2
1 8"""
SAMPLE2_OUT = ["a", "b"]


def check_samples():
    ok = True
    for name, text, want in (("sample 1", SAMPLE1, SAMPLE1_OUT), ("sample 2", SAMPLE2, SAMPLE2_OUT)):
        S, T, K, q = parse(text)
        got = solve(S, T, K, q)
        full = expand(S, T, K)
        print("  %s: f^K(S) = %s ; got %s ; want %s" % (name, full, got, want))
        if got != want:
            ok = False
            print("    MISMATCH")
    return ok


def random_tests(trials=400, seed=12345):
    """Compare against a literal expansion.

    The alphabet is restricted so the expansion stays small, and `limit` is made small so
    that the K > D reduction (step 1) is actually exercised: with limit = 60, D = 6, and
    K is drawn up to 40, so up to 34 levels are folded by the functional-graph walk.
    """
    rnd = random.Random(seed)
    bad = 0
    used_reduction = 0
    for t in range(trials):
        alpha = rnd.randint(2, 4)
        chars = [chr(97 + i) for i in range(alpha)]
        T = {}
        for i in range(26):
            ch = chr(97 + i)
            if i < alpha:
                ln = rnd.randint(2, 3)
                T[ch] = "".join(rnd.choice(chars) for _ in range(ln))
            else:
                T[ch] = "zz"
        S = "".join(rnd.choice(chars) for _ in range(rnd.randint(1, 5)))
        limit = rnd.choice([20, 40, 60])
        D = depth_for(limit)
        K = rnd.randint(1, 40)
        if K > D:
            used_reduction += 1
        # brute force: expand only as far as needed; length grows >= 2^k, stop once > limit
        cur = S
        for _ in range(K):
            nxt = []
            tot = 0
            for c in cur:
                nxt.append(T[c])
                tot += len(T[c])
                if tot > limit:
                    break
            cur = "".join(nxt)[: limit + 5]
        n = min(len(cur), limit)
        if n == 0:
            continue
        qs = sorted(rnd.sample(range(1, n + 1), min(n, 6)))
        want = [cur[m - 1] for m in qs]
        got = solve(S, T, K, qs, limit=limit)
        if got != want:
            bad += 1
            print("  FAIL S=%r T=%r K=%d limit=%d qs=%s got=%s want=%s"
                  % (S, {c: T[c] for c in chars}, K, limit, qs, got, want))
            if bad > 4:
                break
    print("  random: %d trials, %d exercised the K>D fold, %d mismatches" % (trials, used_reduction, bad))
    return bad == 0


def stress_limits():
    """Worst case for the stated limits: |S| = 10^6, K = 10^15, M = 1000, m_i ~ 10^15."""
    import time
    rnd = random.Random(7)
    S = "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(10 ** 6))
    T = {}
    for i in range(26):
        T[chr(97 + i)] = "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(50))
    K = 10 ** 15
    qs = sorted(rnd.randint(1, 10 ** 15) for _ in range(1000))
    t0 = time.time()
    out = solve(S, T, K, qs)
    print("  |S|=10^6 K=10^15 M=1000: %.2fs in python, %d answers, first=%s last=%s"
          % (time.time() - t0, len(out), out[0], out[-1]))
    # K small but |S| large: the one-pass/prefix-sum path.  |f^3(S)| ~ 10^6 * 50^3, so the
    # queries must be drawn inside that length to respect m_i <= |f^K(S)|.
    total = 10 ** 6 * 50 ** 3
    qs3 = sorted(rnd.randint(1, total) for _ in range(1000))
    t0 = time.time()
    out2 = solve(S, T, 3, qs3)
    print("  |S|=10^6 K=3   M=1000: %.2fs (prefix-sum pass over S), first=%s" % (time.time() - t0, out2[0]))
    return True


if __name__ == "__main__":
    print("samples:")
    a = check_samples()
    print("randomized cross-check against literal expansion:")
    b = random_tests()
    print("limits:")
    c = stress_limits()
    print("ALL OK" if (a and b and c) else "FAILURES")
    sys.exit(0 if (a and b and c) else 1)
