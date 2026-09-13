"""verify kattis-nonprimefactors (2018 ICPC Asia Singapore Regional, problem L).

Claim under test: NPF(i) = d(i) - omega(i), where d(i) is the number of
positive divisors of i and omega(i) the number of DISTINCT prime divisors,
and both tables are buildable for all i <= 2e6 by one divisor-counting sieve
so each of the up to 3e6 queries is answered by an array lookup.

Checks:
  1. the statement's sample (4 queries -> 7, 1, 4, 2);
  2. the sieve tables against a trial-division brute force for every i in
     [2, 200000];
  3. the sieve d/omega against the multiplicative formula prod(q_k+1) / m
     from the judges' slide 19, for every i in [2, 200000];
  4. timing of the precompute at the real bound 2e6.
"""
import sys
import time

LIMIT_SMALL = 200_000
LIMIT_REAL = 2_000_000


def sieve_tables(n):
    """d[i] = number of divisors, omega[i] = number of distinct prime factors.

    Divisor count by the harmonic 'for each d, bump every multiple' sieve
    (O(n log n)); omega by the same loop restricted to primes found with a
    plain sieve of Eratosthenes (O(n log log n)).
    """
    d = [0] * (n + 1)
    for step in range(1, n + 1):
        for m in range(step, n + 1, step):
            d[m] += 1
    omega = [0] * (n + 1)
    is_comp = bytearray(n + 1)
    for p in range(2, n + 1):
        if not is_comp[p]:
            for m in range(p, n + 1, p):
                omega[m] += 1
                if m != p:
                    is_comp[m] = 1
    return d, omega


def npf_sieve(n):
    d, omega = sieve_tables(n)
    return [d[i] - omega[i] for i in range(n + 1)], d, omega


def factorize(i):
    f = {}
    p = 2
    while p * p <= i:
        while i % p == 0:
            f[p] = f.get(p, 0) + 1
            i //= p
        p += 1
    if i > 1:
        f[i] = f.get(i, 0) + 1
    return f


def brute_npf(i):
    """Count divisors of i that are not prime, straight from the definition."""
    divs = []
    k = 1
    while k * k <= i:
        if i % k == 0:
            divs.append(k)
            if k != i // k:
                divs.append(i // k)
        k += 1
    primes = set(factorize(i))
    return sum(1 for x in divs if x not in primes)


def main():
    ans, d, omega = npf_sieve(LIMIT_SMALL)

    # 1. statement sample
    sample_in = [100, 13, 12, 2018]
    sample_out = [7, 1, 4, 2]
    got = [ans[i] for i in sample_in]
    assert got == sample_out, (got, sample_out)
    print("sample OK:", got)

    # 2 + 3. brute force and the slide-19 formula, i = 2 .. 200000
    bad = 0
    for i in range(2, LIMIT_SMALL + 1):
        f = factorize(i)
        ndiv = 1
        for q in f.values():
            ndiv *= q + 1
        if d[i] != ndiv or omega[i] != len(f):
            bad += 1
            print("sieve table mismatch at", i, d[i], ndiv, omega[i], len(f))
        if ans[i] != ndiv - len(f):
            bad += 1
            print("formula mismatch at", i)
        if i <= 20000 and brute_npf(i) != ans[i]:
            bad += 1
            print("brute mismatch at", i, brute_npf(i), ans[i])
        if bad > 5:
            sys.exit("too many mismatches")
    assert bad == 0
    print("tables match trial-division brute force for i in [2,%d] "
          "(explicit divisor enumeration up to 20000)" % LIMIT_SMALL)

    # edge cases worth naming
    assert ans[2] == 1 and ans[4] == 2 and ans[1024] == 10
    print("edges OK: NPF(2)=1 (just the divisor 1), NPF(4)=2 {1,4}, NPF(1024)=10")

    # 4. precompute cost at the real bound
    t0 = time.time()
    real, _, _ = npf_sieve(LIMIT_REAL)
    t1 = time.time()
    print("precompute to 2e6 in pure python: %.1fs; NPF(2000000)=%d"
          % (t1 - t0, real[LIMIT_REAL]))
    print("max NPF on [2,2e6] =", max(real[2:]))
    print("ALL OK")


if __name__ == "__main__":
    main()
