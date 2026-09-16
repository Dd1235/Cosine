"""Bipartite Battle.

Claim proved by brute force below: for a bipartite graph with parts of size a
and b and edge set E, the Grundy value of the 'delete one vertex or one edge'
game is exactly  ((a + b) mod 2) + 2 * (|E| mod 2).

Hence Socket (the second player) wins iff the XOR over the N graphs is 0, i.e.
iff  sum_i (a_i + b_i)  is even AND an even number of graphs have an odd edge
count.  The low bit is fixed by the input; the high bit is free and uniform, so
the count of winning drawings is 0 when sum(a_i+b_i) is odd and
2^(sum a_i*b_i - 1) otherwise.
"""
import itertools
import random
import sys
from functools import lru_cache

sys.setrecursionlimit(1000000)
MOD = 10 ** 9 + 7


def grundy_table(A, B):
    """Exact Grundy of every graph on the full A x B vertex set."""
    E = A * B

    @lru_cache(maxsize=None)
    def g(am, bm, em):
        s = set()
        for k in range(E):
            if em >> k & 1:
                s.add(g(am, bm, em ^ (1 << k)))
        for i in range(A):
            if am >> i & 1:
                ne = em
                for j in range(B):
                    ne &= ~(1 << (i * B + j))
                s.add(g(am ^ (1 << i), bm, ne))
        for j in range(B):
            if bm >> j & 1:
                ne = em
                for i in range(A):
                    ne &= ~(1 << (i * B + j))
                s.add(g(am, bm ^ (1 << j), ne))
        m = 0
        while m in s:
            m += 1
        return m

    fa, fb = (1 << A) - 1, (1 << B) - 1
    out = [g(fa, fb, em) for em in range(1 << E)]
    g.cache_clear()
    return out


def check_grundy_formula():
    sizes = [(a, b) for a in range(1, 4) for b in range(1, 4)]
    sizes += [(4, 1), (4, 2), (4, 3), (1, 4), (2, 4), (5, 2)]
    for (a, b) in sizes:
        tab = grundy_table(a, b)
        for em, val in enumerate(tab):
            want = ((a + b) % 2) + 2 * (bin(em).count("1") % 2)
            assert val == want, (a, b, em, val, want)
        print("  grundy formula holds for a=%d b=%d (%d graphs)" % (a, b, len(tab)))


def formula(pairs):
    if sum(a + b for a, b in pairs) % 2:
        return 0
    return pow(2, sum(a * b for a, b in pairs) - 1, MOD)


def brute_answer(pairs):
    """Enumerate every drawing, compute the XOR of true Grundy values."""
    tables = [grundy_table(a, b) for a, b in pairs]
    total = 0
    for combo in itertools.product(*[range(len(t)) for t in tables]):
        x = 0
        for t, em in zip(tables, combo):
            x ^= t[em]
        if x == 0:
            total += 1
    return total % MOD


def main():
    print("checking Grundy = ((a+b)%2) + 2*(|E|%2):")
    check_grundy_formula()
    assert formula([(1, 1)]) == 1
    assert formula([(1, 2)]) == 0
    print("samples ok")
    random.seed(5)
    cases = [[(1, 1)], [(1, 2)], [(2, 2)], [(1, 1), (1, 1)], [(1, 2), (2, 1)],
             [(2, 2), (1, 3)], [(1, 1), (1, 2), (2, 1)], [(2, 3), (1, 1)],
             [(3, 3), (1, 2)], [(2, 2), (2, 2)], [(1, 3), (3, 1), (1, 1)]]
    for pairs in cases:
        b, f = brute_answer(pairs), formula(pairs)
        assert b == f, (pairs, b, f)
        print("  %-28s brute=%d formula=%d" % (pairs, b, f))
    print("all exhaustive multi-graph cases match")


main()
