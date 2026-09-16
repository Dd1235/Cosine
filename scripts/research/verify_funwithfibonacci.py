"""Fun with Fibonacci: the Pisano-period tower, checked against exact big-int
nesting and against the ten sample queries.

F mod m is purely periodic with period pi(m), so G(k,n) mod m_0 needs
G(k-1,n) mod m_1 where m_1 = pi(m_0), and so on.  The tower m_0, pi(m_0),
pi(pi(m_0)), ... always reaches a fixed point pi(M) = M within a couple of dozen
steps (24, 120, 600, 3000, 15000, 375000, ... are such fixed points), and below
that level the whole recursion is a single map T(x) = F_x mod M iterated on
Z_M, so the remaining k - D steps are resolved by finding T's rho.
"""
from math import gcd


def fibpair(n, m):
    if n == 0:
        return (0 % m, 1 % m)
    a, b = fibpair(n >> 1, m)
    c = (a * ((2 * b - a) % m)) % m
    d = (a * a + b * b) % m
    return (d, (c + d) % m) if n & 1 else (c, d)


def F(x, m):
    return fibpair(x, m)[0] if m > 1 else 0


def factor(n):
    f = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def divisors(n):
    ds = [1]
    for p, e in factor(n).items():
        ds = [d * p ** i for d in ds for i in range(e + 1)]
    return sorted(ds)


def pisano_prime(p):
    if p == 2:
        return 3
    if p == 5:
        return 20
    cand = p - 1 if p % 5 in (1, 4) else 2 * (p + 1)
    for d in divisors(cand):
        a, b = fibpair(d, p)
        if a == 0 and b == 1 % p:
            return d
    raise RuntimeError(p)


_pc = {}


def pisano(m):
    if m == 1:
        return 1
    if m in _pc:
        return _pc[m]
    r = 1
    for p, e in factor(m).items():
        q = pisano_prime(p) * p ** (e - 1)
        r = r * q // gcd(r, q)
    _pc[m] = r
    return r


def solve(n, k, p):
    tower = [p]
    while len(tower) <= k:
        nxt = pisano(tower[-1])
        if nxt == tower[-1]:
            break
        tower.append(nxt)
    D = len(tower) - 1
    if k <= D:
        v = n % tower[k]
        for i in range(k - 1, -1, -1):
            v = F(v, tower[i])
        return v % tower[0]
    M = tower[D]
    steps = k - D
    seen = {}
    u, j = n % M, 0
    while j < steps:
        if u in seen:
            start = seen[u]
            clen = j - start
            for _ in range((steps - start) % clen):
                u = F(u, M)
            break
        seen[u] = j
        u = F(u, M)
        j += 1
    v = u
    for i in range(D - 1, -1, -1):
        v = F(v, tower[i])
    return v % tower[0]


def exact_G(n, k, cap=30000):
    """Exact G(k,n) as a big int, or None when an intermediate index blows up."""
    fb = [0, 1]
    while len(fb) <= cap:
        fb.append(fb[-1] + fb[-2])
    v = n
    for _ in range(k):
        if v > cap:
            return None
        v = fb[v]
    return v


def main():
    samples = [(1, 1, 1000000, 1), (1, 2, 1000000, 1), (1, 3, 1000000, 1),
               (2, 1, 1000000, 1), (2, 2, 1000000, 1), (2, 3, 1000000, 1),
               (3, 1, 1000000, 2), (3, 2, 1000000, 1), (3, 3, 1000000, 1),
               (10 ** 18, 10 ** 18, 1000000, 890625)]
    for (n, k, p, want) in samples:
        got = solve(n, k, p)
        assert got == want, (n, k, p, got, want)
    print("all 10 sample queries ok (including n=k=1e18, p=1e6 -> 890625)")

    import random
    random.seed(1)
    checked = 0
    for n in range(1, 13):
        for k in range(1, 6):
            ex = exact_G(n, k)
            if ex is None:
                continue
            for p in [1, 2, 3, 7, 10, 97, 1000, 65536, 999983, 1000000]:
                assert solve(n, k, p) == ex % p, (n, k, p, solve(n, k, p), ex % p)
                checked += 1
    print("%d (n,k,p) triples match exact big-integer nesting" % checked)

    # n <= 5 has a known closed form for every k, which exercises the deep path
    closed = {1: lambda k: 1, 2: lambda k: 1,
              3: lambda k: 2 if k == 1 else 1,
              4: lambda k: [3, 2, 1][k - 1] if k <= 3 else 1,
              5: lambda k: 5}
    deep = 0
    for n in range(1, 6):
        for k in [1, 2, 3, 4, 5, 10, 1000, 10 ** 9, 10 ** 18]:
            for p in [2, 7, 1000, 1000000, 999983, 524288]:
                assert solve(n, k, p) == closed[n](k) % p, (n, k, p)
                deep += 1
    print("%d deep-k queries (k up to 1e18) match the closed form for n<=5" % deep)

    # tower shape report
    for p in [2, 10, 100, 12345, 524288, 999983, 1000000]:
        t = [p]
        while pisano(t[-1]) != t[-1]:
            t.append(pisano(t[-1]))
        print("  pi-tower(%d) depth %d, fixed point %d" % (p, len(t), t[-1]))


main()
