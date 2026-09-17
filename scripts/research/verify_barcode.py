"""Barcode: count length-N red/blue strings that have (#blue == #red) OR (no two
consecutive blue), mod a PRIME M with 1 < M <= 1e7, N <= 1e6, up to 20 datasets.

Solution (inclusion-exclusion on the two conditions):
  |A| = C(N, N/2) if N even else 0
  |B| = Fib(N+2)  (F(1)=F(2)=1), the no-two-adjacent count
  |A and B| = C(N/2+1, N/2) = N/2+1 for even N, else 0
  K = |A| + |B| - |A and B|.
The catch: M can be far smaller than N (the samples use M=997 with N up to 1e6),
so C(N,N/2) mod M needs LUCAS' THEOREM (M prime).  Fib is iterated mod M.
O(N) per dataset time, O(M) space for the factorial table (or O(1) with on-the-fly).

Check: against a direct enumeration of all 2^N strings for N <= 20, for several
primes M including tiny ones.
"""
from itertools import product

def lucas_C(n, k, p):
    """C(n,k) mod prime p"""
    if k < 0 or k > n: return 0
    res = 1
    # factorials mod p up to p-1
    f = [1]*p
    for i in range(1, p): f[i] = f[i-1]*i % p
    def small(a, b):
        if b < 0 or b > a: return 0
        return f[a]*pow(f[b], p-2, p)%p*pow(f[a-b], p-2, p)%p
    while n or k:
        a, b = n % p, k % p
        if b > a: return 0
        res = res * small(a, b) % p
        n //= p; k //= p
    return res

def solve(N, M):
    if N % 2 == 0:
        A = lucas_C(N, N//2, M)
        AB = (N//2 + 1) % M
    else:
        A = 0; AB = 0
    # Fib(N+2) with F(1)=F(2)=1
    a, b = 1, 1           # F(1), F(2)
    for _ in range(N):    # advance to F(N+2)
        a, b = b, (a+b) % M
    B = b % M
    return (A + B - AB) % M

def brute(N, M):
    cnt = 0
    for s in product([0,1], repeat=N):   # 1 = blue
        blue = sum(s)
        cond1 = (blue*2 == N)
        cond2 = all(not (s[i]==1 and s[i+1]==1) for i in range(N-1))
        if cond1 or cond2: cnt += 1
    return cnt % M

def main():
    for n, exp in [(1,2),(2,3),(3,5),(5,13),(7,34),(9,89)]:
        got = solve(n, 997)
        assert got == exp, (n, got, exp)
    print("samples OK")
    bad = 0
    for M in [2,3,5,7,11,13,997,10**7-1]:
        if M == 10**7-1: continue
        for N in range(1, 17):
            f = solve(N, M); b = brute(N, M)
            if f != b:
                bad += 1
                if bad < 8: print("MISMATCH N=%d M=%d fast=%d brute=%d" % (N,M,f,b))
    print("exhaustive N=1..16 over primes 2,3,5,7,11,13,997: mismatches =", bad)
    assert bad == 0
    # large-N sanity: lucas needed
    print("N=10^6, M=997 ->", solve(10**6, 997))
    print("N=10^6, M=9999991 ->", solve(10**6, 9999991))
    print("barcode: OK")

main()
