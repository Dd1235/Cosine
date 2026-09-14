"""
Kattis / ICPC World Finals 2023 "A Recurring Problem" (arecurringproblem)
========================================================================
Verification of the derived solution.

MODEL
-----
A PLRR is (k; c_1..c_k; a_1..a_k), all positive integers, extended by
    a_{i+k} = c_1 a_i + c_2 a_{i+1} + ... + c_k a_{i+k-1}      (i >= 1).
Its "generated part" is the infinite tail  g = (a_{k+1}, a_{k+2}, ...).
All PLRRs are ordered by g lexicographically, ties broken by (c_1..c_k)
lexicographically (shorter-is-smaller on a common prefix, as the statement's
own example k=1,c=(2) before k=2,c=(2,1) shows).  Index n <= 1e9, 1-based.

The order is total: given c and enough of g the initial values are forced
(constraint i=k reads c_1 a_k + sum_{j>=2} c_j a_{k+j-1} = a_{2k}, so a_k, then
a_{k-1}, ... are recovered), so equal g and equal c imply equal a.

FIRST GENERATED VALUE
---------------------
a_{k+1} = sum_j c_j a_j, so the PLRRs whose generated part starts with t are
exactly the ways of writing t = sum_{j=1..k} c_j a_j with k >= 1 and all
factors positive.  Hence, with d() the divisor function and D(x) = sum d(m)x^m,
    g(t) = [x^t] D/(1-D)  =  sum_{c*a <= t} g(t - c*a),   g(0) = 1.
1, 3, 7, 18, 43, 108, 263, 651, 1599, ...  growing like 2.46^t: the cumulative
sums pass 1e9 at t = 24, so the answer's first generated value is <= 24, every
order k is <= 24 and sum_j c_j <= 24, sum_j a_j <= 24.

COUNTING A PREFIX  (the crux; this is the judges' intended recursion)
--------------------------------------------------------------------
Re-index a PLRR so that the generated part is a_1, a_2, ... and the initial
values are a_0, a_{-1}, ..., a_{-(r-1)} (r = the order).  Then a prefix
x = (x_1..x_L) of the generated part means
    x_i = sum_{j=1..r} c_j * a_{-r+i+j-1}     for i = 1..L.
Define f(x, prev), where prev = (a_1, ..., a_L) is the window of values that sit
immediately to the left of the still-unknown part (at the root prev = x):
peel off the LAST coefficient c_r together with the newest unknown initial
value a_0.  Its contribution to equation i is c_r * a_{i-1}, i.e.
c_r * (a_0, prev_1, ..., prev_{L-1}).  So

    f(x, prev) = 1                                   if x == 0 (a finished PLRR)
               = 0                                   if x has a negative entry
               = sum over a_0 >= 1, c >= 1 with c*a_0 <= x_1 of
                    f(x - c*(a_0, prev_1..prev_{L-1}), (a_0, prev_1..prev_{L-1}))

and f(x, x) is the number of PLRRs whose generated part starts with x.  x_1
drops by c*a_0 >= 1 each level, so the recursion depth is at most x_1 <= 24.

Two refinements make it fast:
 (1) f returns a MAP  next generated value -> count  instead of a bare count.
     The next value is x_{L+1} = sum_j c_j a_{L+j-r}; the coefficient peeled at
     a level contributes c * prev_L (the entry that "falls off" when a_0 is
     prepended), so a child's value v is lifted to v + c*prev_L and the base
     case returns {0: 1}.  The trie descent then needs no binary search.
 (2) Projection pruning.  Dropping the last coordinate of x and of prev maps a
     length-L state onto a length-(L-1) state, and the transitions commute with
     that projection.  Moreover the amount subtracted from x_L along a path is
     exactly the next-value accumulated by the projected path, so
         count_L(x, prev) = map_{L-1}(x[:-1], prev[:-1])[x_L],
     an equality, not just a bound.  Hence a state whose projection's map does
     not contain x_L is dead and is cut immediately.  Memoise on (x, prev).

DRIVER
------
Subtract g(1), g(2), ... from n to fix the first generated value; then repeatedly
take the map of the current prefix, walk its keys in increasing order subtracting
counts, and append the key whose bucket contains the remaining rank.  Stop when
that bucket holds at most a handful of PLRRs, re-run the recursion in
"record the path" mode to materialise their (c, a) (c_r and a_r are chosen
first, so both vectors are built backwards), and sort those few by generated
tail then coefficient vector.

FINITE COMPARISON IS EXACT: if two generated sequences of orders k and k' agree
on their first k + k' terms they agree forever - their difference is killed by
the product of the two characteristic polynomials, a monic recurrence of order
k + k' with k + k' leading zeros.  k, k' <= t, so 2t+4 terms decide every
comparison, including the genuine ties (e.g. k=1,c=(2),a=(2) and
k=2,c=(2,1),a=(1,2) generate the same 4,8,16,... and are separated only by c).

COMPLEXITY: no closed form is known (the judges' sketch gives none either).
Empirically the memo holds ~5*10^5 states at n = 10^9 and this pure-Python
implementation answers the worst n seen in ~2 s; the problem author's C++ takes
0.29 s against a 20 s limit.

WHAT THIS SCRIPT CHECKS
-----------------------
 1. both official samples (n = 3 and n = 1235);
 2. the fast solver against an exhaustive brute force for EVERY n from 1 to
    2693 (first generated value <= 9); with --full, every n up to 16333 (<= 11);
 3. the prefix-counting maps themselves against brute-force distributions for
    all prefixes of length 1..3 with first value <= 10 (counts AND next-value
    buckets), i.e. the counting is validated independently of the descent;
 4. g(t) against an independent generating-function computation and against the
    size of the brute-force enumeration;
 5. that every answer produced is a genuine PLRR (positive integers) whose
    generated part really starts with the descended prefix;
 6. timing on n = 10^9 and on random 9-digit n.

Run:  python3 verify_arecurringproblem.py [--full]
"""
import sys, time, random
from collections import defaultdict

sys.setrecursionlimit(100000)

# ----------------------------------------------------------------- brute force
def all_plrr(v):
    """every (k, c, a) with sum c_j a_j = v, i.e. every PLRR whose generated
    part starts with v."""
    divpairs = [[(c, t // c) for c in range(1, t + 1) if t % c == 0]
                for t in range(v + 1)]
    res, cs, as_ = [], [], []
    def rec(rem):
        if rem == 0:
            res.append((len(cs), tuple(cs), tuple(as_))); return
        for t in range(1, rem + 1):
            for (c, a) in divpairs[t]:
                cs.append(c); as_.append(a); rec(rem - t); cs.pop(); as_.pop()
    rec(v)
    return res

def gseq(c, a, m):
    k = len(c); s = list(a)
    for i in range(m):
        s.append(sum(c[j] * s[i + j] for j in range(k)))
    return tuple(s[k:k + m])

def brute_sorted(v):
    L = 2 * v + 4                       # exact, see docstring
    rows = [(gseq(c, a, L), c, a) for (k, c, a) in all_plrr(v)]
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows

def g_table(N):
    """g(t) by the divisor generating function D/(1-D)."""
    d = [0] * (N + 1)
    for i in range(1, N + 1):
        for j in range(i, N + 1, i): d[j] += 1
    g = [0] * (N + 1)
    for t in range(1, N + 1):
        g[t] = d[t] + sum(d[u] * g[t - u] for u in range(1, t))
    return g

# ----------------------------------------------------------------- fast solver
memo = defaultdict(dict)      # memo[L][(x, prev)] -> {next value: count}

def F(L, x, prev):
    key = (x, prev)
    m = memo[L]
    if key in m: return m[key]
    if all(t == 0 for t in x):
        m[key] = {0: 1}; return m[key]
    if any(t < 0 for t in x) or x[0] == 0:
        m[key] = {}; return m[key]
    if L >= 2:                                        # projection pruning
        if x[-1] not in F(L - 1, x[:-1], prev[:-1]):
            m[key] = {}; return m[key]
    res = defaultdict(int)
    x1, tail, back = x[0], prev[:-1], prev[-1]
    for a0 in range(1, x1 + 1):
        for c in range(1, x1 // a0 + 1):
            nprev = (a0,) + tail
            nx = tuple(t - c * p for t, p in zip(x, nprev))
            if nx[0] < 0: continue
            ch = F(L, nx, nprev)
            if not ch: continue
            add = c * back
            for val, cnt in ch.items(): res[val + add] += cnt
    r = dict(res); m[key] = r; return r

def paths(L, x, prev, cs, as_, out):
    if all(t == 0 for t in x):
        out.append((tuple(reversed(cs)), tuple(reversed(as_)))); return
    if any(t < 0 for t in x) or x[0] == 0: return
    if not F(L, x, prev): return
    x1, tail = x[0], prev[:-1]
    for a0 in range(1, x1 + 1):
        for c in range(1, x1 // a0 + 1):
            nprev = (a0,) + tail
            nx = tuple(t - c * p for t, p in zip(x, nprev))
            if nx[0] < 0: continue
            cs.append(c); as_.append(a0)
            paths(L, nx, nprev, cs, as_, out)
            cs.pop(); as_.pop()

def solve(n, thresh=20, maxlen=40, trace=False):
    rem, t = n, 0
    while True:
        t += 1
        cnt = sum(F(1, (t,), (t,)).values())
        if rem <= cnt: break
        rem -= cnt
    pref = [t]
    while True:
        mp = F(len(pref), tuple(pref), tuple(pref))
        tot = sum(mp.values())
        if trace: print("   prefix %-38s count %-12d rank %d" % (pref, tot, rem))
        if tot <= thresh or len(pref) >= maxlen: break
        for val in sorted(mp):
            if rem <= mp[val]: pref.append(val); break
            rem -= mp[val]
        else: raise AssertionError("rank overflow")
    out = []
    paths(len(pref), tuple(pref), tuple(pref), [], [], out)
    assert len(out) == sum(F(len(pref), tuple(pref), tuple(pref)).values())
    out.sort(key=lambda ca: (gseq(ca[0], ca[1], 2 * t + 4), ca[0]))
    c, a = out[rem - 1]
    # self-check: a genuine PLRR whose generated part starts with the prefix
    assert len(c) == len(a) and all(y > 0 for y in c) and all(y > 0 for y in a)
    assert gseq(c, a, len(pref)) == tuple(pref)
    return len(c), c, a, gseq(c, a, 10)

def fmt(n):
    k, c, a, g = solve(n)
    return "%d\n%s\n%s\n%s" % (k, " ".join(map(str, c)),
                               " ".join(map(str, a)), " ".join(map(str, g)))

# ---------------------------------------------------------------------- checks
def main():
    full = "--full" in sys.argv
    ok = True

    print("[1] official samples")
    exp3 = "2\n1 1\n1 1\n2 3 5 8 13 21 34 55 89 144"
    exp1235 = ("4\n1 1 3 1\n3 2 1 1\n"
               "9 15 44 99 255 611 1519 3706 9129 22377")
    for n, exp in ((3, exp3), (1235, exp1235)):
        got = fmt(n)
        print("    n=%-5d %s" % (n, "OK" if got == exp else "FAIL\n" + got))
        ok &= got == exp

    print("[2] g(t) vs generating function vs exhaustive enumeration")
    g = g_table(30)
    print("    g(1..12) =", g[1:13])
    for t in range(1, 13):
        assert sum(F(1, (t,), (t,)).values()) == g[t], t
    for t in range(1, 11):
        assert len(all_plrr(t)) == g[t], t
    cum = 0
    for t in range(1, 31):
        cum += g[t]
        if cum >= 10 ** 9:
            print("    cumulative passes 1e9 at t =", t, "(cum=%d)" % cum); break

    print("[3] prefix-count maps vs brute force (first value <= 10, depth <= 3)")
    for v in range(1, 11):
        rows = brute_sorted(v)
        for depth in (1, 2, 3):
            buckets = defaultdict(lambda: defaultdict(int))
            for s, c, a in rows:
                buckets[s[:depth]][s[depth]] += 1
            for pref, dist in buckets.items():
                mp = F(depth, pref, pref)
                assert mp == dict(dist), (v, pref, mp, dict(dist))
    print("    OK: all depth-1..3 prefix maps (counts and next-value buckets) match")

    print("[4] full enumeration vs solver, every n in order")
    vmax = 11 if full else 9
    rows = []
    for v in range(1, vmax + 1):
        rows.extend([(c, a) for _, c, a in brute_sorted(v)])
    bad = 0
    for n in range(1, len(rows) + 1):
        k, c, a, _ = solve(n)
        if (c, a) != rows[n - 1]:
            bad += 1
            print("    MISMATCH n=%d got %s %s want %s" % (n, c, a, rows[n - 1]))
            if bad > 5: break
    print("    checked n = 1 ..", len(rows), "mismatches:", bad)
    ok &= bad == 0

    print("[5] timing")
    for l in list(memo): memo[l].clear()
    st = time.time(); print("    n=1000000000 ->", fmt(10 ** 9).replace("\n", " | "))
    print("    %.2fs, memo states %s" % (time.time() - st,
                                         sum(len(memo[l]) for l in memo)))
    worst = 0.0
    random.seed(1)
    for _ in range(10):
        n = random.randint(1, 10 ** 9)
        for l in list(memo): memo[l].clear()
        st = time.time(); solve(n); worst = max(worst, time.time() - st)
    print("    worst of 10 random 9-digit n: %.2fs (pure Python)" % worst)

    print("\nRESULT:", "ALL CHECKS PASSED" if ok else "FAILURES")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        print(fmt(int(sys.argv[1])))
    else:
        main()
