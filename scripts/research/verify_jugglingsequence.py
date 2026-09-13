"""kattis-jugglingsequence -- 'Juggling Sequence' (ICPC Asia Can Tho 2020).

a_1 = 1;  a_{i+1} = a_i + i if a_i <= i else a_i - i.
Given n, m <= 1e18 (t <= 1e4 queries), report the m-th smallest of a_1..a_n.

Claimed structure.  The value 1 recurs at indices t = 1, 4, 13, 40, ...
(t -> 3t+1).  Starting from a_t = 1 the block is forced:
    a_t = 1, a_{t+1} = t+1, a_{t+2} = 2t+2,
    a_{t+3+2j} = t-j,  a_{t+4+2j} = 2t+3+j   (j = 0, 1, ...),
and the small branch reaches 1 again exactly at index t+3+2(t-1) = 3t+1, which
starts the next block.  So the block occupying indices t..3t holds the values
    {1} u {2..t} u {t+1} u {2t+2} u {2t+3..3t+1}  =  [1, t+1]  u  [2t+2, 3t+1],
each value exactly once -- two contiguous intervals.  There are O(log_3 n)
blocks, and the final partial block (indices t..n with n < 3t) contributes
1, optionally t+1 and 2t+2, plus the two truncated runs [t-J+1, t] and
[2t+3, 2t+2+K] with J, K the counts of small/large steps that fit before n.

So a_1..a_n is a union of ~O(log n) unit-multiplicity intervals; the m-th
smallest follows from binary searching the value X against
count(X) = sum of |interval n [1, X]|.  O(log n * log(max value)) per query.

Published solution (_tooling/solutions/jugglingsequence.cpp) uses the same
decomposition with the other natural anchor: it lists b = (3^k+1)/2 = 1, 2, 5,
14, ... (the indices where a_b = b), and a complete block b covers indices
b..3b-2 holding [1, b] u [2b, 3b-2].  Its count(x) adds min(x, b) +
|[2b, 3b-2] n [1, x]| per complete block, then handles the final partial block
b..n by splitting the remaining len = n-b+1 indices into ceil(len/2) descending
smalls [b-ceil(len/2)+1, b] and floor(len/2) ascending larges
[2b, 2b+floor(len/2)-1]; it binary searches x over [1, 3n].  Note the loop stops
at the largest b < n, so the partial block may run one index past 3b-2 -- that
index holds 3b-1, which the "larges" run produces anyway, so the formula still
matches.  n = 1 is special-cased (the b list would be empty).  O(log^2 n) per
query, O(log n) space.  This script compiles that file and compares it against
the brute force too.

Brute force: literally iterate the recurrence for small n and sort.
"""
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CPP = os.path.join(HERE, os.pardir, "_tooling", "solutions",
                   "jugglingsequence.cpp")

SHIM = """#pragma once
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <numeric>
#include <queue>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <utility>
#include <vector>
"""


def build(tmp):
    """Compile the published solution (bits/stdc++.h shimmed for libc++)."""
    cxx = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++")
    if cxx is None or not os.path.exists(CPP):
        return None
    os.makedirs(os.path.join(tmp, "bits"), exist_ok=True)
    with open(os.path.join(tmp, "bits", "stdc++.h"), "w") as f:
        f.write(SHIM)
    exe = os.path.join(tmp, "js")
    r = subprocess.run([cxx, "-O2", "-std=c++17", "-I", tmp, "-o", exe, CPP],
                       capture_output=True, text=True)
    if r.returncode:
        print("compile failed:\n" + r.stderr[:2000], file=sys.stderr)
        return None
    return exe


def run_cpp(exe, queries):
    inp = "%d\n" % len(queries)
    inp += "".join("%d %d\n" % q for q in queries)
    r = subprocess.run([exe], input=inp, capture_output=True, text=True,
                       timeout=300)
    assert r.returncode == 0, r.stderr
    out = [int(x) for x in r.stdout.split()]
    assert len(out) == len(queries), (len(out), len(queries))
    return out


# ---------------------------------------------------------------- solution
def intervals(n):
    """The multiset a_1..a_n as a list of inclusive intervals (multiplicities
    add where intervals from different blocks overlap)."""
    out = []
    t = 1
    while 3 * t <= n:                       # complete block, indices t..3t
        out.append((1, t + 1))
        out.append((2 * t + 2, 3 * t + 1))
        t = 3 * t + 1
    if t <= n:                              # partial block, indices t..n
        out.append((1, 1))                  # index t
        if n >= t + 1:
            out.append((t + 1, t + 1))      # index t+1
        if n >= t + 2:
            out.append((2 * t + 2, 2 * t + 2))
        if n >= t + 3:                      # smalls t, t-1, ... at t+3+2j
            J = (n - t - 3) // 2 + 1
            out.append((t - J + 1, t))
        if n >= t + 4:                      # larges 2t+3, ... at t+4+2j
            K = (n - t - 4) // 2 + 1
            out.append((2 * t + 3, 2 * t + 2 + K))
    return out


def count_le(iv, x):
    return sum(min(hi, x) - lo + 1 for lo, hi in iv if lo <= x)


def mth(n, m):
    iv = intervals(n)
    lo, hi = 1, max(h for _, h in iv)
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(iv, mid) >= m:
            hi = mid
        else:
            lo = mid + 1
    return lo


# ---------------------------------------------------------------- brute force
def seq(n):
    a = [0, 1]
    for i in range(1, n):
        a.append(a[i] + i if a[i] <= i else a[i] - i)
    return a[1:n + 1]


def brute(n, m):
    return sorted(seq(n))[m - 1]


# ---------------------------------------------------------------- checks
def check_sample(exe):
    assert seq(6) == [1, 2, 4, 1, 5, 10], seq(6)
    assert [mth(6, 1), mth(6, 2), mth(6, 6)] == [1, 1, 10]
    if exe:
        got = run_cpp(exe, [(6, 1), (6, 2), (6, 6)])
        assert got == [1, 1, 10], got
    print("sample: n=6 -> 1, 1, 10  (sequence 1 2 4 1 5 10); published C++ agrees")


def check_intervals(N=4000):
    """The interval decomposition must reproduce the exact multiset, not just
    order statistics."""
    for n in range(1, N + 1):
        exp = sorted(seq(n))
        got = []
        for lo, hi in intervals(n):
            got.extend(range(lo, hi + 1))
        assert sorted(got) == exp, (n, sorted(got), exp)
    print(f"multiset: interval decomposition == real sequence for every n <= {N}")


def check_mth(exe, N=600):
    queries, want = [], []
    for n in range(1, N + 1):
        s = sorted(seq(n))
        for m in range(1, n + 1):
            g = mth(n, m)
            assert g == s[m - 1], (n, m, g, s[m - 1])
            queries.append((n, m))
            want.append(s[m - 1])
    print(f"order stats: every (n, m) with n <= {N} matches brute force "
          f"({len(queries)} pairs)")
    if exe:
        for lo in range(0, len(queries), 10000):
            chunk = queries[lo:lo + 10000]
            got = run_cpp(exe, chunk)
            for q, g, w in zip(chunk, got, want[lo:lo + 10000]):
                assert g == w, ("cpp mismatch", q, g, w)
        print(f"        published C++ agrees on all {len(queries)} of them")


def check_random(exe, trials=3000, seed=3):
    rng = random.Random(seed)
    qs = []
    for _ in range(trials):
        n = rng.randint(1, 20000)
        m = rng.randint(1, n)
        assert mth(n, m) == brute(n, m), (n, m)
        qs.append((n, m))
    print(f"random: {trials} (n, m) pairs up to n=2e4 match brute force")
    if exe:
        got = run_cpp(exe, qs)
        for q, g in zip(qs, got):
            assert g == brute(*q), ("cpp mismatch", q, g, brute(*q))
        print(f"        published C++ agrees on all {trials}")


def check_big():
    """Limits: n = 1e18, and the value fits in 64-bit (max block top ~3e18)."""
    n = 10 ** 18
    iv = intervals(n)
    assert count_le(iv, max(h for _, h in iv)) == n, "counts must total n"
    for nn in (10 ** 18, 10 ** 18 - 1, 3 ** 38, (3 ** 38 - 1) // 2):
        ivv = intervals(nn)
        assert count_le(ivv, max(h for _, h in ivv)) == nn, nn
        assert len(ivv) <= 100
    print("limits: n=1e18 -> %d intervals, totals check, max value %d < 2^63"
          % (len(iv), max(h for _, h in iv)))
    print("       n=1e18: m=1 ->", mth(n, 1), " m=n ->", mth(n, n),
          " m=n//2 ->", mth(n, n // 2))


def check_big_cpp(exe, seed=17):
    """Huge n against the (brute-verified) interval model, plus the real worst
    case for the time limit: t = 1e4 queries at n = 1e18."""
    if not exe:
        return
    import time
    rng = random.Random(seed)
    qs = []
    for n in (1, 2, 3, 4, 5, 13, 14, 15, 40, 41, 42, 10 ** 18, 10 ** 18 - 1,
              3 ** 38, (3 ** 38 + 1) // 2, (3 ** 38 + 1) // 2 - 1,
              (3 ** 38 + 1) // 2 + 1):
        for m in {1, 2, n, max(1, n // 2), max(1, n // 3), max(1, n - 1)}:
            if m <= n:                      # the statement guarantees m <= n
                qs.append((n, m))
    for _ in range(2000):
        n = rng.randint(1, 10 ** 18)
        qs.append((n, rng.randint(1, n)))
    got = run_cpp(exe, qs)
    for q, g in zip(qs, got):
        assert g == mth(*q), ("cpp vs model mismatch", q, g, mth(*q))
    print("big: published C++ == interval model on %d queries incl. n=1e18 "
          "and the block boundaries 3^k, (3^k+1)/2" % len(qs))
    worst = [(10 ** 18, rng.randint(1, 10 ** 18)) for _ in range(10000)]
    t0 = time.time()
    run_cpp(exe, worst)
    print("limits: t=1e4 queries at n=1e18 in %.2fs" % (time.time() - t0))


if __name__ == "__main__":
    tmp = tempfile.mkdtemp()
    exe = build(tmp)
    if exe is None:
        print("WARNING: no C++ compiler; only the Python model is checked")
    check_sample(exe)
    check_intervals()
    check_mth(exe)
    check_random(exe)
    check_big()
    check_big_cpp(exe)
    print("OK")
