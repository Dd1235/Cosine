"""alicedigital: O(n) scan between barriers (a[i] <= m) + prefix sums, vs O(n^2) brute force
over every subarray (min == m and exactly one occurrence of m)."""
import random

def solve(a, m):
    n = len(a)
    pre = [0]*(n+1)
    for i, x in enumerate(a): pre[i+1] = pre[i] + x
    bar = [i for i, x in enumerate(a) if x <= m]   # positions that stop extension
    best = None
    for k, p in enumerate(bar):
        if a[p] != m: continue
        l = bar[k-1] + 1 if k > 0 else 0
        r = bar[k+1] - 1 if k + 1 < len(bar) else n - 1
        w = pre[r+1] - pre[l]
        if best is None or w > best: best = w
    return best

def brute(a, m):
    n = len(a); best = None
    for i in range(n):
        for j in range(i, n):
            sub = a[i:j+1]
            if min(sub) == m and sub.count(m) == 1:
                s = sum(sub)
                if best is None or s > best: best = s
    return best

assert solve([1,3,2,6,2,4], 2) == 12, solve([1,3,2,6,2,4], 2)
random.seed(3)
bad = 0
for t in range(3000):
    n = random.randint(1, 12)
    m = random.randint(1, 4)
    a = [random.randint(1, 6) for _ in range(n)]
    if m not in a: a[random.randrange(n)] = m
    s, b = solve(a, m), brute(a, m)
    if s != b:
        bad += 1
        if bad < 5: print("MISMATCH", a, m, s, b)
print("sample ok (12); mismatches =", bad)
