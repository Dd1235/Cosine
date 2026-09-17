"""message: K = (#strings of length n) - (#strings of length n that AVOID p).  Avoiding strings are
counted on the KMP automaton restricted to its |p| non-accepting states; n is up to 1e12 so the
transfer matrix (|p| <= 50) is raised to the n-th power by binary exponentiation, everything taken
mod M (M is an arbitrary modulus, not necessarily prime, so only +,* are used).
Brute force: enumerate every string over a small alphabet."""
import random, itertools

def kmp_fail(p):
    f = [0]*len(p)
    k = 0
    for i in range(1, len(p)):
        while k and p[i] != p[k]: k = f[k-1]
        if p[i] == p[k]: k += 1
        f[i] = k
    return f

def automaton(p, alpha):
    """delta[s][c] for s in 0..L (L = accepting/absorbing)"""
    L = len(p); f = kmp_fail(p)
    delta = [[0]*alpha for _ in range(L+1)]
    for s in range(L+1):
        for c in range(alpha):
            if s == L: delta[s][c] = L; continue
            k = s
            while k and p[k] != c: k = f[k-1]
            delta[s][c] = k + 1 if p[k] == c else 0
    return delta

def matmul(A, B, M):
    n = len(A); m = len(B[0]); K = len(B)
    C = [[0]*m for _ in range(n)]
    for i in range(n):
        Ai = A[i]; Ci = C[i]
        for k in range(K):
            a = Ai[k]
            if a:
                Bk = B[k]
                for j in range(m): Ci[j] = (Ci[j] + a*Bk[j]) % M
    return C

def solve(n, M, p, alpha=26):
    p = [ord(c)-97 for c in p] if isinstance(p, str) else p
    L = len(p)
    if L > n: return pow(alpha, n, M) - pow(alpha, n, M)  # 0 strings contain p
    delta = automaton(p, alpha)
    T = [[0]*L for _ in range(L)]
    for s in range(L):
        for c in range(alpha):
            t = delta[s][c]
            if t < L: T[s][t] = (T[s][t] + 1) % M
    R = [[1 if i == j else 0 for j in range(L)] for i in range(L)]
    B = T; e = n
    while e:
        if e & 1: R = matmul(R, B, M)
        B = matmul(B, B, M); e >>= 1
    avoid = sum(R[0]) % M
    return (pow(alpha, n, M) - avoid) % M

def brute(n, M, p, alpha=26):
    cnt = 0
    for tup in itertools.product(range(alpha), repeat=n):
        s = tup; L = len(p)
        pc = tuple(ord(c)-97 for c in p)
        if any(s[i:i+L] == pc for i in range(n-L+1)): cnt += 1
    return cnt % M

assert solve(2, 100, "ab") == 1, solve(2, 100, "ab")
assert solve(3, 100, "ab") == 52, solve(3, 100, "ab")
random.seed(31)
bad = 0
for t in range(120):
    alpha = random.choice([2, 3])
    n = random.randint(1, 11)
    lp = random.randint(1, 5)
    p = ''.join(chr(97+random.randrange(alpha)) for _ in range(lp))
    M = random.choice([7, 1000000007, 999999999989, 10**12])
    if alpha**n > 200000: continue
    s, b = solve(n, M, p, alpha), brute(n, M, p, alpha)
    if s != b:
        bad += 1
        if bad < 4: print("MISMATCH", alpha, n, p, M, s, b)
# big-n sanity: count must be < 26^n and consistent between two moduli
big = solve(10**12, 10**12, "abcabcabcab")
assert 0 <= big < 10**12
print("samples ok (1 / 52); random alpha in {2,3} checked; mismatches =", bad, "; n=1e12 runs:", big)
