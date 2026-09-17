"""Kattis convex (2015 ICPC Singapore, E).

Task: output any strictly convex lattice polygon with exactly N vertices
(3 <= N <= 400000), no three vertices collinear, all coordinates in [0, 4*10^7].

Solution under test: a convex polygon is exactly a cyclic sequence of edge vectors
with pairwise distinct directions summing to zero, sorted by angle.  Distinct
directions <=> no three vertices collinear, so take primitive vectors (gcd = 1).
To make the sum vanish for free, take antipodal PAIRS {v, -v}; for odd N start
from the triangle {(1,0),(0,1),(-1,-1)} (three primitive vectors summing to zero)
and add pairs for the rest.  Greedily take the pairs of smallest L1 norm, because
the polygon's width is exactly sum|a_i| and its height sum|b_i| over the chosen
half-plane representatives.  Sorting by angle gives the polygon; prefix sums give
the vertices.  O(N log N) time after a O(S^2) sieve of primitive vectors,
S = O(sqrt(N)); O(N) space.

This script IS the solution plus a full checker (lattice, in range, distinct,
strictly convex, no three collinear, exactly N vertices) run over many N.
"""
from math import gcd, atan2

BOX = 40_000_000

def pool(limit):
    """primitive vectors in the half plane (b>0) or (b==0 and a>0), by L1 norm."""
    out = []
    s = 1
    while len(out) < limit:
        # shell |a| + b == s
        for b in range(0, s + 1):
            a = s - b
            for aa in ((a,) if a == 0 else (a, -a)):
                if b == 0 and aa <= 0:
                    continue
                if gcd(abs(aa), b) == 1:
                    out.append((aa, b))
        s += 1
    return out

def build(n):
    if n % 2 == 0:
        base, need = [], n // 2
        banned = set()
    else:
        base = [(1, 0), (0, 1), (-1, -1)]
        need = (n - 3) // 2
        banned = {(1, 0), (0, 1), (1, 1)}
    picked, vecs = 0, list(base)
    for v in pool(need + len(banned) + 4):
        if picked == need:
            break
        if v in banned:
            continue
        vecs.append(v)
        vecs.append((-v[0], -v[1]))
        picked += 1
    assert picked == need and len(vecs) == n
    vecs.sort(key=lambda p: atan2(p[1], p[0]))
    pts, x, y = [], 0, 0
    for dx, dy in vecs:
        pts.append((x, y))
        x += dx
        y += dy
    assert (x, y) == (0, 0)
    mnx = min(p[0] for p in pts)
    mny = min(p[1] for p in pts)
    return [(p[0] - mnx, p[1] - mny) for p in pts]

def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

def check(n, pts):
    assert len(pts) == n, "vertex count"
    assert len(set(pts)) == n, "distinct"
    for x, y in pts:
        assert 0 <= x <= BOX and 0 <= y <= BOX, ("out of box", x, y)
    for i in range(n):
        c = cross(pts[i], pts[(i + 1) % n], pts[(i + 2) % n])
        assert c > 0, ("not strictly convex / three collinear at", i, c)
    return max(p[0] for p in pts), max(p[1] for p in pts)

def samples():
    for n in (3, 4):
        check(n, build(n))
    print("samples OK (N=3 and N=4 produce valid polygons)")

if __name__ == "__main__":
    samples()
    worst = 0
    for n in list(range(3, 60)) + [999, 1000, 65535, 65536, 399997, 399998, 399999, 400000]:
        mx, my = check(n, build(n))
        worst = max(worst, mx, my)
        if n > 1000:
            print("N=%7d  bounding box %d x %d  (limit %d)" % (n, mx, my, BOX))
    print("all N checked, worst coordinate used =", worst, "<=", BOX, ":", worst <= BOX)
    assert worst <= BOX
