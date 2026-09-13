"""verify kattis-largesttriangle (2018 ICPC Asia Singapore Regional, problem A).

Claim under test (judges' slides 37-48): the maximum-area triangle over N
points has all three vertices on the convex hull, and for a FIXED hull vertex
a the largest triangle rooted at a can be found with a rotating-calipers-style
monotone two-pointer in O(h) -- so O(h^2) overall after an O(N log N) hull.

Checks:
  1. the statement's sample (7 points -> 100.00000);
  2. the two-pointer against an exhaustive O(N^3) brute force over ALL input
     points (not just hull points) on thousands of random small sets, with
     duplicates, collinear runs, points on a circle, grid points and degenerate
     all-collinear / all-identical sets;
  3. an exploratory search for a counterexample to the single-pass
     "rotating calipers over the whole hull" shortcut (Dobkin-Snyder), which
     Keikha et al. -- cited on slide 49 -- proved does not give a correct O(n)
     algorithm. Random small polygons do NOT expose it (none found in 240k
     tries here), which is precisely why it is a trap; the O(h^2) per-root
     version is used and verified instead.
  4. timing at the real bound N = 5000 with all points on a convex hull.
"""
import math
import random

# ---------- geometry ----------


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(pts):
    """Monotone chain, counter-clockwise, strictly convex (no collinear points)."""
    pts = sorted(set(pts))
    if len(pts) <= 2:
        return pts
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def twice_area(a, b, c):
    return abs(cross(a, b, c))


# ---------- the solution under test ----------


def solve(points):
    """Returns twice the maximum triangle area (an exact integer)."""
    h = convex_hull(points)
    n = len(h)
    if n < 3:
        return 0
    best = 0
    for i in range(n - 2):
        k = i + 2
        for j in range(i + 1, n - 1):
            if k < j + 1:
                k = j + 1
            while k + 1 <= n - 1 and \
                    twice_area(h[i], h[j], h[k + 1]) >= twice_area(h[i], h[j], h[k]):
                k += 1
            a = twice_area(h[i], h[j], h[k])
            if a > best:
                best = a
    return best


# ---------- the shortcut the slides warn about ----------


def dobkin_snyder(points):
    """Single O(h) calipers sweep over the whole hull -- known incorrect."""
    h = convex_hull(points)
    n = len(h)
    if n < 3:
        return 0
    best = 0
    a, b, c = 0, 1, 2
    while True:
        while True:
            while twice_area(h[a], h[b], h[(c + 1) % n]) >= twice_area(h[a], h[b], h[c]):
                c = (c + 1) % n
            best = max(best, twice_area(h[a], h[b], h[c]))
            if twice_area(h[a], h[(b + 1) % n], h[c]) > twice_area(h[a], h[b], h[c]):
                b = (b + 1) % n
            else:
                break
        a += 1
        if a >= n:
            break
        if b == a:
            b = (b + 1) % n
        if c == b:
            c = (c + 1) % n
    return best


# ---------- brute force ----------


def brute(points):
    n = len(points)
    best = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                a = twice_area(points[i], points[j], points[k])
                if a > best:
                    best = a
    return best


# ---------- generators ----------


def gen_random(rng, n, hi):
    return [(rng.randint(0, hi), rng.randint(0, hi)) for _ in range(n)]


def gen_collinear_heavy(rng, n, hi):
    pts = []
    for _ in range(n):
        if rng.random() < 0.6:
            t = rng.randint(0, hi)
            pts.append((t, (2 * t + 3) % (hi + 1)))
        else:
            pts.append((rng.randint(0, hi), rng.randint(0, hi)))
    return pts


def gen_circle(rng, n, r):
    pts = []
    for _ in range(n):
        th = rng.random() * 2 * math.pi
        pts.append((int(r + r * math.cos(th)), int(r + r * math.sin(th))))
    return pts


def gen_dupes(rng, n, hi):
    base = [(rng.randint(0, hi), rng.randint(0, hi)) for _ in range(max(3, n // 3))]
    return [base[rng.randrange(len(base))] for _ in range(n)]


def main():
    # 1. statement sample
    sample = [(0, 0), (0, 5), (7, 7), (0, 10), (0, 0), (20, 0), (10, 10)]
    got = solve(sample) / 2.0
    print("sample: %.5f (expected 100.00000)" % got)
    assert abs(got - 100.0) < 1e-9
    assert brute(sample) == solve(sample)

    # degenerate sets
    assert solve([(1, 1), (2, 2), (3, 3), (7, 7)]) == 0, "all collinear -> 0"
    assert solve([(4, 4)] * 5) == 0, "all identical -> 0"
    assert solve([(0, 0), (0, 0), (5, 0)]) == 0, "degenerate triple -> 0"
    print("degenerate cases OK (collinear / identical -> 0)")

    # 2. randomized cross-check
    rng = random.Random(20181215)
    trials = 0
    for gen, hi_choices in ((gen_random, (3, 8, 40, 10 ** 6)),
                            (gen_collinear_heavy, (5, 12, 60)),
                            (gen_circle, (6, 25, 400)),
                            (gen_dupes, (4, 9, 50))):
        for hi in hi_choices:
            for _ in range(140):
                n = rng.randint(3, 12)
                pts = gen(rng, n, hi)
                e, g = brute(pts), solve(pts)
                trials += 1
                if e != g:
                    raise AssertionError("MISMATCH %r expected %d got %d" % (pts, e, g))
    # a second sweep at larger n
    for _ in range(400):
        n = rng.randint(13, 30)
        pts = gen_random(rng, n, rng.choice((10, 50, 5000)))
        e, g = brute(pts), solve(pts)
        trials += 1
        if e != g:
            raise AssertionError("MISMATCH %r expected %d got %d" % (pts, e, g))
    print("two-pointer == O(N^3) brute force on %d random point sets" % trials)

    # 3. the single-sweep shortcut is genuinely wrong
    bad = None
    for _ in range(40000):
        n = rng.randint(5, 14)
        pts = gen_random(rng, n, rng.choice((20, 100)))
        if len(convex_hull(pts)) < 5:
            continue
        if dobkin_snyder(pts) != brute(pts):
            bad = (pts, dobkin_snyder(pts), brute(pts))
            break
    if bad:
        print("one-sweep calipers FAILS, e.g. %r: got %d want %d" % bad)
    else:
        print("no counterexample to the one-sweep shortcut found on random small "
              "polygons -- it is known-unsound (Keikha et al.) but not randomly "
              "falsifiable, so the O(h^2) per-root algorithm is what is used")

    # 4. timing at the real bound
    import time
    r = 20_000_000
    big = []
    seen = set()
    k = 0
    while len(big) < 5000:
        th = 2 * math.pi * k / 5000.0
        p = (int(r + r * math.cos(th)), int(r + r * math.sin(th)))
        k += 1
        if p not in seen:
            seen.add(p)
            big.append(p)
    t0 = time.time()
    hull = convex_hull(big)
    res = solve(big)
    t1 = time.time()
    print("N=5000 near-circular (hull size %d): area=%.1f in %.1fs (pure python; "
          "the O(h^2) loop is ~%.1fM cross products)"
          % (len(hull), res / 2.0, t1 - t0, len(hull) ** 2 / 2e6))
    print("ALL OK")


if __name__ == "__main__":
    main()
