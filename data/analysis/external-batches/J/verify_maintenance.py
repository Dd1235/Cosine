"""Kattis maintenance (2015 ICPC Singapore, K).

Task: K is given as up to 350 two-digit prime factors (each prime repeated at most
100 times, and K has at most 10^10 divisors).  Buy servers all of the same size M
bytes with M | K; the cost is M + K/M dollars.  Print the minimum cost mod 1e9+7.

Solution under test: M + K/M is minimised by the divisor of K closest to sqrt(K)
from below, because f(M) = M + K/M falls on (0, sqrt K] and rises after it, and the
two candidates M and K/M give the same cost.  K itself has ~1200 bits and up to
10^10 divisors, so the divisors cannot be enumerated: split the prime powers into
two groups whose divisor counts are as equal as possible (greedy on the factors
e_i+1, each <= 101, giving O(sqrt(D)) per side), enumerate each group's divisors,
sort the second list, and for every d1 of the first binary-search the largest d2
with d1*d2 <= isqrt(K).  The best product is M; the cost is
(M + K/M) mod p, K/M taken mod p with a modular inverse (p = 1e9+7 exceeds every
prime factor, so M is never 0 mod p).
O(sqrt(D) log sqrt(D)) big-integer comparisons, O(sqrt(D)) memory.

Brute force: enumerate every divisor of K directly (small inputs only).
"""
import random
from math import isqrt, gcd

MOD = 10 ** 9 + 7

def parse(s):
    e = {}
    for i in range(0, len(s), 2):
        p = int(s[i:i + 2])
        e[p] = e.get(p, 0) + 1
    return e

def divisors_of(group):
    ds = [1]
    for p, k in group:
        cur = []
        pw = 1
        for _ in range(k + 1):
            cur.extend(d * pw for d in ds)
            pw *= p
        ds = cur
    return ds

def solve(s):
    e = parse(s)
    K = 1
    for p, k in e.items():
        K *= p ** k
    items = sorted(e.items(), key=lambda t: -(t[1] + 1))
    ga, gb, ca, cb = [], [], 1, 1
    for p, k in items:                      # greedy balance of the divisor counts
        if ca <= cb:
            ga.append((p, k)); ca *= k + 1
        else:
            gb.append((p, k)); cb *= k + 1
    A = divisors_of(ga)
    B = sorted(divisors_of(gb))
    S = isqrt(K)
    best = 1
    import bisect
    for d1 in A:
        if d1 > S:
            continue
        lim = S // d1
        i = bisect.bisect_right(B, lim)
        if i:
            cand = d1 * B[i - 1]
            if cand > best:
                best = cand
    M = best
    other = K // M
    return (M % MOD + other % MOD) % MOD, M, K

def brute(s):
    e = parse(s)
    K = 1
    for p, k in e.items():
        K *= p ** k
    ds = divisors_of(sorted(e.items()))
    return min((d + K // d) for d in ds) % MOD

def samples():
    for s, want in [("020302", 7), ("1311", 24), ("11", 12)]:
        got = solve(s)[0]
        assert got == want, (s, got, want)
    print("samples OK")

def fuzz(trials=400):
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
              53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    rnd = random.Random(4242)
    for _ in range(trials):
        n = rnd.randint(1, 9)
        s = "".join("%02d" % rnd.choice(primes[:rnd.randint(1, 8)]) for _ in range(n))
        a, b = solve(s)[0], brute(s)
        if a != b:
            print("MISMATCH", s, a, b)
            return False
    print("fuzz OK (%d random factorisations vs full divisor enumeration)" % trials)
    return True

def stress():
    """worst-shaped input: 350 factors, ~10^10 divisors, ~1200-bit K"""
    import time
    # 2^100 * 3^100 * 5^100 has 101^3 ~ 1.03e6 divisors; add more primes to approach 1e10
    e = {2: 100, 3: 100, 5: 100, 7: 20, 11: 9, 13: 9, 17: 4, 19: 4}
    s = "".join("%02d" % p * k for p, k in e.items())
    D = 1
    for k in e.values():
        D *= k + 1
    t = time.time()
    ans, M, K = solve(s)
    print("stress: %d prime factors, K has %d bits, %d divisors -> answer %d in %.1fs"
          % (len(s) // 2, K.bit_length(), D, ans, time.time() - t))
    assert M * (K // M) == K and M <= isqrt(K)

if __name__ == "__main__":
    samples()
    assert fuzz()
    stress()
