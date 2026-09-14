#!/usr/bin/env python3
"""Verify kattis-abstractpainting (2019 ICPC Asia Danang, "Abstract Painting").

Claim: the number of good paintings of an R x C grid of unit squares is
    3^(R+C) * 2^(R*C)   (mod 1e9+7)

Four implementations are compared:
  1. closed_form(R, C)              -- the claimed answer, O(log) per test
  2. brute(R, C)                    -- enumerate all 3^(#edges) colourings
  3. column_dp(R, C)                -- profile DP over the 3^R vertical boundary
  4. published(R, C)                -- transcription of the published C++, which
                                       multiplies by 3 (R+C) times and by 2
                                       (R*C) times, i.e. the same closed form
                                       written without fast exponentiation

Optionally the real compiled binary is driven too:
    python3 verify_abstractpainting.py /path/to/abstractpainting_binary

Edge indexing: h[i][j] is the horizontal edge on grid line i (0..R) above square
(i, j); v[i][j] is the vertical edge on grid line j (0..C) left of square (i, j).
Square (i, j) has edges h[i][j], h[i+1][j], v[i][j], v[i][j+1].
A square is good iff its four edge colours are {x,x,y,y} with x != y.
"""
import itertools
import random
import sys

MOD = 10**9 + 7


def good(a, b, c, d):
    """Exactly two colours, each used exactly twice."""
    vals = sorted((a, b, c, d))
    return vals[0] == vals[1] and vals[2] == vals[3] and vals[1] != vals[2]


def closed_form(R, C, mod=MOD):
    return pow(3, R + C, mod) * pow(2, R * C, mod) % mod


def published(R, C, mod=MOD):
    """Literal transcription of the published C++ solve()."""
    res = 1
    for _ in range(R + C):
        res = res * 3 % mod
    for _ in range(R * C):
        res = res * 2 % mod
    return res


def run_binary(path, cases):
    import subprocess
    out = []
    for i in range(0, len(cases), 5):          # T <= 5 per the statement
        chunk = cases[i:i + 5]
        inp = str(len(chunk)) + "\n" + "\n".join("%d %d" % rc for rc in chunk) + "\n"
        res = subprocess.run([path], input=inp, capture_output=True, text=True)
        out += [int(v) for v in res.stdout.split()]
    return out


def brute(R, C):
    """Exhaustive over every edge colouring. Only for tiny R, C."""
    nh = (R + 1) * C
    nv = R * (C + 1)
    total = 0
    for assign in itertools.product(range(3), repeat=nh + nv):
        h = assign[:nh]
        v = assign[nh:]
        ok = True
        for i in range(R):
            for j in range(C):
                if not good(h[i * C + j], h[(i + 1) * C + j],
                            v[i * (C + 1) + j], v[i * (C + 1) + j + 1]):
                    ok = False
                    break
            if not ok:
                break
        total += ok
    return total


def column_ways(R, left):
    """All (right-boundary tuple) outcomes for one column of R squares given the
    left vertical boundary colours `left`.  Enumerates the column's horizontal
    edges and right vertical edges exhaustively (3^(R+1) * 3^R) -- independent of
    the case analysis used by the closed form."""
    out = {}
    for hs in itertools.product(range(3), repeat=R + 1):
        for rs in itertools.product(range(3), repeat=R):
            if all(good(hs[i], hs[i + 1], left[i], rs[i]) for i in range(R)):
                out[rs] = out.get(rs, 0) + 1
    return out


def column_dp(R, C):
    """DP over columns with state = colours of the vertical boundary."""
    states = list(itertools.product(range(3), repeat=R))
    trans = {s: column_ways(R, s) for s in states}
    cur = {s: 1 for s in states}          # first boundary is free
    for _ in range(C):
        nxt = {}
        for s, w in cur.items():
            for t, k in trans[s].items():
                nxt[t] = nxt.get(t, 0) + w * k
        cur = nxt
    return sum(cur.values())


def main():
    print("== samples ==")
    for (R, C), want in [((1, 1), 18), ((1, 2), 108), ((2, 1), 108)]:
        got = closed_form(R, C)
        print(f"R={R} C={C} closed={got} expected={want} {'OK' if got == want else 'MISMATCH'}")
        assert got == want

    print("\n== exhaustive brute force vs closed form ==")
    for R, C in [(1, 1), (1, 2), (2, 1), (2, 2), (1, 3), (3, 1)]:
        b = brute(R, C)
        c = closed_form(R, C, mod=10**30)
        print(f"R={R} C={C} brute={b} closed={c} {'OK' if b == c else 'MISMATCH'}")
        assert b == c, (R, C, b, c)

    print("\n== profile DP vs closed form ==")
    for R in range(1, 5):
        for C in range(1, 5):
            d = column_dp(R, C)
            c = closed_form(R, C, mod=10**30)
            assert d == c, (R, C, d, c)
            print(f"R={R} C={C} dp={d} closed={c} OK")

    print("\n== random spot checks, DP vs closed form ==")
    random.seed(7)
    for _ in range(6):
        R = random.randint(1, 5)
        C = random.randint(1, 7)
        d = column_dp(R, C) % MOD
        c = closed_form(R, C)
        assert d == c, (R, C, d, c)
        print(f"R={R} C={C} dp={d} closed={c} OK")

    print("\n== published C++ transcription vs closed form ==")
    for R in range(1, 15):
        for C in list(range(1, 13)) + [1999, 2000]:
            assert published(R, C) == closed_form(R, C), (R, C)
    print("all R in 1..14 x C in 1..12, 1999, 2000 agree")

    if len(sys.argv) > 1:
        print("\n== compiled binary vs closed form ==")
        cases = [(R, C) for R in range(1, 15) for C in list(range(1, 13)) + [1999, 2000]]
        random.seed(23)
        cases += [(random.randint(1, 14), random.randint(1, 2000)) for _ in range(200)]
        got = run_binary(sys.argv[1], cases)
        want = [closed_form(R, C) for R, C in cases]
        assert got == want, next(x for x in zip(cases, got, want) if x[1] != x[2])
        print(f"{len(cases)} cases: compiled binary == 3^(R+C) * 2^(R*C) mod 1e9+7")

    print("\n== limits ==")
    print("R=14 C=2000 ->", closed_form(14, 2000))
    print("all checks passed")


if __name__ == "__main__":
    sys.exit(main())
