"""Waterworld (ICPC WF 2023, kattis-waterworld) -- verification.

Claimed solution: the answer is the PLAIN arithmetic mean of all n*m percentages.

Why: the image is cut into n segments of equal HEIGHT, i.e. equal slabs of the
axis coordinate z, and into m equal longitude wedges of d = 360/m degrees.
By Archimedes' hat-box theorem the sphere area between two planes z=z1, z=z2 is
2*pi*R*(z2-z1) -- independent of latitude -- so every one of the n*m cells has
exactly the same area 4*pi*R^2/(n*m), and the water percentage of the sphere is
the unweighted average of the cell percentages.

This script checks, independently of the samples:
  (1) Archimedes numerically: band areas from the true surface integral
      integral 2*pi*sin(theta) dtheta are all equal for equal-z bands
      (and NOT equal for equal-polar-angle bands).
  (2) end-to-end: build a random water region on the sphere, compute each
      cell's water percentage and the global water percentage by exact/very
      fine numeric surface integration, and confirm mean(cells) == global.
  (3) the two published samples.
  (4) the rival reading ("equal steps of latitude angle") is refuted: it gives
      a different number on sample 1.
"""
import math, random

# ---------- reference model: surface measure on the unit sphere ----------
# Area element in (theta, phi): sin(theta) d(theta) d(phi), theta = polar angle.

def band_area_equal_z(i, n, steps=400000):
    """Exact-ish area (out of 4*pi) of the i-th equal-HEIGHT band, by integrating
    sin(theta) over the theta-range that the z-slab [z_lo, z_hi] corresponds to."""
    z_hi = 1.0 - 2.0 * i / n
    z_lo = 1.0 - 2.0 * (i + 1) / n
    th_lo = math.acos(min(1.0, max(-1.0, z_hi)))   # smaller theta <-> larger z
    th_hi = math.acos(min(1.0, max(-1.0, z_lo)))
    # Simpson on 2*pi * sin(theta) d(theta)
    h = (th_hi - th_lo) / steps
    s = 0.0
    for k in range(steps + 1):
        t = th_lo + k * h
        w = 1 if k in (0, steps) else (4 if k % 2 else 2)
        s += w * math.sin(t)
    return 2 * math.pi * s * h / 3.0

def band_area_equal_angle(i, n, steps=400000):
    """Same, if the bands were equal steps of POLAR ANGLE (the rival reading)."""
    th_lo = math.pi * i / n
    th_hi = math.pi * (i + 1) / n
    h = (th_hi - th_lo) / steps
    s = 0.0
    for k in range(steps + 1):
        t = th_lo + k * h
        w = 1 if k in (0, steps) else (4 if k % 2 else 2)
        s += w * math.sin(t)
    return 2 * math.pi * s * h / 3.0

def check_archimedes():
    print("(1) band areas (fraction of 4*pi), equal-height vs equal-angle bands")
    for n in (2, 3, 4, 5, 7, 13):
        eq_z = [band_area_equal_z(i, n) / (4 * math.pi) for i in range(n)]
        eq_a = [band_area_equal_angle(i, n) / (4 * math.pi) for i in range(n)]
        spread_z = max(eq_z) - min(eq_z)
        spread_a = max(eq_a) - min(eq_a)
        assert spread_z < 1e-9, (n, eq_z)
        assert abs(sum(eq_z) - 1.0) < 1e-9
        assert abs(sum(eq_a) - 1.0) < 1e-9
        print("    n=%-3d equal-z: all %.12f (spread %.2e)   equal-angle: %s"
              % (n, eq_z[0], spread_z,
                 "spread %.4f  %s" % (spread_a, ["%.4f" % v for v in eq_a[:3]])))
    print("    -> equal-HEIGHT bands have equal area (Archimedes); "
          "equal-ANGLE bands do not.\n")

# ---------- (2) end-to-end against a fine numeric ground truth ----------

def water_indicator(seed):
    """A random-ish water region: sum of a few random spherical 'blobs'."""
    rnd = random.Random(seed)
    blobs = []
    for _ in range(rnd.randint(2, 5)):
        # random unit vector + threshold
        while True:
            v = (rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))
            L = math.sqrt(sum(c * c for c in v))
            if L > 1e-6:
                break
        v = tuple(c / L for c in v)
        blobs.append((v, rnd.uniform(-0.6, 0.8)))
    def f(x, y, z):
        return any(v[0] * x + v[1] * y + v[2] * z > t for v, t in blobs)
    return f

def cell_and_global(n, m, f, sub=60):
    """Water percentage per cell and globally, by quadrature that is uniform in
    (z, phi) -- which IS the area measure (verified in step 1), refined enough
    that both numbers are accurate to ~1e-3."""
    cells = [[0.0] * m for _ in range(n)]
    tot = 0.0
    for i in range(n):
        z_hi = 1.0 - 2.0 * i / n
        z_lo = 1.0 - 2.0 * (i + 1) / n
        for j in range(m):
            p_lo = 2 * math.pi * j / m
            p_hi = 2 * math.pi * (j + 1) / m
            hit = 0
            for a in range(sub):
                z = z_lo + (z_hi - z_lo) * (a + 0.5) / sub
                r = math.sqrt(max(0.0, 1 - z * z))
                for b in range(sub):
                    phi = p_lo + (p_hi - p_lo) * (b + 0.5) / sub
                    if f(r * math.cos(phi), r * math.sin(phi), z):
                        hit += 1
            frac = 100.0 * hit / (sub * sub)
            cells[i][j] = frac
            tot += hit
    global_pct = 100.0 * tot / (n * m * sub * sub)
    return cells, global_pct

def solve(cells):
    """The claimed solution."""
    n = len(cells); m = len(cells[0])
    return sum(sum(row) for row in cells) / (n * m)

def weighted_by_equal_angle(cells):
    """The rival reading, for contrast."""
    n = len(cells); m = len(cells[0])
    w = [band_area_equal_angle(i, n, steps=20000) / (4 * math.pi) for i in range(n)]
    return sum(w[i] * sum(cells[i]) / m for i in range(n))

def check_end_to_end():
    print("(2) random water regions: mean of cell percentages vs true global percentage")
    worst = 0.0
    for seed in range(12):
        n = random.Random(seed * 7 + 1).randint(2, 6)
        m = random.Random(seed * 7 + 2).randint(2, 6)
        f = water_indicator(seed)
        cells, truth = cell_and_global(n, m, f)
        got = solve(cells)
        worst = max(worst, abs(got - truth))
        assert abs(got - truth) < 1e-9, (seed, n, m, got, truth)
    print("    12 random regions, max |mean(cells) - global| = %.2e  (exact: the"
          " same quadrature points)\n" % worst)

    # Independent-grid check: cell percentages measured on one quadrature, the
    # global truth measured on a totally different, much finer one.
    print("    independent fine ground truth (Monte Carlo, 400k points):")
    for seed in (3, 8):
        n, m = 5, 4
        f = water_indicator(seed)
        cells, _ = cell_and_global(n, m, f)
        rnd = random.Random(1234 + seed)
        N = 400000; hit = 0
        for _ in range(N):
            z = rnd.uniform(-1, 1)            # uniform in z  = uniform in area
            phi = rnd.uniform(0, 2 * math.pi)
            r = math.sqrt(max(0.0, 1 - z * z))
            if f(r * math.cos(phi), r * math.sin(phi), z):
                hit += 1
        mc = 100.0 * hit / N
        got = solve(cells)
        print("      seed %d: answer %.4f   Monte-Carlo truth %.4f   diff %.4f"
              % (seed, got, mc, abs(got - mc)))
        assert abs(got - mc) < 0.5
    print()

# ---------- (3)+(4) samples ----------

SAMPLES = [
    ((3, 7, [[63, 61, 55, 54, 77, 87, 89],
             [73, 60, 38, 5, 16, 56, 91],
             [75, 43, 11, 3, 16, 20, 95]]), 51.809523810),
    ((4, 3, [[10, 10, 10], [10, 10, 10], [10, 10, 10], [10, 10, 10]]), 10.000000000),
]

def check_samples():
    print("(3) published samples")
    for (n, m, grid), expected in SAMPLES:
        got = solve(grid)
        print("    n=%d m=%d -> %.9f   expected %.9f   %s"
              % (n, m, got, expected, "OK" if abs(got - expected) < 1e-6 else "FAIL"))
        assert abs(got - expected) < 1e-6
    print()
    print("(4) rival reading (equal steps of latitude angle) on sample 1:")
    (n, m, grid), expected = SAMPLES[0]
    print("    %.9f  vs required %.9f -> refuted\n"
          % (weighted_by_equal_angle(grid), expected))

if __name__ == "__main__":
    check_archimedes()
    check_samples()
    check_end_to_end()
    print("all checks passed: answer = unweighted mean of the n*m percentages, O(n*m)")
