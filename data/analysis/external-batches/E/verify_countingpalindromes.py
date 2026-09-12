"""kattis-countingpalindromes  -- verification.

Count n-digit palindromes x (no leading zero, n<=1e18) with x = k (mod p),
p prime <= 1000, answer mod 1e9+7.

Three independent implementations:
  brute(n,p,k)  -- enumerate every n-digit palindrome (tiny n only)
  slow(n,p,k)   -- O(n/2 * 10 * p) DP over the free digit positions
  fast(n,p,k)   -- intended solution: the coefficient sequence
                   c_j = 10^j + 10^(n-1-j) (mod p) is periodic in j with
                   period L = ord_p(10) (L = 1 for p in {2,5}); the per-digit
                   generating functions live in the commutative group algebra
                   Z[Z_p] (cyclic convolution of length p), so the whole bulk
                   is one period-product raised to a huge power by binary
                   exponentiation.  O(L*10*p + p^2 log n).
"""
import random, sys, time

MOD = 10 ** 9 + 7


# ---------------------------------------------------------------- brute force
def brute_vec(n, p):
    """exact distribution of (n-digit palindrome mod p), by enumeration"""
    v = [0] * p
    if n == 1:
        for d in range(10):
            v[d % p] += 1
        return v
    h = (n + 1) // 2
    for first in range(10 ** (h - 1), 10 ** h):
        s = str(first)
        v[int(s + s[::-1][(n % 2):]) % p] += 1
    return [x % MOD for x in v]


def brute(n, p, k):
    return brute_vec(n, p)[k % p]


# ------------------------------------------------------- straightforward O(n)
def conv_sparse(v, p, c, digits):
    """multiply group-algebra element v by sum_{d in digits} t^(d*c mod p)"""
    out = [0] * p
    for d in digits:
        sh = (d * c) % p
        for r in range(p):
            out[(r + sh) % p] = (out[(r + sh) % p] + v[r]) % MOD
    return out


def slow_vec(n, p):
    if n == 1:
        v = [0] * p
        for d in range(10):
            v[d % p] += 1
        return v
    m = n - 1
    h = (n + 1) // 2
    v = [0] * p
    v[0] = 1
    # j = 0 : leading digit, 1..9, weight 10^0 + 10^m
    v = conv_sparse(v, p, (1 + pow(10, m, p)) % p, range(1, 10))
    # middle position (n odd) carries a single power
    if n % 2 == 1:
        mid = m // 2
        v = conv_sparse(v, p, pow(10, mid, p), range(10))
    last = h - 1 if n % 2 == 0 else h - 2
    for j in range(1, last + 1):
        c = (pow(10, j, p) + pow(10, m - j, p)) % p
        v = conv_sparse(v, p, c, range(10))
    return v


def slow(n, p, k):
    return slow_vec(n, p)[k % p]


# ------------------------------------------------------------------- intended
def conv(a, b, p):
    out = [0] * p
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    r = i + j
                    if r >= p:
                        r -= p
                    out[r] = (out[r] + ai * bj) % MOD
    return out


def order10(p):
    """period of 10^t mod p for t >= 1"""
    if p in (2, 5):
        return 1
    o, cur = 1, 10 % p
    while cur != 1:
        cur = cur * 10 % p
        o += 1
    return o


def fast_vec(n, p):
    if n == 1:
        v = [0] * p
        for d in range(10):
            v[d % p] += 1
        return v
    m = n - 1
    h = (n + 1) // 2
    v = [0] * p
    v[0] = 1
    v = conv_sparse(v, p, (1 + pow(10, m, p)) % p, range(1, 10))
    if n % 2 == 1:
        v = conv_sparse(v, p, pow(10, m // 2, p), range(10))
    T = (h - 1) if n % 2 == 0 else (h - 2)   # bulk = j in [1, T]
    if T >= 1:
        L = order10(p)

        # exponents are huge but only their residues mod L matter: both
        # j >= 1 and m-j >= 1 sit in the purely periodic regime of 10^t mod p
        def coef(j):
            e1 = j % L
            e2 = (m - j) % L
            a1 = pow(10, e1 + L, p)      # +L keeps the exponent >= 1
            a2 = pow(10, e2 + L, p)
            return (a1 + a2) % p

        full, rem = divmod(T, L)
        if full:
            P = [0] * p
            P[0] = 1
            for j in range(1, L + 1):
                P = conv_sparse(P, p, coef(j), range(10))
            # P ** full
            base, e, acc = P, full, [0] * p
            acc[0] = 1
            while e:
                if e & 1:
                    acc = conv(acc, base, p)
                base = conv(base, base, p)
                e >>= 1
            v = conv(v, acc, p)
        for j in range(1, rem + 1):
            v = conv_sparse(v, p, coef(j), range(10))
    return v


def fast(n, p, k):
    return fast_vec(n, p)[k % p]


# ------------------------------------------------------------------ the tests
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 97, 101]


def main():
    assert fast(1, 2, 0) == 5, fast(1, 2, 0)          # the sample
    bad = 0

    # 1) exhaustive: enumeration vs both DPs, every residue
    for n in range(1, 8):
        for p in PRIMES:
            b, f, sl = brute_vec(n, p), fast_vec(n, p), slow_vec(n, p)
            if not (b == f == sl):
                bad += 1
                print("MISMATCH tiny n=%d p=%d" % (n, p))
                for k in range(p):
                    if not (b[k] == f[k] == sl[k]):
                        print("   k=%d brute=%d fast=%d slow=%d"
                              % (k, b[k], f[k], sl[k]))
            tot = 10 if n == 1 else 9 * 10 ** ((n + 1) // 2 - 1)
            assert sum(b) == tot, (n, p, sum(b), tot)
    print("exhaustive n<=7 x 18 primes x all residues: %d mismatches" % bad)

    # 2) medium/large n: the O(n) DP vs the periodic/exponentiated one
    random.seed(1)
    for _ in range(120):
        n = random.choice([8, 9, 10, 11, 12, 13, 20, 21, 50, 51, 100, 101,
                           998, 999, 1000, 1001, 2048, 4097, 5000])
        p = random.choice(PRIMES + [103, 107, 211, 401])
        if fast_vec(n, p) != slow_vec(n, p):
            bad += 1
            print("MISMATCH med n=%d p=%d" % (n, p))
    print("medium n (O(n) DP vs fast): %d mismatches total" % bad)

    # 3) huge n: only the fast one can run.  Check the residues sum to the
    #    closed-form palindrome count mod 1e9+7, for p at the limit.
    for n, p in [(10 ** 18, 997), (10 ** 18 - 1, 997), (10 ** 18, 2),
                 (10 ** 18, 5), (10 ** 17 + 3, 101), (2, 997), (3, 997)]:
        t0 = time.time()
        v = fast_vec(n, p)
        h = (n + 1) // 2
        tot = (10 if n == 1 else 9 * pow(10, h - 1, MOD)) % MOD
        got = sum(v) % MOD
        ok = got == tot
        bad += 0 if ok else 1
        print("huge n=%d p=%d  sum=%d expected=%d %s  (%.2fs)"
              % (n, p, got, tot, "ok" if ok else "BAD", time.time() - t0))

    print("ALL OK" if bad == 0 else "FAILURES: %d" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
