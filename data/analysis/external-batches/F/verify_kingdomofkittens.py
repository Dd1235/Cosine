"""Kingdom of Kittens - NOT SOLVED.  This script records the reduction that was
established, and checks it against a direct (exact-rational) search over
candidate triangles on small point sets.

Established here:
  (1) every input point must lie on the boundary of the convex hull - a point
      strictly inside the hull is strictly inside any triangle containing it;
  (2) each side line of such a triangle is a supporting line of the hull, so it
      meets the hull in a face (one vertex or one whole edge) or misses it;
      consequently the points it can cover are exactly that face;
  (3) therefore the hull can have at most 6 vertices (three faces cover at most
      six vertices), and every hull edge carrying a point in its interior must
      itself be one of the three chosen faces;
  (4) once three supporting half-planes are chosen, containment inside the
      *sides* is automatic; the triangle is non-degenerate exactly when the
      three outward normals are not inside a closed half-plane, which is the
      three consecutive-gap-below-pi test.
What is missing: step (4) leaves a feasibility question over arcs, because a
face that is a vertex offers a whole cone of normals rather than one direction
(the sample square needs a strictly interior direction there), and the finite
exact test for 'do three normal arcs admit a positively spanning triple' was
not finished.  So no labels are claimed.
"""
import itertools
import random
from fractions import Fraction


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def hull(pts):
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


def on_seg(p, a, b):
    if cross(a, b, p) != 0:
        return False
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def on_hull_boundary(pts):
    h = hull(pts)
    if len(h) <= 2:
        return True
    return all(any(on_seg(p, h[i], h[(i + 1) % len(h)]) for i in range(len(h)))
               for p in pts)


# ---------------------------------------------------------------- brute force
def line_through(p, d):
    """ax + by = c through p with direction d"""
    return (-d[1], d[0], -d[1] * p[0] + d[0] * p[1])


def inter(l1, l2):
    a1, b1, c1 = l1
    a2, b2, c2 = l2
    det = a1 * b2 - a2 * b1
    if det == 0:
        return None
    return (Fraction(c1 * b2 - c2 * b1, det), Fraction(a1 * c2 - a2 * c1, det))


def on_segment_f(p, a, b):
    cr = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if cr != 0:
        return False
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def brute_yes(pts):
    """Search a rich candidate set of triangles; sound (never a false YES)."""
    P = sorted(set(pts))
    dirs = set()
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if (dx, dy) != (0, 0):
                g = abs(dx)
                from math import gcd
                g = gcd(abs(dx), abs(dy))
                dirs.add((dx // g, dy // g))
    lines = set()
    for p in P:
        for d in dirs:
            lines.add(line_through(p, d))
    # 'free' supporting lines pushed just outside the point set
    for d in dirs:
        a, b = -d[1], d[0]
        vals = [a * q[0] + b * q[1] for q in P]
        lines.add((a, b, max(vals) + 1))
        lines.add((a, b, min(vals) - 1))
    lines = list(lines)
    for tri in itertools.combinations(lines, 3):
        v = []
        ok = True
        for i in range(3):
            q = inter(tri[i], tri[(i + 1) % 3])
            if q is None:
                ok = False
                break
            v.append(q)
        if not ok:
            continue
        area = ((v[1][0] - v[0][0]) * (v[2][1] - v[0][1])
                - (v[1][1] - v[0][1]) * (v[2][0] - v[0][0]))
        if area == 0:
            continue
        if all(any(on_segment_f(p, v[i], v[(i + 1) % 3]) for i in range(3)) for p in P):
            return True, tri
    return False, None


def main():
    sq = [(0, 0), (0, 2), (2, 0), (2, 2)]
    sqc = sq + [(1, 1)]
    got, tri = brute_yes(sq)
    assert got, "sample 1 should be YES"
    got2, _ = brute_yes(sqc)
    assert not got2, "sample 2 should be NO"
    print("both samples reproduced by the direct triangle search")
    print("  square witness lines:", tri)

    random.seed(12)
    checked = 0
    for _ in range(120):
        n = random.randint(1, 7)
        pts = list(set((random.randint(0, 4), random.randint(0, 4)) for _ in range(n)))
        yes, _ = brute_yes(pts)
        if yes:
            assert on_hull_boundary(pts), pts        # necessary condition (1)
            h = hull(pts)
            assert len(h) <= 6, (pts, h)             # necessary condition (3)
            checked += 1
    print("%d random YES instances all satisfy 'every point on the hull "
          "boundary' and 'hull has at most 6 vertices'" % checked)

    # (1) is also sufficient to rule out: any point strictly inside is fatal
    bad = 0
    for _ in range(120):
        pts = list(set((random.randint(0, 5), random.randint(0, 5)) for _ in range(random.randint(4, 8))))
        if not on_hull_boundary(pts):
            yes, _ = brute_yes(pts)
            assert not yes, pts
            bad += 1
    print("%d instances with an interior point are all NO, as the reduction "
          "predicts" % bad)
    print("UNSOLVED: the arc-feasibility step (4) is not implemented.")


main()
