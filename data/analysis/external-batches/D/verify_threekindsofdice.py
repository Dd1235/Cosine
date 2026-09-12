"""Verification for kattis-threekindsofdice (ICPC WF 2022 'Three Kinds of Dice').

Claimed reduction
-----------------
A die D3 is a uniform distribution over its faces, so
    score(D3, D) = (1/|D3|) * sum_{v in D3} score(<single face v>, D)
i.e. both quantities we optimise are LINEAR in the distribution of D3.
Map each candidate face value v to the plane point
    P(v) = ( x(v), y(v) ) = ( score(v, D1), score(v, D2) ),
    score(v, D) = (#{f in D : f < v} + 0.5 * #{f in D : f == v}) / |D|.
x(v), y(v) are step functions of v, so only O(n) distinct points exist:
candidates are every face value f and every f+1 (plus 1), which covers both
"lands exactly on a face" and "lands strictly inside a gap".

Achievable (score(D3,D1), score(D3,D2)) pairs = rational convex combinations of
those points = conv(P) (optima sit at a vertex or on one edge, so the required
weights are rational and a real die attains them).

Then:
  answer 1 = min y subject to x >= 1/2   over conv(P)
  answer 2 = max x subject to y <= 1/2   over conv(P)
which is a convex-hull / linear-programming-in-2D query.  O(n log n).

This script checks that against:
  (a) an exact O(N^2) enumeration of every hull vertex and every edge-vs-line
      crossing (independent of the hull code),
  (b) exhaustive brute force over ACTUAL small dice D3 (multisets of faces),
  (c) a constructive check: rebuild the real die achieving the optimum and
      recompute its two scores directly.
"""
from fractions import Fraction as F
from itertools import combinations_with_replacement
import random, bisect

HALF = F(1, 2)


# ---------- basic scoring ----------
def score_val(v, die_sorted, m):
    """score(single face v, die)"""
    lo = bisect.bisect_left(die_sorted, v)
    hi = bisect.bisect_right(die_sorted, v)
    return F(2 * lo + (hi - lo), 2 * m)


def score_dice(A, B):
    """score(A, B) for two dice given as face lists."""
    Bs = sorted(B)
    return sum(score_val(v, Bs, len(B)) for v in A) / len(A)


# ---------- candidate points ----------
def candidate_points(D1, D2):
    s1, s2 = sorted(D1), sorted(D2)
    n1, n2 = len(D1), len(D2)
    vals = {1}
    for f in D1 + D2:
        vals.add(f)
        vals.add(f + 1)
    return [(score_val(v, s1, n1), score_val(v, s2, n2)) for v in sorted(vals)], sorted(vals)


# ---------- convex hull (monotone chain, exact rationals) ----------
def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def lower_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    h = []
    for p in pts:
        while len(h) >= 2 and cross(h[-2], h[-1], p) <= 0:
            h.pop()
        h.append(p)
    return h


def min_second_given_first_ge(points, c):
    """min of second coord over conv(points) intersected with {first >= c}."""
    hull = lower_hull(points)          # lower boundary, x increasing
    best = None
    for (x, y) in hull:
        if x >= c and (best is None or y < best):
            best = y
    for (xa, ya), (xb, yb) in zip(hull, hull[1:]):
        if xa <= c <= xb and xa != xb:
            t = (c - xa) / (xb - xa)
            y = ya + t * (yb - ya)
            if best is None or y < best:
                best = y
    return best


def solve_hull(dieA, dieB):
    """Returns (answer1, answer2) exactly, plus the identified (D1, D2)."""
    if score_dice(dieA, dieB) > HALF:
        D1, D2 = dieA, dieB
    else:
        D1, D2 = dieB, dieA
    pts, _ = candidate_points(D1, D2)
    a1 = min_second_given_first_ge(pts, HALF)
    # max x s.t. y <= 1/2  ==  min (-x) s.t. (-y) >= -1/2
    flipped = [(-y, -x) for (x, y) in pts]
    a2 = -min_second_given_first_ge(flipped, -HALF)
    return a1, a2, D1, D2


# ---------- (a) independent O(N^2) exact LP over the point set ----------
def brute_pairs(D1, D2):
    pts, _ = candidate_points(D1, D2)
    pts = sorted(set(pts))

    def opt(points, c, mode):
        # mode 'min': min second s.t. first >= c
        best = None
        for (x, y) in points:
            if x >= c and (best is None or y < best):
                best = y
        for (xa, ya), (xb, yb) in combinations(points, 2):
            if xa == xb:
                continue
            if min(xa, xb) <= c <= max(xa, xb):
                t = (c - xa) / (xb - xa)
                y = ya + t * (yb - ya)
                if best is None or y < best:
                    best = y
        return best

    from itertools import combinations
    a1 = opt(pts, HALF, 'min')
    flipped = sorted({(-y, -x) for (x, y) in pts})
    a2 = -opt(flipped, -HALF, 'min')
    return a1, a2


# ---------- (b) exhaustive over real dice ----------
def brute_dice(D1, D2, max_faces, value_pool):
    s1, s2 = sorted(D1), sorted(D2)
    n1, n2 = len(D1), len(D2)
    best1 = None   # min score(D3,D2) with score(D3,D1) >= 1/2
    best2 = None   # max score(D3,D1) with score(D3,D2) <= 1/2
    for k in range(1, max_faces + 1):
        for faces in combinations_with_replacement(value_pool, k):
            x = sum(score_val(v, s1, n1) for v in faces) / k
            y = sum(score_val(v, s2, n2) for v in faces) / k
            if x >= HALF and (best1 is None or y < best1):
                best1 = y
            if y <= HALF and (best2 is None or x > best2):
                best2 = x
    return best1, best2


# ---------- (c) constructive check ----------
def construct_and_check(D1, D2, target1, target2):
    """Find an explicit die attaining each optimum and verify it directly."""
    pts, vals = candidate_points(D1, D2)
    ok1 = ok2 = False
    P = list(zip(vals, pts))
    # query 1: need x >= 1/2 and y == target1
    for (va, (xa, ya)), (vb, (xb, yb)) in combinations_with_replacement(P, 2):
        cand = []
        if xa != xb:
            t = (HALF - xa) / (xb - xa)
            if 0 <= t <= 1:
                cand.append((t, va, vb))
        for t, u, w in cand:
            y = ya + t * (yb - ya)
            if y != target1:
                continue
            q = t.denominator
            a = t.numerator
            die = [u] * (q - a) + [w] * a
            if score_dice(die, D1) >= HALF and score_dice(die, D2) == target1:
                ok1 = True
        # query 2: need y <= 1/2, x == target2
        if ya != yb:
            t = (HALF - ya) / (yb - ya)
            if 0 <= t <= 1:
                x = xa + t * (xb - xa)
                if x == target2:
                    q, a = t.denominator, t.numerator
                    die = [va] * (q - a) + [vb] * a
                    if score_dice(die, D2) <= HALF and score_dice(die, D1) == target2:
                        ok2 = True
    # single-point optima
    for v, (x, y) in P:
        if x >= HALF and y == target1:
            ok1 = True
        if y <= HALF and x == target2:
            ok2 = True
    return ok1, ok2


# ---------- driver ----------
def run_samples():
    samples = [
        ([1, 1, 6, 6, 8, 8], [2, 4, 9], ("0.291666667", "0.750000000")),
        ([9, 3, 7, 5], [4, 2, 3], ("0.500000000", "0.500000000")),
    ]
    for A, B, exp in samples:
        a1, a2, D1, D2 = solve_hull(A, B)
        got = ("%.9f" % float(a1), "%.9f" % float(a2))
        print("sample", A, B, "->", got, "expected", exp, "OK" if got == exp else "MISMATCH")
        assert got == exp


def random_tests(trials=300):
    rng = random.Random(20260912)
    bad = 0
    for t in range(trials):
        while True:
            n1 = rng.randint(1, 5)
            n2 = rng.randint(1, 5)
            V = rng.choice([4, 6, 9])
            A = [rng.randint(1, V) for _ in range(n1)]
            B = [rng.randint(1, V) for _ in range(n2)]
            if score_dice(A, B) != HALF:
                break
        a1, a2, D1, D2 = solve_hull(A, B)
        b1, b2 = brute_pairs(D1, D2)
        if (a1, a2) != (b1, b2):
            print("PAIR-LP MISMATCH", A, B, (a1, a2), (b1, b2))
            bad += 1
            continue
        c1, c2 = construct_and_check(D1, D2, a1, a2)
        if not (c1 and c2):
            print("NOT CONSTRUCTIBLE", A, B, a1, a2, c1, c2)
            bad += 1
        if t < 60:
            pool = sorted(set(list(range(1, V + 2))))
            d1, d2 = brute_dice(D1, D2, 5, pool)
            # brute over <=5 faces can only be worse-or-equal than the true optimum
            if d1 is not None and d1 < a1:
                print("BRUTE BEATS HULL (q1)", A, B, a1, d1); bad += 1
            if d2 is not None and d2 > a2:
                print("BRUTE BEATS HULL (q2)", A, B, a2, d2); bad += 1
    print("random tests done, mismatches =", bad)
    return bad


def exhaustive_small(trials=40):
    """Tighter: tiny dice where <=8-face brute force should REACH the optimum."""
    rng = random.Random(7)
    bad = 0
    for _ in range(trials):
        while True:
            A = [rng.randint(1, 3) for _ in range(rng.randint(1, 2))]
            B = [rng.randint(1, 3) for _ in range(rng.randint(1, 2))]
            if score_dice(A, B) != HALF:
                break
        a1, a2, D1, D2 = solve_hull(A, B)
        d1, d2 = brute_dice(D1, D2, 8, list(range(1, 5)))
        if d1 != a1 or d2 != a2:
            print("EXHAUSTIVE MISMATCH", A, B, (a1, a2), (d1, d2)); bad += 1
    print("exhaustive small done, mismatches =", bad)
    return bad


if __name__ == "__main__":
    run_samples()
    bad = random_tests()
    bad += exhaustive_small()
    print("TOTAL BAD:", bad)
