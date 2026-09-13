#!/usr/bin/env python3
"""Verification for kattis-canthoexpressway (2020 ICPC Asia Can Tho, problem C).

The published solution (_tooling/solutions/canthoexpressway.cpp,
sha256 8e0bd20f...) never clips anything: it decides "positive common area"
from sign tests on a*x+b*y-c at the k <= 6 vertices --

  * some edge strictly crosses one of the two boundary lines, or
  * some edge joins a vertex on one boundary line to a vertex on the other, or
  * some vertex lies strictly between the two lines.

This script checks that verdict against an exact oracle: clip the convex
polygon by the two half-planes with Fraction arithmetic (Sutherland-Hodgman)
and take the shoelace area, answering YES iff that area is strictly positive.
A third, independent decision procedure is also compared: project the vertices
onto (a,b) and ask whether [min f, max f] overlaps [min c, max c] in positive
length, which is equivalent because a convex polygon with interior has a
positive-length chord on every line strictly between its supporting lines.

Usage:  python3 verify_canthoexpressway.py [path-to-compiled-binary]
The binary argument is optional: with none, the script builds the recorded
solution source itself and cleans up after.
"""
import random
import subprocess
import sys
from fractions import Fraction

def _build(name):
    """Return a runnable binary for `name`, building it from the recorded source
    if the caller did not pass one.  The published C++ lives in the repo at
    data/analysis/external-batches/_tooling/solutions/<name>.cpp; it includes
    <bits/stdc++.h>, which Apple clang does not ship, so a shim is written into
    the build directory.  Pass an explicit path as argv[1] to skip all of this.
    """
    import os, shutil, subprocess, sys, tempfile, atexit
    if len(sys.argv) > 1:
        return sys.argv[1]
    if os.path.exists("./" + name):
        return "./" + name
    here = os.path.dirname(os.path.abspath(__file__))
    src = None
    for root in (here, os.path.dirname(os.path.dirname(here))):
        cand = os.path.join(root, "data", "analysis", "external-batches",
                            "_tooling", "solutions", name + ".cpp")
        if os.path.exists(cand):
            src = cand
            break
        cand = os.path.join(root, "_tooling", "solutions", name + ".cpp")
        if os.path.exists(cand):
            src = cand
            break
    if src is None:
        sys.exit("cannot find %s.cpp; pass a compiled binary as the first argument" % name)
    cxx = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++")
    if cxx is None:
        sys.exit("no C++ compiler found; pass a compiled binary as the first argument")
    tmp = tempfile.mkdtemp(prefix="verify-" + name + "-")
    atexit.register(shutil.rmtree, tmp, True)
    os.makedirs(os.path.join(tmp, "bits"), exist_ok=True)
    with open(os.path.join(tmp, "bits", "stdc++.h"), "w") as fh:
        fh.write("#pragma once\n" + "".join(
            "#include <%s>\n" % h for h in (
                "algorithm array bitset cassert cctype chrono climits cmath complex "
                "cstdint cstdio cstdlib cstring deque functional iomanip iostream "
                "iterator limits list map numeric queue random set sstream stack "
                "string tuple unordered_map unordered_set utility vector").split()))
    out = os.path.join(tmp, name)
    r = subprocess.run([cxx, "-O2", "-std=c++17", "-I", tmp, "-o", out, src],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("failed to build %s:\n%s" % (src, r.stderr[-2000:]))
    return out
BIN = _build("canthoexpressway")


# ---------------------------------------------------------------- oracle ----
def clip(poly, a, b, c, keep_ge):
    """Clip polygon by a*x+b*y >= c (keep_ge) or <= c.  Exact, Fractions."""
    def side(p):
        v = a * p[0] + b * p[1] - c
        return v if keep_ge else -v

    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        sp, sq = side(p), side(q)
        if sp >= 0:
            out.append(p)
        if (sp > 0 and sq < 0) or (sp < 0 and sq > 0):
            t = sp / (sp - sq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def area2(poly):
    s = Fraction(0)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s)


def oracle(a, b, c1, c2, pts):
    poly = [(Fraction(x), Fraction(y)) for x, y in pts]
    lo, hi = min(c1, c2), max(c1, c2)
    poly = clip(poly, a, b, lo, True)
    if len(poly) < 3:
        return False
    poly = clip(poly, a, b, hi, False)
    if len(poly) < 3:
        return False
    return area2(poly) > 0


def projection_test(a, b, c1, c2, pts):
    vals = [a * x + b * y for x, y in pts]
    lo, hi = min(c1, c2), max(c1, c2)
    return max(min(vals), lo) < min(max(vals), hi)


# ------------------------------------------------------------- polygons -----
def cross(o, u, v):
    return (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0])


def hull(points):
    pts = sorted(set(points))
    if len(pts) < 3:
        return []
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
    h = lower[:-1] + upper[:-1]
    return h if len(h) >= 3 else []


def random_polygon(rng, span):
    """A strictly convex polygon with 3..6 vertices (no 3 consecutive collinear)."""
    for _ in range(200):
        m = rng.randint(3, 9)
        h = hull([(rng.randint(-span, span), rng.randint(-span, span)) for _ in range(m)])
        if 3 <= len(h) <= 6:
            if rng.random() < 0.5:
                h = h[::-1]          # the statement allows either orientation
            k = rng.randrange(len(h))
            return h[k:] + h[:k]     # and any starting vertex
    return [(0, 0), (1, 0), (0, 1)]


def random_case(rng, span, cspan):
    while True:
        a = rng.randint(-cspan, cspan)
        b = rng.randint(-cspan, cspan)
        if a * a + b * b > 0:
            break
    while True:
        c1 = rng.randint(-cspan, cspan)
        c2 = rng.randint(-cspan, cspan)
        if c1 != c2:
            break
    return a, b, c1, c2, random_polygon(rng, span)



def tangent_case(rng):
    """Cases engineered so a strip boundary passes exactly through vertices --
    the class where "touches" must be distinguished from "positive area"."""
    while True:
        span = rng.randint(1, 5)
        pts = random_polygon(rng, span)
        while True:
            a = rng.randint(-3, 3)
            b = rng.randint(-3, 3)
            if a * a + b * b > 0:
                break
        vals = sorted(set(a * x + b * y for x, y in pts))
        pool = set()
        for v in vals:
            pool.update((v - 1, v, v + 1))
        pool = [v for v in pool if -100 <= v <= 100]
        if len(pool) < 2:
            continue
        c1 = rng.choice(pool)
        c2 = rng.choice(pool)
        if c1 == c2:
            continue
        return a, b, c1, c2, pts

# --------------------------------------------------------------- driver -----
def run(cases):
    lines = [str(len(cases))]
    for a, b, c1, c2, pts in cases:
        lines.append("%d %d %d %d" % (a, b, c1, c2))
        lines.append(str(len(pts)) + " " + " ".join("%d %d" % p for p in pts))
    out = subprocess.run([BIN], input="\n".join(lines) + "\n",
                         capture_output=True, text=True, timeout=600)
    if out.returncode != 0:
        raise SystemExit("binary failed: %s" % out.stderr[-400:])
    got = out.stdout.split()
    if len(got) != len(cases):
        raise SystemExit("expected %d verdicts, got %d" % (len(cases), len(got)))
    return got


def check(cases, label):
    got = run(cases)
    for (a, b, c1, c2, pts), g in zip(cases, got):
        want = oracle(a, b, c1, c2, pts)
        proj = projection_test(a, b, c1, c2, pts)
        if proj != want:
            raise SystemExit("projection test disagrees with exact clipping: %s" %
                             ((a, b, c1, c2, pts),))
        if (g == "YES") != want:
            raise SystemExit("solution said %s, exact area oracle says %s: %s" %
                             (g, "YES" if want else "NO", (a, b, c1, c2, pts)))
    yes = sum(1 for g in got if g == "YES")
    print("%-34s %6d cases OK (%d YES / %d NO)" % (label, len(cases), yes, len(cases) - yes))


def main():
    # the statement's sample
    sample = [(0, 1, 0, 1, [(2, 2), (1, 3), (1, 4), (2, 5), (3, 4), (3, 3)]),
              (0, 1, 0, 1, [(2, -1), (1, 0), (1, 1), (2, 2), (3, 1), (3, 0)])]
    got = run(sample)
    assert got == ["NO", "YES"], got
    print("sample 1 OK (NO, YES)")

    rng = random.Random(2020)
    # tiny coordinates: boundary coincidences (vertices exactly on a line,
    # edges lying inside a line, polygon touching a line at one vertex) are common
    for span, cspan, label in ((2, 2, "tiny coords (touching cases)"),
                               (3, 3, "small coords"),
                               (6, 4, "medium coords"),
                               (10000, 100, "full-range coords")):
        for _ in range(12):
            check([random_case(rng, span, cspan) for _ in range(500)],
                  label)

    # strips whose boundaries land exactly on vertex projections
    for _ in range(12):
        check([tangent_case(rng) for _ in range(500)], "tangent strips (engineered)")

    # adversarial: axis-parallel strips whose boundaries fall exactly on vertices
    hand = []
    sq = [(0, 0), (4, 0), (4, 4), (0, 4)]
    tri = [(0, 0), (4, 0), (0, 4)]
    for c1, c2 in ((-3, 0), (0, 4), (4, 7), (-1, 5), (0, 0 + 1), (3, 4), (4, 5), (-5, -1)):
        for a, b in ((0, 1), (1, 0), (1, 1), (1, -1), (-1, -1), (2, 1)):
            hand.append((a, b, c1, c2, sq))
            hand.append((a, b, c1, c2, tri))
    check(hand, "hand-built touching strips")

    # extreme magnitudes: the sign products reach 4e12 (the solution uses 1LL*)
    ext = []
    for _ in range(400):
        ext.append(random_case(rng, 10000, 100))
    big = [(100, 100, -100, 100, [(-10000, -10000), (10000, -10000), (10000, 10000), (-10000, 10000)]),
           (100, -100, 99, 100, [(-10000, -10000), (10000, -10000), (10000, 10000), (-10000, 10000)]),
           (1, 0, -100, -99, [(-10000, 0), (10000, 1), (0, 10000)])]
    check(ext + big, "extreme magnitudes")

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
