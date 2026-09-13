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

The published C++ does not use that closed form: for each of the 24 hours it
solves 5.5*m - 30*(h mod 12) == +-alpha for the minute offset m, by cases on the
hour, keeping m as the exact rational TS/11 (integer part `M`, remainder `Thua`)
and rejecting m >= 60.  A candidate at minute `vl` with remainder `Thua` counts
when T1 <= vl <= T2, except that on vl == T2 it counts only if Thua == 0 --
which is right, because a nonzero remainder puts the instant strictly after the
last whole minute of the window.  published_count() below is a transcription of
that, and it is compared against solve() on all 3,112,560 (T1, T2, alpha)
windows.  Pass the compiled binary to check the transcription itself:
    python3 verify_datingtime.py /path/to/datingtime_binary

solve() is checked against a brute force that walks the whole [T1, T2] window on a fine
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


def published_candidates(k):
    """Transcription of the published C++: the (vl, Thua) instants it
    manufactures for angle k, independent of the query window."""
    out = []
    for i in range(24):
        x = i % 12
        if k == 0:
            if x == 11:
                continue
            out.append((i * 60 + 60 * x // 11, 60 * x % 11))
        elif k == 90:
            if x <= 2:
                cands = [2 * (30 * x + 90), 2 * (30 * x + 270)]
            elif x <= 8:
                cands = [2 * (30 * x + 90), 2 * (30 * x - 90)]
            else:
                cands = [2 * (30 * x - 90), 2 * (30 * x - 270)]
            for TS in cands:
                if TS // 11 < 60:
                    out.append((i * 60 + TS // 11 % 60, TS % 11))
        elif k == 180:
            TS = 2 * (30 * x + 180) if x <= 5 else 2 * (30 * x - 180)
            if TS // 11 < 60:
                out.append((i * 60 + TS // 11 % 60, TS % 11))
    return out


CANDIDATES = {a: published_candidates(a) for a in (0, 90, 180)}


def published_count(T1, T2, k):
    total = 0
    for vl, thua in CANDIDATES[k]:
        if vl == T2:
            total += thua == 0
        else:
            total += T1 <= vl <= T2
    return total


def run_binary(path, cases):
    import subprocess
    lines = [str(len(cases))]
    for T1, T2, a in cases:
        lines.append("%02d:%02d %02d:%02d %d" % (T1 // 60, T1 % 60, T2 // 60, T2 % 60, a))
    res = subprocess.run([path], input="\n".join(lines) + "\n",
                         capture_output=True, text=True)
    return [int(v) for v in res.stdout.split()]


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

    print("\n== published C++ transcription vs the lattice model, EVERY window ==")
    bad = 0
    for a in (0, 90, 180):
        for T1 in range(1440):
            for T2 in range(T1, 1440):
                if published_count(T1, T2, a) != solve(T1, T2, a):
                    bad += 1
                    if bad < 5:
                        print("MISMATCH", T1, T2, a)
    print("3112560 windows, mismatches:", bad)
    assert bad == 0

    if len(sys.argv) > 1:
        print("\n== compiled binary vs transcription ==")
        cases = [(0, 1439, 0), (0, 1439, 90), (0, 1439, 180), (1080, 1081, 180)]
        for _ in range(4000):
            T1 = random.randint(0, 1439)
            T2 = random.randint(T1, 1439)
            cases.append((T1, T2, random.choice((0, 90, 180))))
        got = run_binary(sys.argv[1], cases)
        want = [published_count(*c) for c in cases]
        assert got == want, next(x for x in zip(cases, got, want) if x[1] != x[2])
        print(f"{len(cases)} cases: compiled binary == transcription == lattice model")

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
