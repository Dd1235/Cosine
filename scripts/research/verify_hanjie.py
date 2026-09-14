#!/usr/bin/env python3
"""Verify kattis-hanjie (2019 ICPC Asia Danang, "Hanjie").

Counts the nonogram solutions of an r x c board (r, c <= 6) given a run-length
clue for every row and every column.

Three implementations are compared:
  1. published(...)    -- transcription of the published C++ backtracking:
                          place each row's blocks left to right, and when all r
                          rows are laid down, check the column clues.
  2. brute_grids(...)  -- enumerate all 2^(r*c) black/white grids and test BOTH
                          the row and the column clues from scratch.  Only
                          affordable for r*c <= 16, but it shares nothing with
                          (1): it never assumes a row is valid by construction.
  3. row_product(...)  -- enumerate, per row, every length-c bit pattern whose
                          run lengths equal that row's clue, take the Cartesian
                          product over rows and test the columns.  Reaches 6x6.

Optionally the real compiled binary is driven as well:
    python3 verify_hanjie.py /path/to/hanjie_binary
(built with `g++ -O2 -std=c++17 hanjie.cpp`).  Without it the transcription is
still compared against (2) and (3).

The interesting part is a near-miss in the published code.  Its inner loop bound
`next_Y < c - Lm` does NOT keep the block being placed inside the board: with a
single remaining block of length a it lets next_Y run to c-1, writing black
cells past column c-1 into the oversized global array.  Those states are killed
one level up by `if (y > c + 1) return;`, since y = next_Y + a + 1 exceeds c + 1
exactly when the block overflowed, so Check() is never reached from them.  The
random clue tests below are built to hit that path (block lengths > 1 pressed
against the right edge, plus clue sets with zero solutions).
"""
import itertools
import random
import subprocess
import sys


# ---------------------------------------------------------------- utilities
def runs(bits):
    """Run lengths of the 1s in a tuple/list of 0/1, left to right."""
    out, cur = [], 0
    for b in bits:
        if b:
            cur += 1
        elif cur:
            out.append(cur)
            cur = 0
    if cur:
        out.append(cur)
    return out


def legal_clues(n):
    """Every clue that the statement permits for a line of length n:
    positive a_1..a_k with sum(a) + k - 1 <= n (k = 0 allowed)."""
    out = [[]]
    def rec(pref, used):
        for v in range(1, n + 1):
            need = used + v + (1 if pref else 0)
            if need > n:
                break
            nxt = pref + [v]
            out.append(nxt)
            rec(nxt, need)
    rec([], 0)
    return out


# ------------------------------------------------- 1. published transcription
def published(r, c, row_clues, col_clues):
    """Literal transcription of the published C++ (variable names kept)."""
    a = [list(x) for x in row_clues]
    b = [list(x) for x in col_clues]
    S = []
    for i in range(r):
        pref, acc = [], 0
        for v in a[i]:
            acc += v
            pref.append(acc)
        S.append(pref)
    vl = [[0] * 30 for _ in range(30)]        # oversized, exactly as in the C++
    res = 0

    def check():
        nonlocal res
        ok = True
        for i in range(c):
            vc, j = [], 0
            while j < r:
                k = j
                while k < r and vl[k][i] == vl[j][i]:
                    k += 1
                if vl[j][i] == 1:
                    vc.append(k - j)
                j = k
            if vc != b[i]:
                ok = False
                break
        res += ok

    def vet(x, y, idx):
        if x == r:
            check()
            return
        if idx == len(a[x]):
            if y > c + 1:
                return
            vet(x + 1, 0, 0)
            return
        tong = S[x][len(a[x]) - 1] - (0 if idx == 0 else S[x][idx - 1])
        ln = len(a[x]) - idx
        if y + tong - (ln - 1) - 1 >= c:
            return
        lm = (tong - a[x][idx]) + max(0, ln - 2)
        next_y = y
        lm_y = c - lm
        while next_y < lm_y:
            for p in range(next_y, next_y + a[x][idx]):
                vl[x][p] = 1
            vet(x, next_y + a[x][idx] + 1, idx + 1)
            for p in range(next_y, next_y + a[x][idx]):
                vl[x][p] = 0
            next_y += 1

    vet(0, 0, 0)
    return res


# --------------------------------------------------- 2. exhaustive over grids
def brute_grids(r, c, row_clues, col_clues):
    """All 2^(r*c) colourings; both row and column clues rechecked."""
    rc = [list(x) for x in row_clues]
    cc = [list(x) for x in col_clues]
    total = 0
    for mask in range(1 << (r * c)):
        g = [[(mask >> (i * c + j)) & 1 for j in range(c)] for i in range(r)]
        if any(runs(g[i]) != rc[i] for i in range(r)):
            continue
        if any(runs([g[i][j] for i in range(r)]) != cc[j] for j in range(c)):
            continue
        total += 1
    return total


# ------------------------------------------------ 3. per-row patterns product
def patterns_for(clue, n):
    want = list(clue)
    return [p for p in itertools.product((0, 1), repeat=n) if runs(p) == want]


def row_product(r, c, row_clues, col_clues):
    cc = [list(x) for x in col_clues]
    per_row = [patterns_for(row_clues[i], c) for i in range(r)]
    if any(not p for p in per_row):
        return 0
    total = 0
    for combo in itertools.product(*per_row):
        if all(runs([combo[i][j] for i in range(r)]) == cc[j] for j in range(c)):
            total += 1
    return total


# ------------------------------------------------------------ the real binary
def run_binary(path, cases):
    outs = []
    for r, c, rc, cc in cases:
        lines = ["%d %d" % (r, c)]
        for cl in rc:
            lines.append(" ".join(str(x) for x in [len(cl)] + list(cl)))
        for cl in cc:
            lines.append(" ".join(str(x) for x in [len(cl)] + list(cl)))
        res = subprocess.run([path], input="\n".join(lines) + "\n",
                             capture_output=True, text=True)
        outs.append(int(res.stdout.split()[0]))
    return outs


def main():
    binary = sys.argv[1] if len(sys.argv) > 1 else None

    print("== sample ==")
    case = (2, 2, [[1], [1]], [[1], [1]])
    got = published(*case)
    print("2x2 all-ones clues ->", got, "(expected 2)", "OK" if got == 2 else "MISMATCH")
    assert got == 2
    if binary:
        assert run_binary(binary, [case]) == [2]
        print("compiled binary agrees on the sample")

    print("\n== exhaustive: every legal clue set on small boards ==")
    for r, c in [(1, 1), (1, 2), (2, 1), (1, 3), (3, 1), (2, 2), (2, 3), (3, 2)]:
        rcl, ccl = legal_clues(c), legal_clues(r)
        n = 0
        for rows in itertools.product(rcl, repeat=r):
            for cols in itertools.product(ccl, repeat=c):
                p = published(r, c, rows, cols)
                g = brute_grids(r, c, rows, cols)
                assert p == g, (r, c, rows, cols, p, g)
                n += 1
        print(f"r={r} c={c}: {n} clue sets, published == brute force")

    print("\n== exhaustive 3x3 (sampled clue sets) vs 2^(r*c) brute force ==")
    random.seed(17)
    rcl, ccl = legal_clues(3), legal_clues(3)
    for _ in range(3000):
        rows = [random.choice(rcl) for _ in range(3)]
        cols = [random.choice(ccl) for _ in range(3)]
        p = published(3, 3, rows, cols)
        g = brute_grids(3, 3, rows, cols)
        assert p == g, (rows, cols, p, g)
    print("3000 random 3x3 clue sets, published == brute force")

    print("\n== 4x4 vs 2^(r*c) brute force ==")
    for r, c in [(4, 4), (2, 6), (6, 2)]:
        rcl, ccl = legal_clues(c), legal_clues(r)
        for _ in range(40):
            rows = [random.choice(rcl) for _ in range(r)]
            cols = [random.choice(ccl) for _ in range(c)]
            p = published(r, c, rows, cols)
            g = brute_grids(r, c, rows, cols)
            assert p == g, (r, c, rows, cols, p, g)
        print(f"r={r} c={c}: 40 random clue sets OK")

    print("\n== up to 6x6 vs the row-pattern product ==")
    cases = []
    for _ in range(400):
        r = random.randint(1, 6)
        c = random.randint(1, 6)
        rcl, ccl = legal_clues(c), legal_clues(r)
        rows = [random.choice(rcl) for _ in range(r)]
        cols = [random.choice(ccl) for _ in range(c)]
        cases.append((r, c, rows, cols))
    # plus clue sets drawn from real grids, so many have solutions
    for _ in range(200):
        r = random.randint(1, 6)
        c = random.randint(1, 6)
        g = [[random.randint(0, 1) for _ in range(c)] for _ in range(r)]
        rows = [runs(g[i]) for i in range(r)]
        cols = [runs([g[i][j] for i in range(r)]) for j in range(c)]
        cases.append((r, c, rows, cols))
    # plus blocks pressed against the right edge, the near-miss path
    for _ in range(200):
        c = 6
        r = random.randint(1, 6)
        rows = [random.choice([[2], [3], [4], [5], [6], [2, 2], [3, 2]]) for _ in range(r)]
        cols = [random.choice(legal_clues(r)) for _ in range(c)]
        cases.append((r, c, rows, cols))
    nonzero = 0
    for (r, c, rows, cols) in cases:
        p = published(r, c, rows, cols)
        q = row_product(r, c, rows, cols)
        assert p == q, (r, c, rows, cols, p, q)
        nonzero += p > 0
    print(f"{len(cases)} clue sets up to 6x6 OK ({nonzero} with at least one solution)")

    if binary:
        print("\n== compiled binary vs transcription ==")
        outs = run_binary(binary, cases)
        mine = [published(*x) for x in cases]
        assert outs == mine, next((x for x in zip(cases, outs, mine) if x[1] != x[2]))
        print(f"{len(cases)} cases: compiled binary == transcription")

        print("\n== worst case for the limits (6x6, every clue 1 1) ==")
        import time
        worst = (6, 6, [[1, 1]] * 6, [[1, 1]] * 6)
        t0 = time.time()
        out = run_binary(binary, [worst])
        print("answer", out[0], "in %.3fs" % (time.time() - t0))
        for cl in ([1, 1], [1], [2], [1, 1, 1], []):
            w = (6, 6, [list(cl)] * 6, [list(cl)] * 6)
            t0 = time.time()
            out = run_binary(binary, [w])
            print(f"  clue {cl or '(empty)'}: answer {out[0]} in %.3fs" % (time.time() - t0))

    print("\nall checks passed")


if __name__ == "__main__":
    sys.exit(main())
