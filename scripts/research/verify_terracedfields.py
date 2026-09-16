"""terracedfields: digit DP counting the digits 6/8 over multiples of 8 in [1,n] (+ digits of n
itself when n is not a multiple of 8), vs direct enumeration."""
import random
from functools import lru_cache

LUCKY = {'6', '8'}

def count_mult8(n):
    """total lucky digits over all multiples of 8 in [1, n] -- digit DP, state = value mod 8."""
    s = str(n); L = len(s)
    @lru_cache(maxsize=None)
    def go(i, mod, tight, started):
        """returns (count_of_numbers, total_lucky_digits) for suffixes from position i"""
        if i == L:
            ok = started and mod == 0
            return (1, 0) if ok else (0, 0)
        hi = int(s[i]) if tight else 9
        cnt = tot = 0
        for d in range(0, hi + 1):
            nstarted = started or d > 0
            nmod = (mod * 10 + d) % 8 if nstarted else 0
            c, t = go(i + 1, nmod, tight and d == hi, nstarted)
            cnt += c
            tot += t + (c if (nstarted and str(d) in LUCKY) else 0)
        return cnt, tot
    r = go(0, 0, True, False)
    go.cache_clear()
    return r[1]

def solve(n):
    res = count_mult8(n)
    if n % 8 != 0:
        res += sum(1 for ch in str(n) if ch in LUCKY)
    return res

def brute(n):
    res = sum(sum(1 for ch in str(k) if ch in LUCKY) for k in range(8, n + 1, 8))
    if n % 8 != 0:
        res += sum(1 for ch in str(n) if ch in LUCKY)
    return res

for n, exp in [(9,1),(32,2),(56,4),(18,3)]:
    assert solve(n) == exp, (n, solve(n), exp)
random.seed(5)
bad = 0
for t in range(400):
    n = random.randint(2, 30000)
    if solve(n) != brute(n):
        bad += 1; print("MISMATCH", n, solve(n), brute(n))
for n in list(range(2, 300)) + [10**18, 888888888888888888]:
    if n <= 300 and solve(n) != brute(n):
        bad += 1; print("MISMATCH small", n)
print("samples ok (1,2,4,3); mismatches =", bad, "; f(10^18) =", solve(10**18))
