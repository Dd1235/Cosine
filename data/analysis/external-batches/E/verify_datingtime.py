#!/usr/bin/env python3
"""Verify kattis-datingtime (2019 ICPC Asia Danang, "Dating time").

Model: let t be minutes after 00:00 (a real number, 0 <= t <= 1439).
  minute hand angle = 6t deg (mod 360), hour hand angle = 0.5t deg (mod 360)
  signed separation  = 5.5t (mod 360); the reported angle is
  min(sep, 360 - sep), so the condition "angle == alpha" is
      5.5 t == alpha (mod 360)   or   5.5 t == -alpha (mod 360).
Multiplying by 2 and writing u = 11t:
      u == 2*alpha (mod 720)     or   u == -2*alpha (mod 720),
so every solution has 11t integral and the answer is just a count of lattice
points in an interval: for each residue r in {2a mod 720, -2a mod 720} count
integers k with 11*T1 <= r + 720k <= 11*T2.  O(1) per test case.

Checked against a brute force that walks the whole [T1, T2] window on a fine
rational grid (step 1/110 minute -- the angle function is piecewise linear with
breakpoints only at multiples of 1/11 minute, so the grid cannot miss a
solution) and tests the angle exactly with Fraction arithmetic.
"""
import random
import sys
from fractions import Fraction

GRID = 110  # sub-minute steps; a multiple of 11


def solve(T1, T2, alpha):
    """Closed-form count of instants in [T1, T2] minutes with hand angle alpha."""
    residues = {(2 * alpha) % 720, (-2 * alpha) % 720}
    lo, hi = 11 * T1, 11 * T2
    total = 0
    for r in residues:
        # count k with lo <= r + 720k <= hi
        kmin = -((r - lo) // 720)          # ceil((lo - r)/720)
        kmax = (hi - r) // 720
        if kmax >= kmin:
            total += kmax - kmin + 1
    return total


def brute(T1, T2, alpha):
    """Scan every t = n/GRID in [T1, T2] and test the angle exactly."""
    cnt = 0
    for n in range(T1 * GRID, T2 * GRID + 1):
        t = Fraction(n, GRID)
        sep = (Fraction(11, 2) * t) % 360
        ang = min(sep, 360 - sep)
        if ang == alpha:
            cnt += 1
    return cnt


def brute_finer(T1, T2, alpha, grid):
    cnt = 0
    for n in range(T1 * grid, T2 * grid + 1):
        t = Fraction(n, grid)
        sep = (Fraction(11, 2) * t) % 360
        if min(sep, 360 - sep) == alpha:
            cnt += 1
    return cnt


def main():
    print("== sample ==")
    samples = [((0, 0), (23, 59), 0, 22),
               ((0, 0), (23, 59), 90, 44),
               ((18, 0), (18, 1), 180, 1)]
    for (h1, m1), (h2, m2), a, want in samples:
        got = solve(h1 * 60 + m1, h2 * 60 + m2, a)
        print(f"{h1:02d}:{m1:02d} {h2:02d}:{m2:02d} {a} -> {got} (expected {want})"
              f" {'OK' if got == want else 'MISMATCH'}")
        assert got == want

    print("\n== full-day brute force on every alpha ==")
    for a in (0, 90, 180):
        b = brute(0, 1439, a)
        s = solve(0, 1439, a)
        print(f"alpha={a} brute={b} solve={s} {'OK' if b == s else 'MISMATCH'}")
        assert b == s

    print("\n== exhaustive over EVERY minute window of the full day ==")
    # Same brute force, but the grid is walked once per alpha and the hits are
    # turned into a prefix count so that all 1440*1441/2 windows are affordable.
    bad = 0
    checked = 0
    for a in (0, 90, 180):
        hit = [0] * (1439 * GRID + 2)
        for n in range(0, 1439 * GRID + 1):
            t = Fraction(n, GRID)
            sep = (Fraction(11, 2) * t) % 360
            hit[n] = 1 if min(sep, 360 - sep) == a else 0
        pref = [0] * (len(hit) + 1)
        for n, x in enumerate(hit):
            pref[n + 1] = pref[n] + x
        for T1 in range(0, 1440):
            for T2 in range(T1, 1440):
                want = pref[T2 * GRID + 1] - pref[T1 * GRID]
                if want != solve(T1, T2, a):
                    bad += 1
                    if bad < 5:
                        print("MISMATCH", T1, T2, a, want, solve(T1, T2, a))
                checked += 1
    print("windows checked:", checked, "mismatches:", bad)
    assert bad == 0

    print("\n== random windows over the whole day ==")
    random.seed(11)
    for _ in range(300):
        T1 = random.randint(0, 1439)
        T2 = random.randint(T1, 1439)
        a = random.choice((0, 90, 180))
        b, s = brute(T1, T2, a), solve(T1, T2, a)
        assert b == s, (T1, T2, a, b, s)
    print("300 random windows OK")

    print("\n== denser grid (step 1/330 min) cannot find extra solutions ==")
    for _ in range(20):
        T1 = random.randint(0, 1400)
        T2 = min(1439, T1 + random.randint(0, 40))
        a = random.choice((0, 90, 180))
        b, s = brute_finer(T1, T2, a, 330), solve(T1, T2, a)
        assert b == s, (T1, T2, a, b, s)
    print("20 dense-grid windows OK")

    print("\nall checks passed")


if __name__ == "__main__":
    sys.exit(main())
