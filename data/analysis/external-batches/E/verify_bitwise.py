#!/usr/bin/env python3
"""Kattis 'bitwise' (2018 ICPC Asia Singapore, problem F) -- solver + brute force.

Intended solution (official judges' debrief, reconstructed)
----------------------------------------------------------
Build the answer bit by bit, high to low: keep a mask `ans`, and for each bit b
from 29 down to 0 ask feasible(ans | 1<<b) -- "can the circle be cut into K
contiguous non-empty sections whose ORs each contain every bit of that mask?".
If yes, keep the bit.  Because the bits are fixed from the top, a mask that is
feasible dominates every smaller value on the bits already decided, so the final
mask is the maximum achievable AND.

feasible(X): a section is usable as soon as its running OR contains all of X
(more elements only add bits), so from a fixed starting cut a shortest-first
sweep maximises the number of sections; if that count is >= K we can merge
adjacent sections down to exactly K, and merging only adds bits, so K sections
covering X exist.  The circle has N possible starting cuts, but only <= 31 need
trying: the section holding A_1 may have its start slid forward to the last
position p with OR(A[p..N]) unchanged (the skipped elements fall into the
previous section, which only gains bits), so a useful start is either position 1
or a position where A[p] contributes a new bit to the suffix OR A[p..N] -- and a
30-bit value can gain a bit at most 30 times.

Time O(30 * 31 * N) ~ 4.6e8 word ops at N = 5e5, space O(N).

This script checks that model three ways: against the three statement samples,
against an exhaustive brute force over all C(N,K) circular partitions, and --
separately -- that restricting to the <= 31 candidate starts never loses against
trying all N starts inside feasible().
"""
import random
import sys
import time
from itertools import combinations

BITS = 30  # A_i <= 1e9 < 2^30


# ---------------------------------------------------------------- intended solution
def candidate_starts(a):
    """0-indexed starts worth trying: 0, plus every p where A[p] adds a bit to the
    suffix OR of A[p..n-1].  At most 1 + BITS of them."""
    n = len(a)
    suf = 0
    out = {0}
    for p in range(n - 1, -1, -1):
        nxt = suf
        suf |= a[p]
        if suf != nxt:
            out.add(p)
    return sorted(out)


def feasible(a, k, x, starts):
    """Can the circle be cut into >= k contiguous sections whose ORs all cover x?"""
    n = len(a)
    for s in starts:
        cnt = 0
        cur = 0
        for i in range(n):
            cur |= a[s + i - n] if s + i >= n else a[s + i]
            if cur & x == x:
                cnt += 1
                cur = 0
                if cnt >= k:
                    return True
    return False


def solve(a, k, starts=None):
    if starts is None:
        starts = candidate_starts(a)
    ans = 0
    for b in range(BITS - 1, -1, -1):
        cand = ans | (1 << b)
        if feasible(a, k, cand, starts):
            ans = cand
    return ans


# ------------------------------------------------------------------- brute force
def brute(a, k):
    """Max over every way of cutting the circle into exactly k non-empty arcs.
    A partition is a choice of k of the n gaps as cut points; the arcs run from
    one chosen gap to the next."""
    n = len(a)
    best = -1
    for cuts in combinations(range(n), k):
        total = None
        for idx in range(k):
            i = cuts[idx]
            j = cuts[(idx + 1) % k]
            cur = 0
            p = i
            while True:
                cur |= a[p]
                p = (p + 1) % n
                if p == j:
                    break
            total = cur if total is None else total & cur
        best = max(best, total)
    return best


# ------------------------------------------------------------------------ testing
SAMPLES = [
    (([2, 3, 4, 1], 2), 3),
    (([2, 2, 2, 4, 4, 4], 3), 4),
    (([0, 1, 2, 3], 1), 3),
]


def main():
    for (args, want) in SAMPLES:
        got = solve(*args)
        print("sample", args, "want", want, "got", got)
        assert got == want, "SAMPLE FAILED"

    # (1) whole solver vs exhaustive partition search, small values so ANDs collide
    random.seed(5)
    for _ in range(4000):
        n = random.randint(1, 8)
        k = random.randint(1, n)
        a = [random.randint(0, 15) for _ in range(n)]
        g, b = solve(a, k), brute(a, k)
        if g != b:
            print("MISMATCH", a, k, "greedy", g, "brute", b)
            sys.exit(1)
    print("4000 random small cases (values < 16): bit-greedy == exhaustive partitions")

    # (2) again with sparse high-bit values, where the suffix-OR start trick matters
    random.seed(99)
    for _ in range(3000):
        n = random.randint(2, 9)
        k = random.randint(1, n)
        a = [random.choice([0, 1, 2, 4, 8, 16, 3, 5, 6, 12, 24, 31]) for _ in range(n)]
        g, b = solve(a, k), brute(a, k)
        if g != b:
            print("MISMATCH", a, k, "greedy", g, "brute", b)
            sys.exit(1)
    print("3000 random sparse-bit cases OK")

    # (3) the start reduction on its own: <= 31 candidate starts vs all n starts
    random.seed(1234)
    checked = 0
    for _ in range(4000):
        n = random.randint(1, 10)
        k = random.randint(1, n)
        a = [random.choice([0, 1, 2, 4, 8, 3, 6, 9, 15]) for _ in range(n)]
        allstarts = list(range(n))
        cands = candidate_starts(a)
        for x in range(16):
            if feasible(a, k, x, cands) != feasible(a, k, x, allstarts):
                print("START-SET MISMATCH", a, k, x, cands)
                sys.exit(1)
            checked += 1
    print("%d (input, K, X) triples: <=31 candidate starts == all N starts" % checked)

    # (4) shape and cost at the stated limit N = 5e5
    random.seed(2)
    big = [random.randint(0, 10 ** 9) for _ in range(500000)]
    cs = candidate_starts(big)
    assert len(cs) <= BITS + 1, len(cs)
    # adversarial array: a suffix that picks up one fresh bit at a time, so the
    # candidate-start set is as large as it can get
    tail = [1 << b for b in range(BITS)]
    adv = [0] * (500000 - len(tail)) + tail[::-1]
    ca = candidate_starts(adv)
    assert len(ca) <= BITS + 1, len(ca)
    t = time.time()
    feasible(big, 250000, (1 << 29) - 1, cs[:1])
    dt = time.time() - t
    print("N=5e5: %d candidate starts on random input, %d on an adversarial one "
          "(cap %d); one start-sweep %.3fs in pure Python, so the worst case "
          "30 bits * %d starts * N ~ %.1e word ops is fine in C++"
          % (len(cs), len(ca), BITS + 1, dt, BITS + 1, 30 * (BITS + 1) * 5e5))
    print("worst case (all-ones, K=N):", solve([(1 << 30) - 1] * 40, 40))

    # (5) the outer loop is NOT a binary search: feasibility is monotone under
    # submask, not under the numeric order, so no interval of X can be discarded.
    a, k = [4, 4], 2
    cs2 = candidate_starts(a)
    assert feasible(a, k, 4, cs2) and not feasible(a, k, 3, cs2)
    print("feasible(4) is True while feasible(3) is False on [4,4], K=2 -- the "
          "predicate is not monotone in the value of X, only in its bit set")


if __name__ == "__main__":
    main()
