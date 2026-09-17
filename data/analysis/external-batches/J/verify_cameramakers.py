"""Kattis cameramakers (2015 ICPC Singapore, I).

Task: N <= 100000 lattice points, 2 <= K <= 200 (and either K <= 20 or N <= 5000).
Place one disk anywhere; find the smallest radius R whose disk covers at least K
of the points.  Print R to two decimals.

Solution under test: binary search on R with the classical "arc cover" decision
test.  If some disk of radius R covers K points then, by sliding the centre away
from them until the farthest covered point is at distance exactly R, there is a
witness centre lying on the circle C_i of radius R about some input point i.  For
a centre o on C_i, another point j is covered iff o lies on the arc of C_i of
half-width acos(d(i,j)/(2R)) around the direction i->j -- so for each i, collect
those arcs for the j with d(i,j) <= 2R, sweep the interval endpoints, and compare
1 + max overlap with K.

Restricting j to d(i,j) <= 2R is what makes it fit: with U = min_i d_{K-1}(i)
(distance from i to its (K-1)-st nearest neighbour) one has R* <= U (the disk
centred at the minimising i covers K points) and U <= 2R* (every point of the
optimal disk is within 2R* of any other), so R* lies in [U/2, U]; and a square of
side U/2 can hold at most K-1 points (else R* <= U/(2 sqrt 2) < U/2), so a disk of
radius 2U about any point holds O(K) points.  Hence each sweep is over O(K) arcs
and a decision costs O(N K log K); the "K <= 20 or N <= 5000" clause is exactly
what keeps N*K around 2*10^7.  Space O(N).

Brute force: every radius that can be optimal is half a pair distance or a triple
circumradius, so enumerate all pairs and triples and take the smallest radius
whose circle covers K points.
"""
import math, random

EPS = 1e-9

def decide(pts, K, R):
    """is there a disk of radius R covering >= K points?"""
    n = len(pts)
    if R <= 0:
        return K == 1
    R2 = (2 * R) ** 2
    for i in range(n):
        xi, yi = pts[i]
        ev = []
        for j in range(n):
            if j == i:
                continue
            dx, dy = pts[j][0] - xi, pts[j][1] - yi
            d2 = dx * dx + dy * dy
            if d2 > R2 + EPS:
                continue
            d = math.sqrt(d2)
            base = math.atan2(dy, dx)
            half = math.acos(min(1.0, max(-1.0, d / (2 * R))))
            a, b = base - half, base + half
            # normalise to [0, 2pi) and split wrapping arcs
            a %= 2 * math.pi
            b %= 2 * math.pi
            if a <= b:
                ev.append((a - EPS, 1)); ev.append((b + EPS, -1))
            else:
                ev.append((a - EPS, 1)); ev.append((2 * math.pi, -1))
                ev.append((0.0, 1)); ev.append((b + EPS, -1))
        ev.sort()
        cur = best = 0
        for _, t in ev:
            cur += t
            if cur > best:
                best = cur
        if best + 1 >= K:
            return True
    return False

def solve(pts, K):
    lo, hi = 0.0, 1.5e6
    # tighten hi: U = min over i of distance to its (K-1)-st nearest neighbour
    n = len(pts)
    U = hi
    for i in range(n):
        ds = sorted((pts[i][0] - q[0]) ** 2 + (pts[i][1] - q[1]) ** 2 for q in pts)
        if len(ds) >= K:
            U = min(U, math.sqrt(ds[K - 1]))
    hi = U
    lo = U / 2 - 1e-6
    if not decide(pts, K, lo):
        pass
    else:
        lo = 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if decide(pts, K, mid):
            hi = mid
        else:
            lo = mid
    return hi

def brute(pts, K):
    n = len(pts)
    cands = []
    for i in range(n):
        for j in range(i + 1, n):
            cx = (pts[i][0] + pts[j][0]) / 2.0
            cy = (pts[i][1] + pts[j][1]) / 2.0
            r = math.hypot(pts[i][0] - cx, pts[i][1] - cy)
            cands.append((r, cx, cy))
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                ax, ay = pts[i]; bx, by = pts[j]; cx_, cy_ = pts[k]
                d = 2 * (ax * (by - cy_) + bx * (cy_ - ay) + cx_ * (ay - by))
                if abs(d) < 1e-12:
                    continue
                ux = ((ax*ax+ay*ay)*(by-cy_) + (bx*bx+by*by)*(cy_-ay) + (cx_*cx_+cy_*cy_)*(ay-by)) / d
                uy = ((ax*ax+ay*ay)*(cx_-bx) + (bx*bx+by*by)*(ax-cx_) + (cx_*cx_+cy_*cy_)*(bx-ax)) / d
                cands.append((math.hypot(ax - ux, ay - uy), ux, uy))
    best = None
    for r, cx, cy in sorted(cands):
        cnt = sum(1 for (x, y) in pts if math.hypot(x - cx, y - cy) <= r + 1e-9)
        if cnt >= K:
            best = r
            break
    return best

def samples():
    pts = [(1, 1), (0, 2), (0, 0), (3, 2)]
    got = solve(pts, 3)
    assert abs(got - 1.0) < 1e-3, got
    print("sample OK  (R = %.2f)" % got)

def fuzz(trials=150):
    rnd = random.Random(20150)
    for t in range(trials):
        n = rnd.randint(2, 7)
        pts = set()
        while len(pts) < n:
            pts.add((rnd.randint(0, 12), rnd.randint(0, 12)))
        pts = sorted(pts)
        K = rnd.randint(2, n)
        a, b = solve(pts, K), brute(pts, K)
        if abs(a - b) > 1e-3:
            print("MISMATCH", pts, K, a, b)
            return False
    print("fuzz OK (%d random point sets vs exhaustive pair/triple circles)" % trials)
    return True

if __name__ == "__main__":
    samples()
    assert fuzz()
