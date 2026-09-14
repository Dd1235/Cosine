"""
Kattis / ICPC WF 2023 "Schedule"  -- verification of the derived solution.

MODEL
-----
A schedule is a w x n matrix over {1,2}; entry (t,i) = which member of team i
is in the office in week t.  Column i is a binary vector c_i of length w.
Two people (i,a),(j,b), i != j, meet in week t iff c_i[t]=a and c_j[t]=b.
With virtual occurrences at week 0 and week w+1, "max gap <= k" is exactly
"every k consecutive weeks inside [1,w] contain an occurrence".

So isolation <= k  <=>  for every pair of columns (i,j) and every window of k
consecutive weeks, all four patterns (1,1),(1,2),(2,1),(2,2) appear in that
window  (and, when k >= w, simply: all four appear somewhere in [1,w]).

A set of binary columns in which every pair realises all 4 patterns is exactly
a binary COVERING ARRAY of strength 2 (pairwise "qualitatively independent"
vectors).  So:
   * window [1,k] must be a CA with k rows and n columns  =>  k >= CAN(n)
   * a schedule of period k whose k distinct rows form such a CA makes EVERY
     window of length k contain each of the k rows exactly once  =>  k works.
Hence  answer = min{ k : 4 <= k <= w and a CA(k;2,n,2) exists }, else infinity.

MAX COLUMNS FOR k ROWS (Milner's theorem)
-----------------------------------------
Normalise every column so row 1 is '1' (complementing a column just swaps the
two members of that team, which the problem's max over a,b is invariant to).
Then pattern (1,1) is realised in row 1, and with S_i = { rows >= 2 where the
column is '2' } the remaining three patterns say exactly:
    S_i ^ S_j != {},  S_i \ S_j != {},  S_j \ S_i != {}
i.e. the S_i form an INTERSECTING ANTICHAIN on the ground set {2..k} of size
M = k-1.  Milner's theorem: such a family has size at most C(M, ceil((M+1)/2)),
attained by taking ALL subsets of that single size s = ceil(k/2) (2s > M forces
pairwise intersection; equal sizes force the antichain).
    maxn(k) = C(k-1, ceil(k/2))
    k:      4  5  6   7   8   9  10   11   12   13    14    15    16     17
    maxn:   3  4 10  15  35  56 126  210  462  792  1716  3003  6435  11440
n <= 10^4 so k <= 17 always suffices; w <= 52 so the cap is w.

NOTE the odd-k subtlety: the frequently quoted C(k-1, ceil(k/2)-1) is only
correct for even k; for odd k it OVERCOUNTS (k=5 would give 6, truth is 4).
The brute force below checks this.
"""

import sys, itertools
from math import comb
from functools import lru_cache

# ---------------------------------------------------------------- solution --

def maxn(k):
    """max #teams schedulable with isolation k (Milner)."""
    if k < 4:
        return 0
    return comb(k - 1, (k + 1) // 2)

def answer(n, w):
    for k in range(4, w + 1):
        if maxn(k) >= n:
            return k
    return None            # infinity

def build(n, w):
    """schedule achieving answer(n,w); list of w strings over {'1','2'}."""
    k = answer(n, w)
    if k is None:
        return None
    s = (k + 1) // 2                       # ceil(k/2)
    cols = []                              # column i = subset of {1..k-1}
    for S in itertools.combinations(range(1, k), s):
        cols.append(set(S))
        if len(cols) == n:
            break
    assert len(cols) == n
    rows = []
    for r in range(k):                     # r = 0 is the normalised row
        rows.append(''.join('2' if r in c else '1' for c in cols))
    return [rows[t % k] for t in range(w)]

# ----------------------------------------------------------------- checker --

def isolation(sched):
    """exact isolation of a schedule (list of w strings); None = infinity."""
    w = len(sched); n = len(sched[0])
    worst = 0
    for i in range(n):
        for j in range(i + 1, n):
            for a in '12':
                for b in '12':
                    prev = 0; mx = 0
                    for t in range(1, w + 1):
                        if sched[t-1][i] == a and sched[t-1][j] == b:
                            mx = max(mx, t - prev); prev = t
                    if prev == 0:
                        return None
                    mx = max(mx, w + 1 - prev)
                    worst = max(worst, mx)
    return worst

# ------------------------------------------- brute force #1: maxn via clique --

def maxn_brute(k):
    """largest set of pairwise qualitatively independent length-k binary vecs."""
    # normalise first bit to 0 -> vertices are the 2^(k-1) tails
    verts = list(range(1 << (k - 1)))
    def qi(u, v):
        # full vectors: 0<<(k-1)|u  and 0<<(k-1)|v ; bit r of tail = row r+1
        both = u & v                 # rows where both are 1
        uo   = u & ~v & ((1 << (k-1)) - 1)
        vo   = v & ~u & ((1 << (k-1)) - 1)
        return both and uo and vo    # pattern (0,0) supplied by row 0
    adj = [0] * len(verts)
    for x in verts:
        m = 0
        for y in verts:
            if x != y and qi(x, y):
                m |= 1 << y
        adj[x] = m
    best = 0
    def expand(cand, size):
        nonlocal best
        while cand:
            if size + bin(cand).count('1') <= best:
                return
            v = (cand & -cand).bit_length() - 1
            cand &= ~(1 << v)
            expand(cand & adj[v], size + 1)
            best = max(best, size + 1)
    expand((1 << len(verts)) - 1, 0)
    return best

# ------------------------------- brute force #2: exhaustive over schedules ---

def brute_answer(n, w):
    """true min isolation by enumerating every schedule (row 1 fixed all-'1')."""
    best = None
    rows_all = [format(m, '0%db' % n).replace('0', '1').replace('1', '2')
                for m in range(1 << n)]
    # build rows properly: bit set -> '2'
    rows_all = []
    for m in range(1 << n):
        rows_all.append(''.join('2' if (m >> i) & 1 else '1' for i in range(n)))
    first = rows_all[0]                      # all '1'  (WLOG by complementing)
    for rest in itertools.product(rows_all, repeat=w - 1):
        s = [first] + list(rest)
        v = isolation(s)
        if v is not None and (best is None or v < best):
            best = v
    return best

# ----------------------------------------------------------------- driver ---

def main():
    ok = True

    print("== samples ==")
    for (n, w, exp) in [(2, 6, 4), (2, 1, None)]:
        a = answer(n, w)
        print(f"  n={n} w={w}: got {a if a else 'infinity'} expected "
              f"{exp if exp else 'infinity'}", "OK" if a == exp else "FAIL")
        ok &= (a == exp)
        if a is not None:
            s = build(n, w)
            iso = isolation(s)
            print("    built schedule:", s, "isolation", iso)
            ok &= (iso == a)

    print("== maxn(k) formula vs exhaustive clique ==")
    for k in range(4, 8):
        b = maxn_brute(k)
        f = maxn(k)
        bad_formula = comb(k - 1, (k + 1) // 2 - 1)   # the commonly quoted one
        print(f"  k={k}: brute={b} milner={f} (quoted-alt={bad_formula})",
              "OK" if b == f else "FAIL")
        ok &= (b == f)

    print("== exhaustive schedule search vs formula ==")
    for n in range(2, 5):
        for w in range(1, 7):
            if n == 4 and w == 6:
                continue                     # 2^20 schedules, done separately
            b = brute_answer(n, w)
            f = answer(n, w)
            print(f"  n={n} w={w}: brute={b} formula={f}",
                  "OK" if b == f else "FAIL")
            ok &= (b == f)

    print("== constructed schedule really achieves the formula value ==")
    for n in range(2, 26):
        for w in range(1, 53):
            f = answer(n, w)
            s = build(n, w)
            if f is None:
                if s is not None:
                    print(f"  n={n} w={w} FAIL: built a schedule but said infinity")
                    ok = False
                continue
            iso = isolation(s)
            if iso != f:
                print(f"  n={n} w={w} FAIL: built isolation {iso} != {f}")
                ok = False
    print("  done (n=2..25, w=1..52)")

    print("== spot values ==")
    for k in range(4, 18):
        print(f"  maxn({k}) = {maxn(k)}")
    print("  n=10^4 needs k =", answer(10**4, 52))

    print("ALL OK" if ok else "FAILURES PRESENT")

main()

# ============================================================ extra checks ==
# (added on a second pass: the case the driver above skips, an independent
#  re-derivation of "isolation <= k <=> every k-window holds all 4 patterns",
#  and a sampled check of the real 10^4-team output.)

import random

def isolation_by_windows(sched):
    """Isolation computed from the window characterisation instead of gaps."""
    w = len(sched); n = len(sched[0])
    def ok(k):                       # every k consecutive weeks hold all 4
        for i in range(n):
            for j in range(i + 1, n):
                for start in range(0, w - k + 1):
                    seen = set()
                    for t in range(start, start + k):
                        seen.add((sched[t][i], sched[t][j]))
                    if len(seen) < 4:
                        return False
        return True
    # infinity <=> some pair misses a pattern over all of [1,w]
    for i in range(n):
        for j in range(i + 1, n):
            seen = set((r[i], r[j]) for r in sched)
            if len(seen) < 4:
                return None
    for k in range(1, w + 1):
        if ok(k):
            return k
    return None

def extra():
    ok = True

    print("== the case the driver skips: n=4, w=6 (2^20 schedules) ==")
    b, f = brute_answer(4, 6), answer(4, 6)
    print(f"  n=4 w=6: brute={b} formula={f}", "OK" if b == f else "FAIL")
    ok &= (b == f)

    print("== gap-definition vs window-characterisation, random schedules ==")
    random.seed(20230404)
    bad = 0
    for _ in range(4000):
        n = random.randint(2, 4); w = random.randint(1, 9)
        s = [''.join(random.choice('12') for _ in range(n)) for _ in range(w)]
        if isolation(s) != isolation_by_windows(s):
            bad += 1
            if bad == 1:
                print("  FAIL on", s, isolation(s), isolation_by_windows(s))
    print(f"  mismatches: {bad}", "OK" if bad == 0 else "FAIL")
    ok &= (bad == 0)

    print("== periodicity claim: every window of a period-k schedule is the CA ==")
    for n in range(2, 40):
        for w in range(4, 53):
            k = answer(n, w)
            if k is None:
                continue
            s = build(n, w)
            if any(s[t] != s[t % k] for t in range(w)):
                print(f"  n={n} w={w} FAIL: not periodic"); ok = False
    print("  done")

    print("== worst case n=10^4: build and check a random sample of pairs ==")
    n, w = 10**4, 52
    k = answer(n, w)
    s = build(n, w)
    print(f"  answer={k}, rows={len(s)}, cols={len(s[0])}, period ok:",
          all(s[t] == s[t % k] for t in range(w)))
    random.seed(1)
    worst = 0
    for _ in range(20000):
        i = random.randrange(n); j = random.randrange(n)
        if i == j:
            continue
        for a in '12':
            for b in '12':
                prev = 0; mx = 0
                for t in range(1, w + 1):
                    if s[t-1][i] == a and s[t-1][j] == b:
                        mx = max(mx, t - prev); prev = t
                if prev == 0:
                    print(f"  FAIL: cols {i},{j} never realise {a}{b}"); ok = False
                else:
                    worst = max(worst, max(mx, w + 1 - prev))
    print(f"  sampled isolation = {worst}", "OK" if worst == k else "FAIL")
    ok &= (worst == k)

    print("== columns are distinct & the whole family is an intersecting antichain ==")
    for n, w in [(3, 4), (10, 6), (35, 8), (126, 10), (1000, 14)]:
        k = answer(n, w); s = build(n, w)
        cols = [''.join(r[i] for r in s[:k]) for i in range(n)]
        assert len(set(cols)) == n, (n, w)
        for i in range(n):
            for j in range(i + 1, min(n, i + 30)):
                pats = set(zip(cols[i], cols[j]))
                if len(pats) != 4:
                    print(f"  n={n} FAIL cols {i},{j} -> {pats}"); ok = False
        print(f"  n={n} w={w} k={k}: {len(set(cols))} distinct columns, pairs OK")

    print("EXTRA ALL OK" if ok else "EXTRA FAILURES PRESENT")

extra()
