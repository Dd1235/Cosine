"""Check for kattis-peaktower.

Claim: clip every moving rectangle to the scene [0,W]x[0,H] and let f(t) be the
area of their union.  Sweeping x, f(t) = sum over vertical strips of (strip
width) * (length of the union of the active y-intervals).  As long as no two of
the 2N+2 x-coordinates (object edges plus the clip lines 0 and W) cross and no
two of the 2N+2 y-coordinates cross, the active set of every strip and the
merge pattern of the y-intervals are fixed, so both factors are linear in t and
f is a quadratic polynomial on that interval.  All crossings are roots of linear
equations, O(N^2) of them, so f is minimised exactly by fitting the quadratic on
each interval between consecutive events and checking its vertex and endpoints.

Tested against a dense scan of t with an independent coordinate-compression
union-area routine.
"""
import random


def clipped(obj, t, W, H):
    w, h, sx, sy, vx, vy = obj
    x1 = sx + vx * t
    y1 = sy + vy * t
    x2, y2 = x1 + w, y1 + h
    x1, x2 = max(0.0, min(W, x1)), max(0.0, min(W, x2))
    y1, y2 = max(0.0, min(H, y1)), max(0.0, min(H, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)


def area_at(objs, t, W, H):
    rects = [r for r in (clipped(o, t, W, H) for o in objs) if r]
    if not rects:
        return 0.0
    xs = sorted({r[0] for r in rects} | {r[2] for r in rects})
    ys = sorted({r[1] for r in rects} | {r[3] for r in rects})
    total = 0.0
    for i in range(len(xs) - 1):
        xm = (xs[i] + xs[i + 1]) / 2
        act = [r for r in rects if r[0] <= xm <= r[2]]
        if not act:
            continue
        cov = 0.0
        for j in range(len(ys) - 1):
            ym = (ys[j] + ys[j + 1]) / 2
            if any(r[1] <= ym <= r[3] for r in act):
                cov += ys[j + 1] - ys[j]
        total += (xs[i + 1] - xs[i]) * cov
    return total


def events(objs, W, H, E):
    """All times in [0,E] where the x-order or y-order of the coordinates changes."""
    xs = []   # (const, slope) for each x-coordinate that matters
    ys = []
    for w, h, sx, sy, vx, vy in objs:
        xs.append((sx, vx))
        xs.append((sx + w, vx))
        ys.append((sy, vy))
        ys.append((sy + h, vy))
    xs += [(0.0, 0.0), (W, 0.0)]
    ys += [(0.0, 0.0), (H, 0.0)]
    ts = {0.0, E}
    for arr in (xs, ys):
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                c1, m1 = arr[i]
                c2, m2 = arr[j]
                if m1 == m2:
                    continue
                t = (c2 - c1) / (m1 - m2)
                if 0.0 < t < E:
                    ts.add(t)
    return sorted(ts)


def solve(objs, W, H, E):
    ts = events(objs, W, H, E)
    best = float("inf")
    for i in range(len(ts) - 1):
        a, b = ts[i], ts[i + 1]
        m = (a + b) / 2
        fa, fm, fb = (area_at(objs, x, W, H) for x in (a, m, b))
        best = min(best, fa, fm, fb)
        # fit q(t) = A t^2 + B t + C through (a,fa),(m,fm),(b,fb) and test the vertex
        d = (a - m) * (a - b) * (m - b)
        if abs(d) < 1e-15:
            continue
        A = (b * (fm - fa) + m * (fa - fb) + a * (fb - fm)) / d
        B = (b * b * (fa - fm) + m * m * (fb - fa) + a * a * (fm - fb)) / d
        if A > 1e-12:
            v = -B / (2 * A)
            if a < v < b:
                best = min(best, area_at(objs, v, W, H))
    if not ts:
        best = area_at(objs, 0.0, W, H)
    return best


def dense(objs, W, H, E, steps=20000):
    return min(area_at(objs, E * i / steps, W, H) for i in range(steps + 1))


def main():
    assert abs(solve([], 300.0, 200.0, 6.0)) < 1e-9
    s2 = [(15.0, 20.0, 125.0, 0.0, 10.0, 0.0), (15.0, 15.0, 240.0, 0.0, -10.0, 0.0)]
    got = solve(s2, 270.0, 200.0, 10.0)
    assert abs(got - 300.0) < 1e-6, got
    print("both statement samples OK (0.0 and %.6f)" % got)

    rng = random.Random(17)
    bad = 0
    for trial in range(120):
        n = rng.randint(1, 6)
        W = rng.uniform(20, 60)
        H = rng.uniform(20, 60)
        E = rng.uniform(1, 10)
        objs = []
        for _ in range(n):
            w = rng.uniform(1, 25)
            h = rng.uniform(1, 25)
            objs.append((w, h, rng.uniform(-30, 60), rng.uniform(-30, 60),
                         rng.uniform(-20, 20), rng.uniform(-20, 20)))
        ev = solve(objs, W, H, E)
        dn = dense(objs, W, H, E, 4000)
        if ev > dn + 1e-7 or dn - ev > 1e-3 * max(1.0, dn):
            bad += 1
            print("MISMATCH trial=%d events=%.9f dense=%.9f objs=%s" % (trial, ev, dn, objs))
            if bad > 3:
                return
    print("120 random instances: event minimum always <= dense scan and within 1e-3 (%s)"
          % ("OK" if bad == 0 else "%d FAILURES" % bad))


if __name__ == "__main__":
    main()
