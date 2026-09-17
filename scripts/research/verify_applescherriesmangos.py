"""Kattis applescherriesmangos (2015 ICPC Singapore, B).

Task: count the arrangements of A apples, C cherries and M mangos in a row with no
two equal fruits adjacent, modulo 1e9+7.  1 <= A, C, M <= 200000.

Solution under test (Smirnov / Carlitz words).  Group each letter's occurrences
into i maximal runs and then forbid runs of length >= 2 by inclusion-exclusion:
the generating function of adjacent-distinct words is 1/(1 - x/(1+x) - y/(1+y) -
z/(1+z)), whose coefficient extraction gives

  ans = sum_{i,j,k >= 1} (-1)^{(A-i)+(C-j)+(M-k)} C(A-1,i-1) C(C-1,j-1) C(M-1,k-1)
        * (i+j+k)! / (i! j! k!)

C(A-1,i-1) chooses where to cut A apples into i runs, and the multinomial counts
the interleavings of the runs with no two like runs adjacent (after the sign
cancellation).  Written that way it is O(A*C*M), far too slow, but it factors:
with a_i = (-1)^{A-i} C(A-1,i-1)/i!, ans = sum_n n! * (a * c * m)[n], a *single*
triple convolution of polynomials of degree <= 200000.  Two NTT-based convolutions
(three NTT primes + CRT, or Kronecker substitution) give O(n log n) time and O(n)
space with n = A+C+M <= 600000.

This script checks: (1) the triple sum against exhaustive enumeration of the
multiset permutations, and (2) that the convolution regrouping reproduces the
triple sum exactly (done here with schoolbook convolution, which is what the NTT
computes).
"""
from itertools import permutations
from math import comb

MOD = 10 ** 9 + 7
LIM = 2_000_005
fact = [1] * LIM
for i in range(1, 8):    # grown lazily below; small for the test sizes
    fact[i] = fact[i - 1] * i % MOD

def _facts(n):
    f = [1] * (n + 1)
    for i in range(1, n + 1):
        f[i] = f[i - 1] * i % MOD
    inv = [1] * (n + 1)
    inv[n] = pow(f[n], MOD - 2, MOD)
    for i in range(n, 0, -1):
        inv[i - 1] = inv[i] * i % MOD
    return f, inv

def triple_sum(A, C, M):
    n = A + C + M
    f, invf = _facts(n + 1)
    tot = 0
    for i in range(1, A + 1):
        ca = comb(A - 1, i - 1) % MOD * (1 if (A - i) % 2 == 0 else -1)
        for j in range(1, C + 1):
            cc = comb(C - 1, j - 1) % MOD * (1 if (C - j) % 2 == 0 else -1)
            for k in range(1, M + 1):
                cm = comb(M - 1, k - 1) % MOD * (1 if (M - k) % 2 == 0 else -1)
                tot += ca * cc * cm % MOD * f[i + j + k] % MOD * invf[i] % MOD * invf[j] % MOD * invf[k]
    return tot % MOD

def conv_form(A, C, M):
    """same value, regrouped as one triple convolution (schoolbook here, NTT in the real solution)"""
    n = A + C + M
    f, invf = _facts(n + 1)
    def poly(L):
        p = [0] * (L + 1)
        for i in range(1, L + 1):
            s = 1 if (L - i) % 2 == 0 else -1
            p[i] = s * comb(L - 1, i - 1) % MOD * invf[i] % MOD
        return p
    def mul(p, q):
        r = [0] * (len(p) + len(q) - 1)
        for i, pi in enumerate(p):
            if pi:
                for j, qj in enumerate(q):
                    r[i + j] = (r[i + j] + pi * qj) % MOD
        return r
    r = mul(mul(poly(A), poly(C)), poly(M))
    return sum(f[t] * v for t, v in enumerate(r)) % MOD

def brute(A, C, M):
    word = "a" * A + "c" * C + "m" * M
    seen = set()
    for p in set(permutations(word)):
        if all(p[i] != p[i + 1] for i in range(len(p) - 1)):
            seen.add(p)
    return len(seen) % MOD

def samples():
    for (A, C, M), want in [((1, 2, 1), 6), ((2, 2, 2), 30), ((1, 1, 10), 0)]:
        got = triple_sum(A, C, M)
        assert got == want, (A, C, M, got, want)
        got2 = conv_form(A, C, M)
        assert got2 == want, (A, C, M, got2, want)
    print("samples OK (both the triple sum and the convolution regrouping)")

def fuzz():
    ok = True
    for A in range(1, 5):
        for C in range(1, 5):
            for M in range(1, 5):
                b = brute(A, C, M)
                t = triple_sum(A, C, M)
                c = conv_form(A, C, M)
                if not (b == t == c):
                    print("MISMATCH", A, C, M, b, t, c)
                    ok = False
    print("fuzz OK (all 1<=A,C,M<=4 match exhaustive enumeration)" if ok else "FAILED")
    return ok

if __name__ == "__main__":
    samples()
    assert fuzz()
