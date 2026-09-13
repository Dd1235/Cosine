"""kattis-steppeonit / "Steppe on It" (ICPC WF 2024) -- verification.

Problem: tree with n vertices (parent of i is v_i < i, edge weight t_i),
choose f vertices to host fire engines, minimise
    max_{u in V} min_{c in chosen} dist(u, c)
i.e. the vertex-restricted f-center problem on a weighted tree.

Intended solution: binary search on the answer R; feasibility "can R be
covered with <= f centers?" is a linear bottom-up greedy over the tree.

This file:
  * fast()   -- the intended O(n log W) algorithm
  * brute()  -- exhaustive over all C(n,f) center sets, O(C(n,f) * n^2)
  * random cross-check + the two official samples.
"""
import itertools, random, sys


# ---------------------------------------------------------------- intended
def feasible(n, par, w, R, f):
    """Greedy: min #centers of radius R covering the tree; return count <= f.

    Post-order (vertices are numbered so par[i] < i, so a reverse index scan
    IS a post-order).  Per vertex u keep
        need[u] = max dist from u to a still-uncovered vertex in subtree(u)
                  (-1 = nothing uncovered)
        cov[u]  = max leftover radius R - dist(u, c) of a chosen center c in
                  subtree(u)   (-1 = none reaches u)
    A center is placed at u only when forced, i.e. when pushing the deepest
    uncovered vertex one edge further toward the parent would break R.
    """
    NEG = -1
    need = [0] * (n + 1)      # every vertex initially needs covering (dist 0)
    cov = [NEG] * (n + 1)
    used = 0
    for u in range(n, 0, -1):
        if cov[u] >= need[u]:          # deepest uncovered is already reached
            need[u] = NEG
        if need[u] >= 0:
            pu = par[u]
            # forced to place here?  root, or the parent edge overflows R
            if pu == 0 or need[u] + w[u] > R:
                used += 1
                if used > f:
                    return False
                cov[u] = R
                need[u] = NEG
        if u > 1:
            p, e = par[u], w[u]
            if need[u] >= 0 and need[u] + e > need[p]:
                need[p] = need[u] + e
            if cov[u] - e > cov[p]:
                cov[p] = cov[u] - e
    return used <= f


def fast(n, par, w, f):
    lo, hi = 0, 0
    for u in range(2, n + 1):
        hi += w[u]
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(n, par, w, mid, f):
            hi = mid
        else:
            lo = mid + 1
    return lo


# ------------------------------------------------------------------- brute
def brute(n, par, w, f):
    INF = float('inf')
    d = [[INF] * (n + 1) for _ in range(n + 1)]
    for u in range(1, n + 1):
        d[u][u] = 0
    for u in range(2, n + 1):
        d[u][par[u]] = d[par[u]][u] = w[u]
    for k in range(1, n + 1):
        dk = d[k]
        for i in range(1, n + 1):
            di = d[i]
            v = di[k]
            if v == INF:
                continue
            for j in range(1, n + 1):
                if v + dk[j] < di[j]:
                    di[j] = v + dk[j]
    best = INF
    for cs in itertools.combinations(range(1, n + 1), min(f, n)):
        worst = max(min(d[u][c] for c in cs) for u in range(1, n + 1))
        if worst < best:
            best = worst
    return best


# ----------------------------------------------------------------- samples
def parse(text):
    it = iter(text.split())
    n = int(next(it)); f = int(next(it))
    par = [0] * (n + 1); w = [0] * (n + 1)
    for i in range(2, n + 1):
        par[i] = int(next(it)); w[i] = int(next(it))
    return n, f, par, w


SAMPLES = [("6 2  1 8  2 7  2 7  3 6  3 5", 8),
           ("3 3  1 1000  2 1000", 0)]

for text, want in SAMPLES:
    n, f, par, w = parse(text)
    got = fast(n, par, w, f)
    print("sample n=%d f=%d -> %d (expected %d) %s"
          % (n, f, got, want, "OK" if got == want else "FAIL"))
    assert got == want

# ------------------------------------------------------------ random check
random.seed(20240912)
bad = 0
for trial in range(4000):
    n = random.randint(1, 9)
    f = random.randint(1, n)
    par = [0] * (n + 1); w = [0] * (n + 1)
    for i in range(2, n + 1):
        par[i] = random.randint(1, i - 1)
        w[i] = random.choice([1, 1, 2, 3, 5, 10])
    a, b = fast(n, par, w, f), brute(n, par, w, f)
    if a != b:
        bad += 1
        print("MISMATCH n=%d f=%d par=%s w=%s fast=%s brute=%s"
              % (n, f, par[2:], w[2:], a, b))
        if bad > 5:
            sys.exit(1)
print("random small: 4000 trials, %d mismatches" % bad)

# deeper/path-like trees, still brute-forceable
for trial in range(800):
    n = random.randint(6, 10)
    f = random.randint(1, 4)
    par = [0] * (n + 1); w = [0] * (n + 1)
    for i in range(2, n + 1):
        par[i] = i - 1 if random.random() < 0.75 else random.randint(1, i - 1)
        w[i] = random.randint(1, 20)
    a, b = fast(n, par, w, f), brute(n, par, w, f)
    if a != b:
        bad += 1
        print("MISMATCH(path) n=%d f=%d par=%s w=%s fast=%s brute=%s"
              % (n, f, par[2:], w[2:], a, b))
print("random path-ish: 800 trials, total mismatches %d" % bad)

# ------------------------------------------------------------ scale timing
import time
n = 100000
par = [0] * (n + 1); w = [0] * (n + 1)
for i in range(2, n + 1):
    par[i] = random.randint(max(1, i - 3), i - 1)   # deep-ish tree
    w[i] = random.randint(1, 10000)
t0 = time.time()
ans = fast(n, par, w, 300)
print("n=100000 f=300 -> %d in %.2fs (pure python)" % (ans, time.time() - t0))
