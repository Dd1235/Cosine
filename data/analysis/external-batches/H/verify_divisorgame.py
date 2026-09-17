"""divisorgame: each number X is a nim pile of size Omega(X) (a proper divisor can drop the prime
count to ANY smaller value), the game is misere nim, so the mover (RR) LOSES iff
  (some pile >= 2 and xor == 0)  or  (all piles == 1 and the count is odd).
Flash wins exactly on those lists, so count = (#subsets with a composite and xor(Omega)=0)
                                            + (#subsets of primes of odd size).
Brute force: full memoised misere game search over multisets."""
import random, itertools, sys
from functools import lru_cache
sys.setrecursionlimit(100000)
MOD = 10**9 + 7

def omega(x):
    c = 0; d = 2
    while d*d <= x:
        while x % d == 0: x //= d; c += 1
        d += 1
    if x > 1: c += 1
    return c

def solve(A, B):
    """counts over non-empty subsets of [A,B], mod 1e9+7"""
    oms = [omega(x) for x in range(A, B+1)]
    primes = sum(1 for o in oms if o == 1)
    comp = [o for o in oms if o >= 2]
    # dp over xor of the composite Omegas; then primes contribute parity 1 each
    SZ = 64
    dp = [0]*SZ; dp[0] = 1
    for o in comp:                                   # each composite: in or out
        nd = [0]*SZ
        for x in range(SZ):
            if dp[x]:
                nd[x] = (nd[x] + dp[x]) % MOD
                nd[x ^ o] = (nd[x ^ o] + dp[x]) % MOD
        dp = nd
    # primes: choosing an even/odd number of them, 2^(p-1) ways each (p>0)
    if primes:
        even = odd = pow(2, primes-1, MOD)
    else:
        even, odd = 1, 0
    ans = 0
    # at least one composite chosen and total xor 0
    for x in range(SZ):
        if not dp[x]: continue
        # composite-xor x, prime parity p gives total xor x ^ (p&1 ? 1 : 0)... piles of size 1 xor in as 1
        if x == 0: ways = dp[x] * even % MOD        # needs even #primes; but x==0 includes "no composite"
        elif x == 1: ways = dp[x] * odd % MOD
        else: ways = 0
        ans = (ans + ways) % MOD
    # subtract the composite-free part that slipped in (x==0, no composite chosen, even primes)
    ans = (ans - even) % MOD                        # the empty-composite choice counted with even primes
    # all-prime (no composite) subsets with an odd number of primes
    ans = (ans + odd) % MOD
    return ans % MOD

def brute(A, B):
    @lru_cache(maxsize=None)
    def win(state):
        """True if the player to move WINS (last move loses)"""
        moves = set()
        for i, x in enumerate(state):
            for d in range(1, x):
                if x % d == 0:
                    ns = list(state); ns[i] = d
                    moves.add(tuple(sorted(ns)))
        if not moves: return True                   # cannot move -> opponent took the last move
        return any(not win(m) for m in moves)
    nums = list(range(A, B+1))
    cnt = 0
    for r in range(1, len(nums)+1):
        for sub in itertools.combinations(nums, r):
            if not win(tuple(sorted(sub))): cnt += 1   # RR (first player) loses => Flash wins
    return cnt

for (A, B), exp in [((2,4),2), ((2,5),4), ((2,6),8), ((2,7),16)]:
    got = solve(A, B)
    assert got == exp, (A, B, got, exp)
bad = 0
for A in range(2, 13):
    for B in range(A, min(A+9, 21)):
        s, b = solve(A, B), brute(A, B)
        if s != b:
            bad += 1
            if bad < 6: print("MISMATCH", A, B, s, b)
print("samples ok (2,4,8,16); brute-force ranges checked; mismatches =", bad)
