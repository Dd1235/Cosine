"""codechef-cyclicxor: independent brute force vs the derived closed form.

Problem: over all N! permutations P of [1..N], f(P) = max_i P[i] xor
P[(i+1) mod N] (indices cyclic).  Report min f(P) and how many permutations
attain it, mod 998244353.  Constraints: N <= 2e5, sum N <= 2e5.

Derived solution
----------------
Let H = 2^floor(log2 N), M = N - H + 1 = |{H..N}| ("high", top bit set),
L = H - 1 = |{1..H-1}| ("low").  A Hamiltonian cycle crosses the high/low cut
an even number >= 2 of times, and every crossing edge has bit log2(H) set, so
f(P) >= H.  For x < H, (H+j) ^ x = H + (j ^ x), so a crossing costs exactly H
iff x == j; that gives K = M - 1 "free" pairs {j, H+j}, j = 1..M-1.  Every
non-crossing edge is automatically < H.

  M >= 3 (K >= 2): answer H, and every crossing used must be a free pair.
  Choose 2t of the K pairs; the high side splits into t paths on M vertices
  whose endpoint set is the 2t chosen high vertices, the low side likewise on
  L vertices, and the two induced endpoint-matchings must glue into ONE cycle.
      #(path systems with a fixed endpoint matching on n vertices) =
          (n - t - 1)! / (t - 1)!          [place n-2t free vertices into t
                                            ordered interiors]
      #(pairs of perfect matchings on 2t points whose union is a single cycle)
          = (2t-1)!! * 2^(t-1) * (t-1)!
      cycles = sum_t C(K,2t) * (2t-1)!! * 2^(t-1) * (t-1)! *
               (M-t-1)!/(t-1)! * (L-t-1)!/(t-1)!,   2t <= min(K, M, L)

  M == 1 (N = H >= 4): the lone high vertex H must take the two cheapest
  crossings H^1 = H+1 and H^2 = H+2, so answer H+2, cycles = (N-3)!.
  M == 2 (N = H+1 >= 5): crossings of cost <= H+2 are (H+1,1)=H, (H,1)=H+1,
  (H,2)=H+2, (H+1,3)=H+2, and no two cost <= H+1 pairs are low-disjoint, so
  answer H+2.  Either H and H+1 are adjacent (3 low-disjoint endpoint choices,
  (N-4)! low paths each) or they are not (H sees {1,2}, H+1 sees {1,3}, vertex
  1 is a singleton low path, the other runs 2..3 in (N-5)! ways):
      cycles = 3*(N-4)! + (N-5)!
  N = 2 -> (3, 2); N = 3 -> (3, 6) (degenerate, L = 1).

Each cycle gives 2N permutations (N rotations x 2 directions) for N >= 3.
Complexity: O(max N) factorial precompute, O(M) per test, well inside limits.
"""
from math import factorial

MOD = 998244353


# ---------------- brute force: bitmask Hamiltonian-cycle count ----------------
def brute(n):
    """Exact min f and exact permutation count, by counting Hamiltonian cycles
    in the graph of edges with xor <= V for increasing candidate V."""
    vals = sorted({(a + 1) ^ (b + 1) for a in range(n) for b in range(a + 1, n)})
    if n == 2:                       # degenerate cycle: one edge seen twice
        return 3, 2
    for V in vals:
        adj = [0] * n
        for a in range(n):
            for b in range(n):
                if a != b and ((a + 1) ^ (b + 1)) <= V:
                    adj[a] |= 1 << b
        full = (1 << n) - 1
        # dp[mask][v]: paths from vertex 0 covering mask, ending at v
        dp = [[0] * n for _ in range(1 << n)]
        dp[1][0] = 1
        for mask in range(1, 1 << n):
            if not mask & 1:
                continue
            row = dp[mask]
            for v in range(n):
                c = row[v]
                if not c:
                    continue
                free = adj[v] & ~mask
                while free:
                    b = free & -free
                    u = b.bit_length() - 1
                    dp[mask | b][u] += c
                    free ^= b
        total = sum(dp[full][v] for v in range(n) if adj[v] >> 0 & 1)
        if total:
            return V, total * n      # x n: vertex 0 can sit at any position


# ---------------- closed form ----------------
def top_pow2(n):
    h = 1
    while h * 2 <= n:
        h *= 2
    return h


def solve(n):
    if n == 2:
        return 3, 2
    if n == 3:
        return 3, 6
    H = top_pow2(n)
    M, L = n - H + 1, H - 1
    if M == 1:
        return H + 2, factorial(n - 3) * 2 * n % MOD
    if M == 2:
        return H + 2, (3 * factorial(n - 4) + factorial(n - 5)) * 2 * n % MOD
    K = M - 1
    cycles, t = 0, 1
    while 2 * t <= min(K, M, L):
        dfac = 1                                     # (2t-1)!!
        for i in range(1, 2 * t, 2):
            dfac *= i
        ways = factorial(K) // (factorial(2 * t) * factorial(K - 2 * t))
        ways *= dfac * 2 ** (t - 1) * factorial(t - 1)
        ways *= factorial(M - t - 1) // factorial(t - 1)
        ways *= factorial(L - t - 1) // factorial(t - 1)
        cycles += ways
        t += 1
    return H, cycles * 2 * n % MOD


# ---------------- checks ----------------
SAMPLE = {2: (3, 2), 3: (3, 6), 4: (6, 8), 6: (4, 12),
          8: (10, 1920), 11: (8, 15840), 17: (18, 586857844)}

if __name__ == "__main__":
    import sys
    ok = True
    for n, exp in sorted(SAMPLE.items()):
        got = solve(n)
        ok &= got == exp
        print(f"sample N={n:3d} expected={exp} got={got} "
              f"{'OK ' if got == exp else 'BAD'}")
    print()
    hi = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    for n in range(2, hi + 1):
        b = brute(n)
        s = solve(n)
        s_cmp = (s[0], s[1])
        b_cmp = (b[0], b[1] % MOD)
        ok &= b_cmp == s_cmp
        print(f"brute  N={n:3d} brute={b} formula={s} "
              f"{'OK ' if b_cmp == s_cmp else 'BAD'}")
    print()
    print("ALL MATCH" if ok else "MISMATCH")
