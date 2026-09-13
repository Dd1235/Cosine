"""Carl's Vacation -- Kattis `carlsvacation`, ICPC World Finals 2022 & 2023 (Luxor).

Two right square pyramids stand on the plane z = 0 (their bases overlap in zero
area).  Carl walks only on the two lateral surfaces and on the ground; find the
shortest walk between the two apexes.

------------------------------------------------------------------ derivation --
Let a pyramid have base side s, height h, base centre c, apex a3 = (c, h).

(1) For ANY point U on the base boundary the surface distance apex -> U is the
    straight 3-D distance  r(U) = |a3 - U| = sqrt(h^2 + |c - U|^2).
    U and the apex lie on one lateral triangle, which is planar and convex, so
    the 3-D segment between them stays inside that face -- it is a legal path,
    and no path can beat the straight 3-D distance.  (Equivalently: the lateral
    surface is a cone and every geodesic out of the cone point is radial, so a
    geodesic leaving the apex never crosses a lateral edge.)

(2) Unfolding that one face about its base edge e makes the surface distance
    planar.  Rotating the face down about e lays it flat pointing INWARD -- the
    walkable angle across the base edge is 180 - (face elevation), a convex
    ridge, so flattening carries the face across the edge onto the ground's far
    side.  With m = midpoint(e), n = OUTWARD unit normal of e and
    slant = sqrt(h^2 + (s/2)^2), the image is
            A' = m - slant * n
    (check h -> 0: slant -> s/2 and A' -> the base centre, as it must).  Then
            |A' - U| = sqrt(slant^2 + t^2) = sqrt(h^2 + (s/2)^2 + t^2) = r(U)
    for U at distance t from m along e.  Note m + slant*n gives the SAME
    distances (it is the mirror image of A' in the line e, and U lies on that
    line) but the wrong geometry: with the outward image the unfolded path
    bounces off e instead of crossing it, which breaks every crossing test.

(3) The answer is
        min over U in dBase1, V in dBase2 of  r1(U) + |U - V| + r2(V),      (*)
    using the STRAIGHT ground distance with no obstacle test.
    Lower bound: a real walk has a last point U on dBase1 and a first point V
    after it on dBase2, and its three pieces cost at least r1(U), |U-V|, r2(V).
    Upper bound: the minimiser of (*) can be taken unobstructed.  r is
    1-Lipschitz in ground distance (r(U) = sqrt(h^2+|c-U|^2) is 1-Lipschitz in
    |c-U|, which is 1-Lipschitz in U), so if UV cuts through base1 and leaves it
    at W then r1(W) + |WV| <= r1(U) + |UW| + |WV| = r1(U) + |UV|; the bases are
    convex, so repeating once for base2 clears the segment for good.

(4) Fixing one base edge of each pyramid, (*) becomes
        min_{U in e1, V in e2}  |A' - U| + |U - V| + |V - B'|,
    jointly convex on a product of two segments (a sum of norms of affine maps),
    so it has a closed form: if the segment A'B' meets e1 and then e2 the answer
    is |A'B'| (one straight unfolded line); otherwise an endpoint is optimal for
    one of them -- a base CORNER, where r equals the lateral edge
    sqrt(h^2 + s^2/2) -- and the other is the classic reflect-and-clamp
    point-segment-point minimisation.  16 edge pairs, O(1) overall.
    (Nested ternary search on the same convex objective is the usual
    contest-time substitute for the case analysis; both are implemented here.)

This file checks the answer against
  (a) the provided sample,
  (b) the closed form vs nested ternary search -- two independent minimisers,
  (c) fact (1), by Dijkstra on a fine triangulated mesh of ONE pyramid,
  (d) a dense-sampling brute force whose ground leg is a real VISIBILITY-GRAPH
      shortest path around both square obstacles, i.e. it does not assume the
      "straight ground segment" claim of (3),
  (e) a 3-D Dijkstra over a mesh of the entire surface (both pyramids plus the
      ground) that assumes neither (1) nor (3): an edge exists only between
      nodes whose connecting segment provably lies on the surface,
  (f) the inward/outward unfolding claim of (2).
"""
import math, random, heapq

EPS = 1e-9

# --------------------------------------------------------------- 2-D helpers --
def sub(a, b):   return (a[0]-b[0], a[1]-b[1])
def add(a, b):   return (a[0]+b[0], a[1]+b[1])
def mul(a, t):   return (a[0]*t, a[1]*t)
def dot(a, b):   return a[0]*b[0] + a[1]*b[1]
def cross(a, b): return a[0]*b[1] - a[1]*b[0]
def norm(a):     return math.hypot(a[0], a[1])
def dist(a, b):  return math.hypot(a[0]-b[0], a[1]-b[1])
def lerp(a, b, t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)


class Pyr:
    """Right square pyramid given one directed base edge (body on the LEFT)."""
    def __init__(self, x1, y1, x2, y2, h):
        d = (x2-x1, y2-y1)
        s = norm(d)
        n = (-d[1], d[0])                        # left normal, length s
        p1, p2 = (x1, y1), (x2, y2)
        p3, p4 = add(p2, n), add(p1, n)
        self.corners = [p1, p2, p3, p4]          # counter-clockwise
        self.s, self.h = s, float(h)
        self.center = (sum(c[0] for c in self.corners)/4.0,
                       sum(c[1] for c in self.corners)/4.0)
        self.apex3 = (self.center[0], self.center[1], float(h))
        self.slant = math.hypot(h, s/2.0)        # apex -> base-edge midpoint
        self.lat = math.sqrt(h*h + s*s/2.0)      # apex -> base corner
        self.edges, self.images, self.wrong_images = [], [], []
        for i in range(4):
            a, b = self.corners[i], self.corners[(i+1) % 4]
            m = mul(add(a, b), 0.5)
            out = mul(sub(m, self.center), 1.0/norm(sub(m, self.center)))
            self.edges.append((a, b))
            self.images.append(add(m, mul(out, -self.slant)))       # INWARD
            self.wrong_images.append(add(m, mul(out, self.slant)))  # outward

    def radial(self, u):
        """True surface distance apex -> u, for u on the base boundary."""
        return math.sqrt(self.h*self.h + dist(self.center, u)**2)


def inside_poly(poly, p, eps=EPS):
    return all(cross(sub(poly[(i+1) % len(poly)], poly[i]), sub(p, poly[i])) > eps
               for i in range(len(poly)))


def seg_cuts_poly(u, v, poly, eps=1e-7):
    """Does segment uv overlap the OPEN interior of the convex CCW polygon in
    positive length?  Clip t in [0,1] against  cross(e, u + t*d - a) > 0."""
    t0, t1 = 0.0, 1.0
    d = sub(v, u)
    for i in range(len(poly)):
        a = poly[i]
        e = sub(poly[(i+1) % len(poly)], a)
        c0 = cross(e, sub(u, a))       # value at t = 0
        k = cross(e, d)                # slope in t;  need c0 + t*k > 0
        if abs(k) < 1e-18:
            if c0 <= 0:
                return False
            continue
        t = -c0/k
        if k > 0: t0 = max(t0, t)
        else:     t1 = min(t1, t)
        if t0 >= t1:
            return False
    return (t1 - t0)*norm(d) > eps


# ----------------------------------------------------- intended O(1) solution --
def point_seg_point(c, B, b1, b2):
    """min over V on segment [b1,b2] of |c-V| + |V-B|  (reflect and clamp)."""
    d = sub(b2, b1); L = norm(d)
    if L < 1e-15:
        return dist(c, b1) + dist(b1, B)
    u = mul(d, 1.0/L)
    nr = (-u[1], u[0])
    sc, sB = dot(sub(c, b1), nr), dot(sub(B, b1), nr)
    pc, pB = dot(sub(c, b1), u),  dot(sub(B, b1), u)
    den = abs(sc) + abs(sB)            # same expression for "crosses the line"
    t = pc if den < 1e-15 else pc + (pB - pc)*abs(sc)/den   # and for "reflect"
    t = min(max(t, 0.0), L)            # convex in t, so clamping is optimal
    V = add(b1, mul(u, t))
    return dist(c, V) + dist(V, B)


def seg_param_hit(P, Q, a, b):
    """Parameter along PQ where it meets segment ab, or None."""
    d1, d2 = sub(Q, P), sub(b, a)
    den = cross(d1, d2)
    if abs(den) < 1e-15:
        return None
    t = cross(sub(a, P), d2)/den
    s = cross(sub(a, P), d1)/den
    return t if (-1e-12 <= t <= 1+1e-12 and -1e-12 <= s <= 1+1e-12) else None


def pair_closed(A, e1, B, e2):
    """min_{U in e1, V in e2} |A-U| + |U-V| + |V-B|, closed form."""
    a1, a2 = e1; b1, b2 = e2
    t1 = seg_param_hit(A, B, a1, a2)
    t2 = seg_param_hit(A, B, b1, b2)
    if t1 is not None and t2 is not None and t1 <= t2 + 1e-12:
        return dist(A, B)
    best = float('inf')
    for U in (a1, a2):                 # U pinned at a base corner of pyramid 1
        best = min(best, dist(A, U) + point_seg_point(U, B, b1, b2))
    for V in (b1, b2):                 # V pinned at a base corner of pyramid 2
        best = min(best, dist(V, B) + point_seg_point(V, A, a1, a2))
    return best


def pair_ternary(A, e1, B, e2, iters=90):
    """Same objective by nested ternary search (it is jointly convex)."""
    a1, a2 = e1; b1, b2 = e2
    def inner(u):
        lo, hi = 0.0, 1.0
        for _ in range(iters):
            m1, m2 = lo + (hi-lo)/3.0, hi - (hi-lo)/3.0
            v1, v2 = lerp(b1, b2, m1), lerp(b1, b2, m2)
            if dist(u, v1)+dist(v1, B) < dist(u, v2)+dist(v2, B): hi = m2
            else: lo = m1
        v = lerp(b1, b2, (lo+hi)/2.0)
        return dist(u, v) + dist(v, B)
    lo, hi = 0.0, 1.0
    for _ in range(iters):
        m1, m2 = lo + (hi-lo)/3.0, hi - (hi-lo)/3.0
        if dist(A, lerp(a1, a2, m1)) + inner(lerp(a1, a2, m1)) < \
           dist(A, lerp(a1, a2, m2)) + inner(lerp(a1, a2, m2)): hi = m2
        else: lo = m1
    u = lerp(a1, a2, (lo+hi)/2.0)
    return dist(A, u) + inner(u)


def solve(p, q, pair=pair_closed, attr='images'):
    return min(pair(getattr(p, attr)[i], p.edges[i], getattr(q, attr)[j], q.edges[j])
               for i in range(4) for j in range(4))


# ------------------------- cross-check (d): visibility-graph ground distance --
def ground_sp(u, v, polys):
    """Shortest ground path u -> v avoiding the interiors of the convex polys.
    Convex obstacles, so an optimal path bends only at obstacle vertices."""
    nodes = [u, v] + [c for poly in polys for c in poly]
    n = len(nodes)
    INF = float('inf')
    d = [INF]*n; d[0] = 0.0
    seen = [False]*n
    pq = [(0.0, 0)]
    while pq:
        du, i = heapq.heappop(pq)
        if seen[i]: continue
        seen[i] = True
        if i == 1: return du
        for j in range(n):
            if seen[j] or j == i: continue
            if any(seg_cuts_poly(nodes[i], nodes[j], poly) for poly in polys):
                continue
            nd = du + dist(nodes[i], nodes[j])
            if nd < d[j] - 1e-12:
                d[j] = nd; heapq.heappush(pq, (nd, j))
    return d[1]


def brute_boundary(p, q, n=90):
    """Sample both base boundaries and use the TRUE obstacle-avoiding ground
    path.  An upper bound converging from above as n grows."""
    def samples(py):
        out = []
        for i in range(4):
            a, b = py.edges[i]
            for k in range(n):
                u = lerp(a, b, k/float(n))
                out.append((u, py.radial(u)))
        return out
    us, vs = samples(p), samples(q)
    best = float('inf')
    for (u, du) in us:
        if du >= best: continue
        for (v, dv) in vs:
            if du + dist(u, v) + dv >= best: continue
            best = min(best, du + ground_sp(u, v, [p.corners, q.corners]) + dv)
    return best


# ------------------ cross-check (c)/(e): Dijkstra on a real 3-D surface mesh --
def _face_lattice(py, res, tag):
    """3-D lattice on the four lateral faces; points shared by adjacent faces
    (the lateral edges) collapse to one node so paths may cross them."""
    pts = {}
    ap = py.apex3
    for i in range(4):
        a, b = py.edges[i]
        for r in range(res+1):
            t = r/float(res)
            for c in range(r+1):
                w = 0.0 if r == 0 else c/float(r)
                bx, by = lerp(a, b, w)
                pt = (ap[0]+(bx-ap[0])*t, ap[1]+(by-ap[1])*t, ap[2]*(1.0-t))
                key = (round(pt[0], 7), round(pt[1], 7), round(pt[2], 7))
                pts.setdefault(key, [pt, set()])[1].add((tag, i))
    return pts


def surface_dijkstra(pyrs, src3, dst3, res=14, gres=0, ground_box=None):
    """Dijkstra on a mesh of the lateral surfaces (plus an optional ground grid).
    An edge exists only when the straight segment demonstrably lies ON the
    surface: both ends on one planar convex lateral face, or both on the ground
    with the segment clear of every base.  So the result is a genuine UPPER
    bound on the true geodesic, converging from above."""
    nodes, faces, index = [], [], {}
    for tag, py in enumerate(pyrs):
        for key, (pt, fs) in _face_lattice(py, res, tag).items():
            if key in index:
                faces[index[key]] |= fs
            else:
                index[key] = len(nodes); nodes.append(pt); faces.append(set(fs))
    if gres:
        x0, y0, x1, y1 = ground_box
        for i in range(gres+1):
            for j in range(gres+1):
                x = x0 + (x1-x0)*i/gres; y = y0 + (y1-y0)*j/gres
                if any(inside_poly(py.corners, (x, y)) for py in pyrs): continue
                key = (round(x, 7), round(y, 7), 0.0)
                if key not in index:
                    index[key] = len(nodes); nodes.append((x, y, 0.0)); faces.append(set())
        for k in range(len(nodes)):            # every z == 0 node is on the ground
            if abs(nodes[k][2]) < 1e-12: faces[k].add('G')
    N = len(nodes)
    polys = [py.corners for py in pyrs]
    def ok(i, j):
        if (faces[i] & faces[j]) - {'G'}:
            return True                        # one planar convex lateral face
        if 'G' in faces[i] and 'G' in faces[j]:
            u = (nodes[i][0], nodes[i][1]); v = (nodes[j][0], nodes[j][1])
            return not any(seg_cuts_poly(u, v, poly) for poly in polys)
        return False
    span = max(max(abs(n[k]) for n in nodes) for k in range(3))
    R = 3.0*span/float(max(res, gres or res))
    adj = [[] for _ in range(N)]
    for i in range(N):
        xi, yi, zi = nodes[i]
        for j in range(i+1, N):
            dx, dy, dz = xi-nodes[j][0], yi-nodes[j][1], zi-nodes[j][2]
            w = math.sqrt(dx*dx+dy*dy+dz*dz)
            if w <= R and ok(i, j):
                adj[i].append((j, w)); adj[j].append((i, w))
    def near(p3):
        return min(range(N), key=lambda k: (nodes[k][0]-p3[0])**2 +
                   (nodes[k][1]-p3[1])**2 + (nodes[k][2]-p3[2])**2)
    s, t = near(src3), near(dst3)
    INF = float('inf'); d = [INF]*N; d[s] = 0.0
    pq = [(0.0, s)]
    while pq:
        du, u = heapq.heappop(pq)
        if du > d[u] + 1e-15: continue
        if u == t: return du
        for v, w in adj[u]:
            if du + w < d[v] - 1e-12:
                d[v] = du + w; heapq.heappush(pq, (du+w, v))
    return d[t]


# --------------------------------------------------------------------- tests --
def sat_disjoint(A, B):
    for poly in (A, B):
        for i in range(len(poly)):
            a, b = poly[i], poly[(i+1) % len(poly)]
            ax = (-(b[1]-a[1]), b[0]-a[0])
            pa = [dot(ax, c) for c in A]; pb = [dot(ax, c) for c in B]
            if max(pa) <= min(pb)+1e-9 or max(pb) <= min(pa)+1e-9:
                return True
    return False


def random_pair(rng, lim=9, hmax=9, side=7):
    while True:
        def mk():
            x1, y1 = rng.randint(-lim, lim), rng.randint(-lim, lim)
            while True:
                dx, dy = rng.randint(-side, side), rng.randint(-side, side)
                if (dx, dy) != (0, 0): break
            return Pyr(x1, y1, x1+dx, y1+dy, rng.randint(1, hmax))
        a, b = mk(), mk()
        if sat_disjoint(a.corners, b.corners):
            return a, b


def main():
    ok = True

    # (a) the sample ---------------------------------------------------------
    p, q = Pyr(0, 0, 10, 0, 4), Pyr(9, 18, 34, 26, 42)
    got = solve(p, q)
    good = abs(got - 60.866649532) < 1e-6
    ok &= good
    print('(a) sample        expected 60.866649532  got %.9f  %s'
          % (got, 'OK' if good else 'FAIL'))

    # (b) closed form vs nested ternary search -------------------------------
    rng = random.Random(20220000)
    worst = 0.0
    for _ in range(400):
        a, b = random_pair(rng)
        worst = max(worst, abs(solve(a, b) - solve(a, b, pair_ternary)))
    good = worst < 1e-7
    ok &= good
    print('(b) closed form vs nested ternary search, 400 random pairs: '
          'max abs diff %.2e  %s' % (worst, 'OK' if good else 'FAIL'))

    # (f) the unfolding direction of fact (2) --------------------------------
    rng = random.Random(11)
    same_val, wrong_closed = 0.0, 0.0
    for _ in range(200):
        a, b = random_pair(rng)
        ref = solve(a, b, pair_ternary)
        same_val = max(same_val, abs(solve(a, b, pair_ternary, 'wrong_images') - ref))
        wrong_closed = max(wrong_closed, abs(solve(a, b, pair_closed, 'wrong_images') - ref))
    good = same_val < 1e-7 and wrong_closed > 1e-2
    ok &= good
    print('(f) outward image: same objective value (max diff %.1e) but breaks the'
          '\n    crossing test (closed form off by up to %.3f)  %s'
          % (same_val, wrong_closed, 'OK' if good else 'FAIL'))

    # (c) fact (1): apex -> base point is the straight 3-D distance ----------
    print('(c) apex->base-point geodesic vs sqrt(h^2+|c-U|^2), mesh Dijkstra on'
          ' one pyramid:')
    for (spec, target) in [((0, 0, 6, 0, 2), 'far corner'),
                           ((0, 0, 4, 0, 9), 'far corner'),
                           ((0, 0, 5, 0, 1), 'far edge midpoint'),
                           ((0, 0, 3, 0, 8), 'far edge midpoint')]:
        py = Pyr(*spec)
        u = py.corners[2] if target == 'far corner' else \
            mul(add(py.corners[2], py.corners[3]), 0.5)
        claim = py.radial(u)
        mesh = surface_dijkstra([py], py.apex3, (u[0], u[1], 0.0), res=30)
        rel = (mesh - claim)/claim
        good = -1e-9 < rel < 8e-3
        ok &= good
        print('     s=%.0f h=%.0f %-18s claim %.6f  mesh %.6f  (%+.3f%%)  %s'
              % (py.s, py.h, target, claim, mesh, 100*rel, 'OK' if good else 'FAIL'))

    # (d) vs boundary sampling + visibility-graph ground path -----------------
    rng = random.Random(7)
    bad, worst = 0, 0.0
    for _ in range(60):
        a, b = random_pair(rng, lim=7, hmax=7)
        x, y = solve(a, b), brute_boundary(a, b, n=90)
        if x > y + 1e-9:
            bad += 1
            print('     OVER-ESTIMATE', a.corners, a.h, b.corners, b.h, x, y)
        worst = max(worst, (y - x)/max(1.0, x))
    good = bad == 0 and worst < 3e-3
    ok &= good
    print('(d) vs boundary sampling + visibility-graph ground path, 60 pairs: '
          '%d over-estimates,\n    max gap %.2e (sampling error)  %s'
          % (bad, worst, 'OK' if good else 'FAIL'))

    # (e) whole-surface 3-D mesh Dijkstra ------------------------------------
    print('(e) whole-surface mesh Dijkstra (coarse upper bound, assumes nothing):')
    for spec in [((0, 0, 4, 0, 3), (6, 1, 10, 1, 5)),
                 ((0, 0, 6, 0, 2), (0, 7, 5, 7, 6)),
                 ((0, 0, 5, 0, 7), (-1, 9, 4, 9, 2)),
                 ((0, 0, 5, 0, 2), (5, 0, 10, 0, 3)),
                 ((0, 0, 6, 0, 1), (7, -1, 11, -1, 9))]:
        A, B = Pyr(*spec[0]), Pyr(*spec[1])
        xs = [c[0] for c in A.corners+B.corners]
        ys = [c[1] for c in A.corners+B.corners]
        pad = 0.3*max(max(xs)-min(xs), max(ys)-min(ys))
        box = (min(xs)-pad, min(ys)-pad, max(xs)+pad, max(ys)+pad)
        ex = solve(A, B)
        mm = surface_dijkstra([A, B], A.apex3, B.apex3, res=12, gres=26, ground_box=box)
        rel = (mm - ex)/ex
        good = -1e-9 < rel < 0.04
        ok &= good
        print('     exact %.6f   mesh upper bound %.6f  (%+.2f%%)  %s'
              % (ex, mm, 100*rel, 'OK' if good else 'FAIL'))

    print('\nALL CHECKS PASSED' if ok else '\nSOME CHECKS FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
