"""Kattis mububa (2015 ICPC Singapore, H).

Task: cut the array of N<=3000 briefcase values into consecutive blocks whose sums
are non-decreasing from left to right; maximise the number of blocks.

Solution under test: dp over prefixes keeping the Pareto-best pair
(max number of blocks, and the smallest possible last-block sum achieving it).
dp[i] = max over j<i with pre[i]-pre[j] >= last[j] of dp[j]+1, ties broken by the
largest such j (smallest last block).  O(N^2) time, O(N) space.

The question the fuzz answers: is it safe to keep ONLY that one pair per prefix,
i.e. can a prefix split with fewer blocks but a smaller last block ever win?
Brute force: exhaustive over all 2^(n-1) cut sets.
"""
import itertools, random

NEG = -1

def solve(a):
    n = len(a)
    pre = [0] * (n + 1)
    for i, v in enumerate(a):
        pre[i + 1] = pre[i] + v
    cnt = [0] * (n + 1)      # cnt[i] = max blocks for prefix of length i
    last = [0] * (n + 1)     # last[i] = min last-block sum attaining cnt[i]
    for i in range(1, n + 1):
        best_c, best_l = NEG, 0
        for j in range(i - 1, -1, -1):
            s = pre[i] - pre[j]
            if s >= last[j] and cnt[j] + 1 > best_c:
                best_c, best_l = cnt[j] + 1, s
        cnt[i], last[i] = best_c, best_l
    return cnt[n]

def brute(a):
    n = len(a)
    best = 1
    for mask in range(1 << (n - 1)):
        cuts = [i + 1 for i in range(n - 1) if mask >> i & 1]
        bounds = [0] + cuts + [n]
        sums = [sum(a[bounds[k]:bounds[k + 1]]) for k in range(len(bounds) - 1)]
        if all(sums[k] <= sums[k + 1] for k in range(len(sums) - 1)):
            best = max(best, len(sums))
    return best

def samples():
    assert solve([1, 2, 1, 2]) == 3, solve([1, 2, 1, 2])
    assert solve([6, 4, 2, 2, 2, 2]) == 3, solve([6, 4, 2, 2, 2, 2])
    print("samples OK")

def fuzz(trials=4000):
    rnd = random.Random(5)
    for _ in range(trials):
        n = rnd.randint(2, 11)
        a = [rnd.randint(1, 8) for _ in range(n)]
        x, y = solve(a), brute(a)
        if x != y:
            print("MISMATCH", a, x, y)
            return False
    # a few adversarial shapes: big head, tiny tail
    for _ in range(600):
        n = rnd.randint(4, 12)
        a = [rnd.choice([1, 1, 1, 2, 30, 100]) for _ in range(n)]
        if solve(a) != brute(a):
            print("MISMATCH", a, solve(a), brute(a))
            return False
    print("fuzz OK (%d random + 600 skewed cases, n<=12)" % trials)
    return True

if __name__ == "__main__":
    samples()
    assert fuzz()
