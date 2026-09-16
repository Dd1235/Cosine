"""Numeric check for kattis-doors.

The fetched statement has no figure, so the layout below is RECONSTRUCTED from
the four sample scenarios (R=10, l=6, w=8):

    corridor  0 <= y <= w, extending right to Bob at (+inf, w/2)
    vertical shaft of width l above the ceiling: walls x=0 and x=l for y >= w,
      so the ceiling is y=w for x<=0 and for x>=l and the shaft mouth is (0,l)
    door A hinged at (0,w), pointing (cos A, -sin A): closed (A=0) it fills the
      mouth, A=pi lays it flat under the ceiling on the far side of the hinge
    door B hinged on a corridor wall far to the right, tip at height l*sin B

Claimed answer: min(R, dist(corner (l,w), door A)/2, (w - l*sin B)/2)
             =  min(R, l*sin(min(A, pi/2))/2, (w - l*sin B)/2).

This script (1) checks that closed form against the four sample answers and
(2) checks it against an actual motion-planning computation in the layout above
(coarse-grid BFS over the free configuration space, bisected on r).  What it
CANNOT check is the layout itself, in particular how far door B sits from the
shaft: if the figure puts the two doors close together the true answer gains a
door-A-to-door-B term this formula does not have.
"""
import math
from collections import deque


def formula(R, l, w, A, B):
    a = l * math.sin(min(A, math.pi / 2)) / 2.0
    b = (w - l * math.sin(B)) / 2.0
    return max(0.0, min(R, a, b))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    dd = dx * dx + dy * dy
    if dd == 0:
        t = 0.0
    else:
        t = ((px - ax) * dx + (py - ay) * dy) / dd
        t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def clearance(px, py, l, w, A, B, xB, big):
    """Distance from (px,py) to the nearest obstacle in the reconstructed layout."""
    d = []
    d.append(abs(py - 0.0) if -big <= px <= big else big)          # floor
    d.append(seg_dist(px, py, -big, w, 0.0, w))                    # ceiling left
    d.append(seg_dist(px, py, l, w, big, w))                       # ceiling right
    d.append(seg_dist(px, py, 0.0, w, 0.0, big))                   # shaft wall left
    d.append(seg_dist(px, py, l, w, l, big))                       # shaft wall right
    d.append(seg_dist(px, py, 0.0, w, l * math.cos(A), w - l * math.sin(A)))   # door A
    d.append(seg_dist(px, py, xB, 0.0, xB + l * math.cos(B), l * math.sin(B)))  # door B
    return min(d)


def numeric(R, l, w, A, B, step=0.1, xB=20.0):
    """Largest r (bisected) for which a disc of radius r gets from high in the
    shaft to the far right of the corridor, on a grid of the free space."""
    big = 60.0
    xs = [x * step for x in range(int(-15 / step), int(32 / step) + 1)]
    ys = [y * step for y in range(0, int((w + 14) / step) + 1)]
    nx, ny = len(xs), len(ys)
    clr = [[clearance(xs[i], ys[j], l, w, A, B, xB, big) for j in range(ny)]
           for i in range(nx)]
    si = min(range(nx), key=lambda i: abs(xs[i] - l / 2.0))
    sj = ny - 2
    ti = min(range(nx), key=lambda i: abs(xs[i] - 30.0))
    tj = min(range(ny), key=lambda j: abs(ys[j] - w / 2.0))

    def reachable(r):
        if clr[si][sj] < r or clr[ti][tj] < r:
            return False
        seen = [[False] * ny for _ in range(nx)]
        seen[si][sj] = True
        q = deque([(si, sj)])
        while q:
            i, j = q.popleft()
            if i == ti and j == tj:
                return True
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = i + di, j + dj
                if 0 <= a < nx and 0 <= b < ny and not seen[a][b] and clr[a][b] >= r:
                    seen[a][b] = True
                    q.append((a, b))
        return False

    lo, hi = 0.0, min(R, w / 2.0, l / 2.0) + 0.001
    if not reachable(1e-9):
        return 0.0
    for _ in range(22):
        mid = (lo + hi) / 2
        if reachable(mid):
            lo = mid
        else:
            hi = mid
    return lo


def main():
    R, l, w = 10.0, 6.0, 8.0
    samples = [((0.0000, 0.0000), 0.000000000),
               ((3.1415, 0.0000), 3.000000000),
               ((1.0472, 0.0000), 2.598079885),
               ((1.0472, 1.5708), 1.000000000)]
    for (A, B), exp in samples:
        got = formula(R, l, w, A, B)
        assert abs(got - exp) < 1e-6, (A, B, got, exp)
    print("all 4 statement samples match the closed form to 1e-6")

    # closed form vs. grid motion planning in the reconstructed layout
    tests = [(0.3, 0.0), (0.8, 0.4), (1.5708, 0.9), (2.4, 1.2), (3.0, 1.5708),
             (1.0472, 1.5708), (2.0, 0.2), (0.6, 1.1)]
    worst = 0.0
    for A, B in tests:
        f = formula(R, l, w, A, B)
        n = numeric(R, l, w, A, B)
        worst = max(worst, abs(f - n))
        print("A=%.4f B=%.4f formula=%.4f grid=%.4f diff=%.4f" % (A, B, f, n, abs(f - n)))
    print("worst |formula - grid| = %.4f (grid step 0.1, so <= ~0.15 is agreement)" % worst)


if __name__ == "__main__":
    main()
