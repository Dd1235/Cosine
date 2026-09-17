"""Engaging with Loyal Customers: n customers, m gifts (both <= 1000), k <= n*m
feedback cards (i,j,p) with p in [1,30000]; unlisted pairs are worth 0.  Assign at
most one gift per customer and at most one customer per gift, maximising the total
satisfaction, and print one optimal assignment.

Solution: this is the (rectangular, non-perfect) MAXIMUM-WEIGHT BIPARTITE MATCHING
= assignment problem.  Pad the n x m satisfaction matrix with zeros and run the
Hungarian / Kuhn-Munkres algorithm (JV form, O(min*max^2) ~ 1e9 worst case but
cache-friendly on a dense 1000x1000 matrix); equivalently min-cost max-flow with
negated costs and Johnson potentials, one shortest-path augmentation per matched
pair.  Zero-weight pairs are dropped from the printed assignment.
O(n*m + n^2*m) time, O(n*m) space.

Check: Hungarian vs brute-force enumeration of all partial matchings on small
random instances.
"""
import random
from itertools import permutations

INF = float('inf')

def hungarian(a):
    """a is 1-indexed cost matrix (n+1) x (m+1), n<=m, MINIMISES.  Returns (cost, match)
       where match[j] = i assigned to column j (0 = none).  Classic e-maxx JV."""
    n = len(a)-1; m = len(a[0])-1
    u = [0]*(n+1); v = [0]*(m+1); p = [0]*(m+1); way = [0]*(m+1)
    for i in range(1, n+1):
        p[0] = i; j0 = 0
        minv = [INF]*(m+1); used = [False]*(m+1)
        while True:
            used[j0] = True
            i0 = p[j0]; delta = INF; j1 = -1
            for j in range(1, m+1):
                if not used[j]:
                    cur = a[i0][j] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur; way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]; j1 = j
            for j in range(0, m+1):
                if used[j]:
                    u[p[j]] += delta; v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0: break
        while True:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
            if j0 == 0: break
    return p

def solve(n, m, cards):
    """returns (best total, list of (customer, gift))"""
    w = [[0]*(m+1) for _ in range(n+1)]
    for i, j, pp in cards: w[i][j] = pp
    # hungarian minimises; pad to n<=m by transposing if needed
    transposed = False
    if n > m:
        w2 = [[0]*(n+1) for _ in range(m+1)]
        for i in range(1, n+1):
            for j in range(1, m+1): w2[j][i] = w[i][j]
        w = w2; n, m = m, n; transposed = True
    a = [[0]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1):
        for j in range(1, m+1): a[i][j] = -w[i][j]
    p = hungarian(a)
    total = 0; res = []
    for j in range(1, m+1):
        i = p[j]
        if i and w[i][j] > 0:
            total += w[i][j]
            res.append((j, i) if transposed else (i, j))
    return total, res

def brute(n, m, cards):
    w = [[0]*(m+1) for _ in range(n+1)]
    for i, j, pp in cards: w[i][j] = pp
    best = 0
    cols = list(range(1, m+1))
    for r in range(0, min(n, m)+1):
        for rows in permutations(range(1, n+1), r):
            for cs in permutations(cols, r):
                best = max(best, sum(w[rows[t]][cs[t]] for t in range(r)))
    return best

def main():
    tot, asg = solve(2, 3, [(1,1,2),(1,2,3),(1,3,5),(2,3,8)])
    print("sample:", tot, sorted(asg))
    assert tot == 11
    w = {(1,1):2,(1,2):3,(1,3):5,(2,3):8}
    assert sum(w[(i,j)] for i,j in asg) == 11
    assert len(set(i for i,_ in asg)) == len(asg) and len(set(j for _,j in asg)) == len(asg)
    print("sample OK")
    random.seed(4); bad = 0
    for _ in range(200):
        n = random.randint(1,4); m = random.randint(1,4)
        cards = []
        for i in range(1, n+1):
            for j in range(1, m+1):
                if random.random() < 0.6:
                    cards.append((i, j, random.randint(1, 20)))
        if not cards: continue
        f, asg = solve(n, m, cards)
        b = brute(n, m, cards)
        wd = {(i,j):p for i,j,p in cards}
        s = sum(wd[(i,j)] for i,j in asg)
        ok = (f == b == s and len(set(i for i,_ in asg)) == len(asg)
              and len(set(j for _,j in asg)) == len(asg))
        if not ok:
            bad += 1
            if bad < 5: print("MISMATCH", n, m, cards, f, b, asg)
    print("random small instances: mismatches =", bad)
    assert bad == 0
    print("engaging: OK")

main()
