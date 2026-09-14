"""codechef-rebxor / "Nikitosh and xor".

Max over 1<=l1<=r1<l2<=r2<=N of xor(A[l1..r1]) + xor(A[l2..r2]).
N <= 4e5, A_i <= 1e9.

Intended solution:
  P[i] = A[1]^...^A[i], P[0]=0.  xor(l..r) = P[r]^P[l-1].
  best_end[i]  = max over r<=i of (max over l<=r of P[r]^P[l-1])
  best_start[i]= symmetric from the right (same routine on reversed array)
  answer = max over split k in [1, N-1] of best_end[k] + best_start[k+1]
  "max over l<=r of P[r]^P[l-1]" is a classic binary-trie query: insert
  P[0..r-1] into a 30-bit binary trie and greedily descend taking the
  opposite bit of P[r] where a child exists.
  O(N * 30) time and memory.
"""
import random, sys

BITS = 30  # A_i <= 1e9 < 2^30, so every prefix xor < 2^30


class Trie:
    __slots__ = ("ch",)

    def __init__(self):
        self.ch = [[-1, -1]]  # node 0 = root

    def insert(self, x):
        ch = self.ch
        cur = 0
        for b in range(BITS - 1, -1, -1):
            d = (x >> b) & 1
            nxt = ch[cur][d]
            if nxt == -1:
                ch.append([-1, -1])
                nxt = len(ch) - 1
                ch[cur][d] = nxt
            cur = nxt

    def query_max_xor(self, x):
        ch = self.ch
        cur = 0
        res = 0
        for b in range(BITS - 1, -1, -1):
            d = (x >> b) & 1
            want = d ^ 1
            if ch[cur][want] != -1:
                res |= 1 << b
                cur = ch[cur][want]
            else:
                cur = ch[cur][d]
        return res


def best_prefix(a):
    """b[i] (1-indexed, len n+1) = max xor of a subarray inside a[0..i-1]."""
    n = len(a)
    t = Trie()
    t.insert(0)          # P[0]
    p = 0
    b = [0] * (n + 1)
    for i in range(1, n + 1):
        p ^= a[i - 1]
        b[i] = max(b[i - 1], t.query_max_xor(p))
        t.insert(p)
    return b


def solve(a):
    n = len(a)
    left = best_prefix(a)
    right_rev = best_prefix(a[::-1])
    # right[k] = best subarray inside a[k-1 .. n-1]  (1-indexed start k)
    # in reversed array that is the prefix of length n-k+1
    ans = 0
    for k in range(1, n):          # split: first part inside a[0..k-1]
        ans = max(ans, left[k] + right_rev[n - k])
    return ans


def brute(a):
    n = len(a)
    # px[i] = xor of a[0..i-1]
    px = [0] * (n + 1)
    for i in range(n):
        px[i + 1] = px[i] ^ a[i]
    best = 0
    for r1 in range(1, n + 1):
        for l1 in range(1, r1 + 1):
            v1 = px[r1] ^ px[l1 - 1]
            for r2 in range(r1 + 1, n + 1):
                for l2 in range(r1 + 1, r2 + 1):
                    best = max(best, v1 + (px[r2] ^ px[l2 - 1]))
    return best


def main():
    # sample
    a = [1, 2, 3, 1, 2]
    assert solve(a) == 6, solve(a)
    assert brute(a) == 6
    print("sample ok: 6")

    random.seed(7)
    for it in range(4000):
        n = random.randint(2, 8)
        hi = random.choice([1, 3, 7, 15, 1000, 10**9])
        a = [random.randint(0, hi) for _ in range(n)]
        s, b = solve(a), brute(a)
        if s != b:
            print("MISMATCH", a, s, b)
            sys.exit(1)
    print("4000 random small cases ok")

    # timing at the real limit
    import time
    n = 400000
    a = [random.randint(0, 10**9) for _ in range(n)]
    t0 = time.time()
    r = solve(a)
    print("n=4e5 ->", r, "in %.2fs (python; C++ is ~50x faster)" % (time.time() - t0))


main()
