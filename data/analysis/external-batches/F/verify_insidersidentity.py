"""Insider's Identity: automaton DP vs exhaustive enumeration.

Count binary strings of length n that contain an occurrence of P ('1' must meet
'1', '*' meets anything).  Complement-count the strings with NO occurrence with
a DP whose state is the set of pattern prefixes still alive - i.e. the
Aho-Corasick state of the (up to 2^15) concrete completions of P, maintained as
a shift-and bitmask so it is built lazily.  Stars <= m/2 <= 15, so the reachable
state count is bounded by the trie size, at most about 30*2^15.
"""
import random
from itertools import product


def solve(n, P):
    m = len(P)
    if m > n:
        return 0
    star = 0
    for i, ch in enumerate(P):
        if ch == '*':
            star |= 1 << i
    top = 1 << (m - 1)
    cur = {1: 1}                       # alive-prefix set; length 0 always alive
    for _ in range(n):
        nxt = {}
        for A, v in cur.items():
            if not (A & top):          # append '1'
                B = (A << 1) | 1
                nxt[B] = nxt.get(B, 0) + v
            if not ((A & top) and P[m - 1] == '*'):   # append '0'
                B = ((A & star) << 1) | 1
                nxt[B] = nxt.get(B, 0) + v
        cur = nxt
    return (1 << n) - sum(cur.values())


def brute(n, P):
    m = len(P)
    tot = 0
    for bits in product('01', repeat=n):
        s = ''.join(bits)
        ok = False
        for i in range(n - m + 1):
            if all(P[j] == '*' or s[i + j] == '1' for j in range(m)):
                ok = True
                break
        tot += ok
    return tot


def main():
    assert solve(10, "1") == 1023
    assert solve(3, "1*1") == 2
    print("samples ok")
    random.seed(9)
    for _ in range(500):
        m = random.randint(1, 8)
        ones = max(1, (m + 1) // 2)
        P = ['1'] * ones + ['*'] * (m - ones)
        random.shuffle(P)
        P = ''.join(P)
        n = random.randint(1, 14)
        a, b = solve(n, P), brute(n, P)
        assert a == b, (n, P, a, b)
    # explicit m > n and all-star-tail shapes
    for P in ["1", "11", "1*", "*1", "1**1", "1*1*1", "11*1"]:
        for n in range(1, 13):
            assert solve(n, P) == brute(n, P), (n, P)
    print("500 random + edge patterns match exhaustive count")


main()
