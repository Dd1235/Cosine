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

Brute force: literally iterate the recurrence for small n and sort.
"""
import random


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
def check_sample():
    assert seq(6) == [1, 2, 4, 1, 5, 10], seq(6)
    assert [mth(6, 1), mth(6, 2), mth(6, 6)] == [1, 1, 10]
    print("sample: n=6 -> 1, 1, 10  (sequence 1 2 4 1 5 10)")


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


def check_mth(N=600):
    for n in range(1, N + 1):
        s = sorted(seq(n))
        for m in range(1, n + 1):
            g = mth(n, m)
            assert g == s[m - 1], (n, m, g, s[m - 1])
    print(f"order stats: every (n, m) with n <= {N} matches brute force")


def check_random(trials=3000, seed=3):
    rng = random.Random(seed)
    for _ in range(trials):
        n = rng.randint(1, 20000)
        m = rng.randint(1, n)
        assert mth(n, m) == brute(n, m), (n, m)
    print(f"random: {trials} (n, m) pairs up to n=2e4 match brute force")


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


if __name__ == "__main__":
    check_sample()
    check_intervals()
    check_mth()
    check_random()
    check_big()
    print("OK")
