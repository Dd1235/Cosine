"""Alchemy 101 (kattis-alchemy101) -- brute force vs closed form.

Task: pick the largest subset S of {1..m} with xor(S) == m; among the largest,
print the lexicographically smallest list.

Closed form used by the solution:
  X(m) = xor of 1..m = [m, 1, m+1, 0][m % 4]
  v = X(m) ^ m.  If v == 0 the whole set {1..m} already xors to m (size m).
  Otherwise drop the single element v (which is always in [1, m]); size m-1.
  The surviving set is unique for its size, so sorting it ascending is the
  lexicographically smallest list and the tie-break in the statement is vacuous.

Brute force enumerates every subset for small m, takes the maximum size, then the
lexicographically smallest sorted list at that size.
"""
from itertools import combinations


def xor_1_to(m):
    return [m, 1, m + 1, 0][m % 4]


def solve(m):
    v = xor_1_to(m) ^ m
    if v == 0:
        return list(range(1, m + 1))
    assert 1 <= v <= m, (m, v)
    return [x for x in range(1, m + 1) if x != v]


def brute(m):
    best = None
    for mask in range(1 << m):
        acc = 0
        sub = []
        for i in range(m):
            if mask >> i & 1:
                acc ^= i + 1
                sub.append(i + 1)
        if acc == m:
            key = (-len(sub), sub)          # sub is already ascending
            if best is None or key < best[0]:
                best = (key, sub)
    return best[1] if best else None


def brute_count_max(m):
    """How many distinct maximum-size subsets are there? (checks the tie-break)"""
    best = -1
    cnt = 0
    for mask in range(1 << m):
        acc = 0
        sz = 0
        for i in range(m):
            if mask >> i & 1:
                acc ^= i + 1
                sz += 1
        if acc == m:
            if sz > best:
                best, cnt = sz, 1
            elif sz == best:
                cnt += 1
    return best, cnt


def main():
    # samples
    assert solve(1) == [1], solve(1)
    assert solve(4) == [1, 2, 3, 4], solve(4)
    assert solve(5) == [1, 2, 3, 5], solve(5)
    print("samples OK")

    bad = 0
    for m in range(1, 17):
        b = brute(m)
        s = solve(m)
        if b != s:
            bad += 1
            print("MISMATCH m=%d brute=%s solve=%s" % (m, b, s))
        sz, cnt = brute_count_max(m)
        if cnt != 1:
            print("NOTE m=%d has %d maximum-size subsets (size %d)" % (m, cnt, sz))
    print("exhaustive m<=16 mismatches:", bad)

    # structural checks over the full input range
    from functools import reduce
    for m in range(1, 1001):
        s = solve(m)
        x = reduce(lambda a, b: a ^ b, s)
        assert x == m, (m, x)
        assert len(set(s)) == len(s) and all(1 <= e <= m for e in s)
        v = xor_1_to(m) ^ m
        assert len(s) == (m if v == 0 else m - 1)
        # upper bound: size m is only achievable when the full set already xors to m
        if v != 0:
            assert xor_1_to(m) != m
        assert s == sorted(s)
    print("m<=1000 structural checks OK")
    print("sizes by residue:", [(m, len(solve(m))) for m in range(1, 13)])


main()
