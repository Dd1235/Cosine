"""Carl's Vacation (Kattis carlsvacation, ICPC WF 2022/2023).

Two right square pyramids on the plane z=0.  Shortest path on the union of the
two lateral surfaces and the ground between the two apexes.

Key facts used:
  * A geodesic leaving the apex crosses exactly ONE lateral face (unfolding two
    adjacent faces about their shared lateral edge gives a wedge whose two
    halves both have the apex as a vertex; a straight ray from that vertex
    cannot cross the dividing ray).  So the path descends one face, crosses that
    face's base edge at some point U, walks the ground, and climbs one face of
    the other pyramid.
  * Unfolding that face about its base edge puts the apex at the planar point
    A' = midpoint(e) + slant * outward_normal(e), slant = sqrt(h^2+(s/2)^2),
    and the surface distance apex->U equals |A'-U| exactly, for every U on e.
  * Hence the answer is  min over (e_i of P1, e_j of P2) of
        min_{U in e_i, V in e_j} |A_i'-U| + |U-V| + |V-B_j'|,
    a CONVEX program on a product of two segments (solved here by nested
    ternary search; the classic closed form is "straight line A'B' if it
    crosses both edges, else route through a base corner", and at a corner
    |A'-corner| = lateral edge length sqrt(h^2+s^2/2)).
  * Walking around a base is never needed: if a path reaches a base corner c of
    pyramid k, the surface geodesic apex_k->c is the lateral edge and is no
    longer, so corner routing dominates any detour.

This file checks the closed-form/convex answer against
  (a) the provided sample,
  (b) a dense boundary-sampling brute force that makes NO use of the unfolding
      crossing conditions and explicitly rejects ground segments that cut
      through either base,
  (c) a 3-D Dijkstra over a fine triangulated mesh of the whole surface
      (makes no use of the "one face" claim at all), on small cases.
"""
import math, random, heapq

# ---------------------------------------------------------------- geometry --
def sub(a, b): return (a[0]-b[0], a[1]-b[1])
def add(a, b): return (a[0]+b[0], a[1]+b[1])
def mul(a, t): return (a[0]*t, a[1]*t)
def dot(a, b): return a[0]*b[0]+a[1]*b[1]
def cross(a, b): return a[0]*b[1]-a[1]*b[0]
def norm(a): return math.hypot(a[0], a[1])
def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])

class Pyr:
    def __init__(self, x1, y1, x2, y2, h):
        d = (x2-x1, y2-y1)
        s = norm(d)
        n = (-d[1], d[0])                 # left normal, length s -> body side
        p1 = (x1, y1); p2 = (x2, y2)
        p3 = add(p2, n); p4 = add(p1, n)
        self.corners = [p1, p2, p3, p4]   # CCW
        self.s = s
        self.h = h
        self.center = (sum(c[0] for c in self.corners)/4.0,
                       sum(c[1] for c in self.corners)/4.0)
        self.apex3 = (self.center[0], self.center[1], h)
        self.slant = math.hypot(h, s/2.0)          # apex -> base-edge midpoint
        self.lat = math.sqrt(h*h + s*s/2.0)        # apex -> base corner
        self.edges = []
        self.images = []
        for i in range(4):
            a = self.corners[i]; b = self.corners[(i+1) % 4]
            m = mul(add(a, b), 0.5)
            out = sub(m, self.center)
            out = mul(out, 1.0/norm(out))
            self.edges.append((a, b))
            self.images.append(add(m, mul(out, self.slant)))

def seg_hits_polygon_interior(u, v, poly, eps=1e-9):
    """True if open segment uv has positive-length overlap with the interior of
    the convex polygon poly (CCW)."""
    t0, t1 = 0.0, 1.0
    d = sub(v, u)
    for i in range(len(poly)):
        a = poly[i]; b = poly[(i+1) % len(poly)]
        e = sub(b, a)
        # inside == cross(e, p-a) > 0
        num = cross(e, sub(u, a))
        den = -cross(e, d)
        if abs(den) < 1e-18:
            if num <= 0:
                return False
            continue
        t = num/den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return False
    return (t1 - t0) * norm(d) > 1e-7

# ------------------------------------------------------- intended solution --
def solve(p, q):
    best = float('inf')
    for i in range(4):
        A = p.images[i]; (a1, a2) = p.edges[i]
        for j in range(4):
            B = q.images[j]; (b1, b2) = q.edges[j]
            def inner(u):
                lo, hi = 0.0, 1.0
                for _ in range(90):
                    m1 = lo + (hi-lo)/3.0; m2 = hi - (hi-lo)/3.0
                    v1 = add(b1, mul(sub(b2, b1), m1))
                    v2 = add(b1, mul(sub(b2, b1), m2))
                    f1 = dist(u, v1) + dist(v1, B)
                    f2 = dist(u, v2) + dist(v2, B)
                    if f1 < f2: hi = m2
                    else: lo = m1
                v = add(b1, mul(sub(b2, b1), (lo+hi)/2))
                return dist(u, v) + dist(v, B), v
            lo, hi = 0.0, 1.0
            for _ in range(90):
                m1 = lo + (hi-lo)/3.0; m2 = hi - (hi-lo)/3.0
                u1 = add(a1, mul(sub(a2, a1), m1))
                u2 = add(a1, mul(sub(a2, a1), m2))
                f1 = dist(A, u1) + inner(u1)[0]
                f2 = dist(A, u2) + inner(u2)[0]
                if f1 < f2: hi = m2
                else: lo = m1
            u = add(a1, mul(sub(a2, a1), (lo+hi)/2))
            r, v = inner(u)
            tot = dist(A, u) + r
            # reject configurations whose ground leg tunnels through a base
            if seg_hits_polygon_interior(u, v, p.corners) or \
               seg_hits_polygon_interior(u, v, q.corners):
                continue
            best = min(best, tot)
    return best

# ------------------------------------- brute force 1: boundary sampling ----
def boundary_samples(p, n):
    out = []
    for i in range(4):
        a, b = p.edges[i]
        A = p.images[i]
        for k in range(n+1):
            t = k/float(n)
            u = add(a, mul(sub(b, a), t))
            out.append((u, dist(A, u)))
    return out

def brute_sample(p, q, n=700):
    us = boundary_samples(p, n)
    vs = boundary_samples(q, n)
    best = float('inf')
    for (u, du) in us:
        if du >= best: continue
        for (v, dv) in vs:
            tot = du + dist(u, v) + dv
            if tot < best:
                if seg_hits_polygon_interior(u, v, p.corners) or \
                   seg_hits_polygon_interior(u, v, q.corners):
                    continue
                best = tot
    return best

# --------------------------- brute force 2: Dijkstra on a 3-D surface mesh --
def mesh_dijkstra(p, q, res=26, gres=34):
    """Nodes: lattice on each lateral face (barycentric), plus a lattice on a
    ground rectangle covering both bases (points inside a base are dropped).
    Edges: k-nearest within each patch.  Gives an upper bound that converges
    from above; used only as a sanity check on small configurations."""
    pts = []
    def face_pts(py):
        ap = py.apex3
        for i in range(4):
            a, b = py.edges[i]
            for r in range(res+1):
                for c in range(r+1):
                    # point on triangle apex,a,b
                    t = r/float(res)
                    if r == 0:
                        base = ((a[0]+b[0])/2, (a[1]+b[1])/2)
                        pt = (ap[0], ap[1], ap[2])
                        pts.append(pt); continue
                    u = c/float(r)
                    bx = a[0] + (b[0]-a[0])*u; by = a[1] + (b[1]-a[1])*u
                    pt = (ap[0] + (bx-ap[0])*t, ap[1] + (by-ap[1])*t, ap[2]*(1-t))
                    pts.append(pt)
    face_pts(p); face_pts(q)
    napex_p = 0
    xs = [c[0] for c in p.corners+q.corners]; ys = [c[1] for c in p.corners+q.corners]
    pad = 0.15*max(max(xs)-min(xs), max(ys)-min(ys), 1.0)
    x0, x1 = min(xs)-pad, max(xs)+pad; y0, y1 = min(ys)-pad, max(ys)+pad
    def inside(poly, pt):
        for i in range(4):
            a = poly[i]; b = poly[(i+1) % 4]
            if cross(sub(b, a), sub(pt, a)) < -1e-9: return False
        return True
    for i in range(gres+1):
        for j in range(gres+1):
            x = x0 + (x1-x0)*i/gres; y = y0 + (y1-y0)*j/gres
            if inside(p.corners, (x, y)) or inside(q.corners, (x, y)):
                continue
            pts.append((x, y, 0.0))
    # index apexes
    ai = min(range(len(pts)), key=lambda k: (pts[k][0]-p.apex3[0])**2+(pts[k][1]-p.apex3[1])**2+(pts[k][2]-p.apex3[2])**2)
    bi = min(range(len(pts)), key=lambda k: (pts[k][0]-q.apex3[0])**2+(pts[k][1]-q.apex3[1])**2+(pts[k][2]-q.apex3[2])**2)
    # k-nearest graph (brute force, small meshes only)
    N = len(pts)
    K = 12
    adj = [[] for _ in range(N)]
    for i in range(N):
        ds = []
        xi, yi, zi = pts[i]
        for j in range(N):
            if i == j: continue
            d = math.sqrt((xi-pts[j][0])**2+(yi-pts[j][1])**2+(zi-pts[j][2])**2)
            ds.append((d, j))
        ds.sort()
        for d, j in ds[:K]:
            adj[i].append((j, d))
    INF = float('inf')
    dd = [INF]*N; dd[ai] = 0.0
    pq = [(0.0, ai)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dd[u]+1e-15: continue
        if u == bi: break
        for v, w in adj[u]:
            nd = d+w
            if nd < dd[v]-1e-12:
                dd[v] = nd; heapq.heappush(pq, (nd, v))
    return dd[bi]

# ----------------------------------------------------------------- driver --
def sat_overlap(A, B):
    for poly in (A, B):
        for i in range(4):
            a = poly[i]; b = poly[(i+1) % 4]
            ax = (-(b[1]-a[1]), b[0]-a[0])
            pa = [dot(ax, c) for c in A]; pb = [dot(ax, c) for c in B]
            if max(pa) <= min(pb)+1e-9 or max(pb) <= min(pa)+1e-9:
                return False
    return True

if __name__ == '__main__':
    p = Pyr(0, 0, 10, 0, 4); q = Pyr(9, 18, 34, 26, 42)
    got = solve(p, q)
    print('sample  expected 60.866649532  got %.9f  diff %.2e' % (got, abs(got-60.866649532)))
    print('sample  brute-sample %.6f' % brute_sample(p, q, 900))

    random.seed(7)
    bad = 0
    for t in range(300):
        while True:
            x1, y1 = random.randint(-9, 9), random.randint(-9, 9)
            dx, dy = random.randint(-7, 7), random.randint(-7, 7)
            if (dx, dy) == (0, 0): continue
            a = Pyr(x1, y1, x1+dx, y1+dy, random.randint(1, 9))
            x1, y1 = random.randint(-9, 9), random.randint(-9, 9)
            dx, dy = random.randint(-7, 7), random.randint(-7, 7)
            if (dx, dy) == (0, 0): continue
            b = Pyr(x1, y1, x1+dx, y1+dy, random.randint(1, 9))
            if not sat_overlap(a.corners, b.corners):
                break
        s1 = solve(a, b); s2 = brute_sample(a, b, 500)
        # sampling can only over-estimate; require s1 <= s2 + tiny and close
        if not (s1 <= s2 + 1e-9 and s2 - s1 < 2e-3*max(1.0, s1)):
            bad += 1
            print('MISMATCH', a.corners, a.h, b.corners, b.h, s1, s2)
    print('random vs boundary-sampling brute force: %d/300 mismatches' % bad)

    # mesh Dijkstra sanity checks (upper bound, coarse)
    for (pa, pb) in [((0, 0, 4, 0, 3), (6, 1, 10, 1, 5)),
                     ((0, 0, 6, 0, 2), (0, 7, 5, 7, 6)),
                     ((0, 0, 5, 0, 7), (-1, 9, 4, 9, 2))]:
        A = Pyr(*pa); B = Pyr(*pb)
        ex = solve(A, B); mm = mesh_dijkstra(A, B)
        print('mesh check exact=%.5f  mesh(upper bd)=%.5f  ratio=%.4f' % (ex, mm, mm/ex))
