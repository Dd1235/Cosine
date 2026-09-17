"""Kingdom of Kittens -- verification.

Solution under test (solve):
  * a point strictly inside the convex hull can never lie on a side of a
    triangle that contains the hull, so every point must lie on the hull
    boundary;
  * every side line of such a triangle supports the hull, so the points it can
    carry are exactly one face of the hull (one vertex or one whole edge).
    Three faces cover at most six hull vertices, hence the hull has at most six
    vertices, and every hull edge carrying a point in its interior must itself
    be one of the three chosen faces;
  * a side line may be pushed inwards until it supports the hull without losing
    anything, so the outward normal of the side that carries face F may be any
    direction of F's normal cone: a single direction for an edge, the closed arc
    between the two adjacent edge normals for a vertex;
  * containment is then automatic and the only remaining question is whether the
    three half planes are bounded, i.e. whether directions d1, d2, d3 can be
    picked from the three (disjoint, cyclically ordered) arcs with all three
    ccw gaps below pi.  Eliminating d2, then d3, then d1 from
        0 < t2-t1 < pi,  0 < t3-t2 < pi,  0 < t1+2pi-t3 < pi
    over the boxes [a_i, b_i] leaves exactly three conditions:  the ccw gap
    from the END of each arc to the START of the next is below pi.  All three
    are integer cross/dot tests on the hull edge normals.

Cross-checked against brute(), which shares none of that reasoning: it uses
only the fact that every side line may be pushed in until it supports the point
set, enumerates candidate outward normals (the normals of every pair of points,
their negations, and one strictly interior direction per elementary arc of that
arrangement -- the arrangement in which every constraint of the problem is
piecewise constant), and accepts a triple whose three supporting lines cover all
points and whose directions positively span the plane.
"""
import functools
import random
import time
from math import gcd


# --------------------------------------------------------------- solution
def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(pts):
    """strict ccw hull: collinear boundary points are not kept as vertices"""
    p = sorted(set(pts))
    if len(p) <= 2:
        return p
    lo = []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    up = []
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def gap_lt_pi(u, v):
    """is the ccw gap from direction u to direction v in [0, pi)?"""
    cr = u[0] * v[1] - u[1] * v[0]
    if cr > 0:
        return True
    if cr < 0:
        return False
    return u[0] * v[0] + u[1] * v[1] > 0        # gap 0 yes, gap pi no


def on_seg_interior(p, a, b):
    if cross(a, b, p) != 0 or p == a or p == b:
        return False
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def solve(points):
    P = list(set(points))
    h = convex_hull(P)
    if len(h) <= 2:
        return True                      # one point or a segment always fits
    k = len(h)
    if k > 6:
        return False                     # three faces cover at most six vertices
    hs = set(h)
    heavy = [False] * k                  # edges carrying a point in their interior
    for p in P:
        if p in hs:
            continue
        for i in range(k):
            if on_seg_interior(p, h[i], h[(i + 1) % k]):
                heavy[i] = True
                break
        else:
            return False                 # strictly inside the hull
    nrm = []
    for i in range(k):
        dx = h[(i + 1) % k][0] - h[i][0]
        dy = h[(i + 1) % k][1] - h[i][1]
        nrm.append((dy, -dx))            # outward: hull is ccw
    faces = []                           # ccw order of the normal fan
    for i in range(k):
        faces.append(('E', i, nrm[i], nrm[i]))
        faces.append(('V', (i + 1) % k, nrm[i], nrm[(i + 1) % k]))
    F = len(faces)
    for i in range(F):
        for j in range(i + 1, F):
            for l in range(j + 1, F):
                tri = (faces[i], faces[j], faces[l])
                ce = set(f[1] for f in tri if f[0] == 'E')
                cv = set(f[1] for f in tri if f[0] == 'V')
                if any(heavy[e] and e not in ce for e in range(k)):
                    continue
                if any(v not in cv and v not in ce and (v - 1) % k not in ce
                       for v in range(k)):
                    continue
                if (gap_lt_pi(tri[0][3], tri[1][2])
                        and gap_lt_pi(tri[1][3], tri[2][2])
                        and gap_lt_pi(tri[2][3], tri[0][2])):
                    return True
    return False


# --------------------------------------------------------------- brute force
def _prim(d):
    g = gcd(abs(d[0]), abs(d[1]))
    return (d[0] // g, d[1] // g)


def _sort_dirs(ds):
    def half(d):
        return 0 if (d[1] > 0 or (d[1] == 0 and d[0] > 0)) else 1

    def cmp(a, b):
        if half(a) != half(b):
            return -1 if half(a) < half(b) else 1
        cr = a[0] * b[1] - a[1] * b[0]
        return -1 if cr > 0 else (1 if cr < 0 else 0)
    return sorted(ds, key=functools.cmp_to_key(cmp))


def _candidates(P):
    ds = set()
    for a in P:
        for b in P:
            if a != b:
                dx, dy = b[0] - a[0], b[1] - a[1]
                ds.add(_prim((dy, -dx)))
                ds.add(_prim((-dy, dx)))
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1),
              (1, 1), (1, -1), (-1, 1), (-1, -1)):
        ds.add(d)
    base = _sort_dirs(ds)
    out = list(base)
    for i in range(len(base)):
        a, b = base[i], base[(i + 1) % len(base)]
        if a[0] * b[1] - a[1] * b[0] != 0:
            out.append((a[0] + b[0], a[1] + b[1]))
    return out


def _spans(d1, d2, d3):
    ds = _sort_dirs([d1, d2, d3])
    for i in range(3):
        u, v = ds[i], ds[(i + 1) % 3]
        if u[0] * v[1] - u[1] * v[0] <= 0:
            return False
    return True


def brute(points):
    P = list(set(points))
    n = len(P)
    if n <= 2:
        return True
    full = (1 << n) - 1
    seen = set()
    uniq = []
    for d in _candidates(P):
        if d in seen:
            continue
        seen.add(d)
        vals = [d[0] * p[0] + d[1] * p[1] for p in P]
        mx = max(vals)
        mask = 0
        for i, v in enumerate(vals):
            if v == mx:
                mask |= 1 << i
        uniq.append((d, mask))
    L = len(uniq)
    for i in range(L):
        di, mi = uniq[i]
        for j in range(i + 1, L):
            dj, mij = uniq[j][0], mi | uniq[j][1]
            for l in range(j + 1, L):
                dl, ml = uniq[l]
                if mij | ml == full and _spans(di, dj, dl):
                    return True
    return False


# --------------------------------------------------------------- driver
def boundary_points(h):
    out = []
    for i in range(len(h)):
        a, b = h[i], h[(i + 1) % len(h)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        g = gcd(abs(dx), abs(dy))
        for t in range(g):
            out.append((a[0] + dx * t // g, a[1] + dy * t // g))
    return out


def main():
    t0 = time.time()
    sq = [(0, 0), (0, 2), (2, 0), (2, 2)]
    assert solve(sq) is True and brute(sq) is True
    assert solve(sq + [(1, 1)]) is False and brute(sq + [(1, 1)]) is False
    print("both samples reproduced (square YES, square plus its centre NO)")

    rng = random.Random(2024)
    stats = {True: 0, False: 0}
    hullsize = {}
    cases = 0
    for it in range(4000):
        m = it % 4
        if m == 0:
            R = rng.choice([2, 3, 4, 6, 8])
            pts = [(rng.randint(0, R), rng.randint(0, R))
                   for _ in range(rng.randint(1, 7))]
        elif m == 1:
            R = rng.choice([4, 6, 8, 10])
            base = [(rng.randint(0, R), rng.randint(0, R))
                    for _ in range(rng.randint(3, 9))]
            h = convex_hull(base)
            if len(h) < 3:
                continue
            pts = [p for p in boundary_points(h)
                   if p in set(h) or rng.random() < 0.6]
            if rng.random() < 0.4:
                pts = [p for p in pts if rng.random() < 0.8]
        elif m == 2:
            a = (rng.randint(-3, 3), rng.randint(-3, 3))
            d = (rng.randint(-2, 2), rng.randint(-2, 2))
            pts = [(a[0] + d[0] * t, a[1] + d[1] * t)
                   for t in range(rng.randint(1, 5))]
            if rng.random() < 0.5:
                pts.append((rng.randint(-3, 3), rng.randint(-3, 3)))
        else:
            x1, x2 = sorted(rng.sample(range(0, 6), 2))
            y1, y2 = sorted(rng.sample(range(0, 6), 2))
            pts = [(x1, y1), (x1, y2), (x2, y1), (x2, y2)]
            for _ in range(rng.randint(0, 3)):
                pts.append(rng.choice([
                    (rng.randint(x1, x2), rng.choice([y1, y2])),
                    (rng.choice([x1, x2]), rng.randint(y1, y2)),
                    (rng.randint(x1, x2), rng.randint(y1, y2))]))
        if not pts:
            continue
        cases += 1
        a, b = solve(pts), brute(pts)
        assert a == b, ("MISMATCH", sorted(set(pts)), a, b)
        stats[b] += 1
        hullsize[len(convex_hull(list(set(pts))))] = \
            hullsize.get(len(convex_hull(list(set(pts)))), 0) + 1
    print("%d random point sets: solution and brute force agree everywhere "
          "(%d YES / %d NO)" % (cases, stats[True], stats[False]))
    print("hull sizes covered: %s" % sorted(hullsize.items()))

    # the square needs a side whose normal is strictly inside a vertex cone
    assert solve([(0, 0), (0, 2), (2, 0), (2, 2)]) is True
    # three sides of a square are two parallel lines plus one: unbounded
    assert gap_lt_pi((0, -1), (1, 0)) and gap_lt_pi((1, 0), (0, 1)) \
        and not gap_lt_pi((0, 1), (0, -1))
    # a seventh hull vertex can never be covered
    hept = [(0, 0), (4, 0), (6, 2), (6, 5), (4, 7), (1, 7), (-1, 4)]
    assert len(convex_hull(hept)) == 7 and solve(hept) is False
    print("hand cases: square YES, three-sides-of-a-square unbounded, "
          "7-gon NO  (%.1fs)" % (time.time() - t0))
    print("PASS")


main()
