#!/usr/bin/env python3
"""Verification for kattis-beautifulsquare (2020 ICPC Asia Can Tho, problem B).

The published solution
(_tooling/solutions/beautifulsquare.cpp, sha256 92489fe7...) is a case-analysis
constructor for a Hamiltonian path in the n x n grid graph that starts at (r,c).
This script checks three independent things:

  1. ORACLE.  For n <= 4, exhaustive DFS decides, for every start cell, whether a
     Hamiltonian path exists at all.  That oracle is compared with the parity
     rule the solution uses ("NO iff n is odd and r+c is odd"), so the rule is
     not taken on faith.
  2. FEASIBILITY.  For every (n,r,c) tested, the answer printed by the binary
     must agree with the parity rule.
  3. OUTPUT VALIDITY.  Every grid printed after a YES must be a permutation of
     1..n*n, must place 1 at (r,c), and consecutive integers must sit in
     edge-adjacent cells.

Usage:  python3 verify_beautifulsquare.py [path-to-compiled-binary]
The binary argument is optional: with none, the script builds the recorded
solution source itself and cleans up after.
The binary is built from beautifulsquare.cpp (g++ -O2 -std=c++17).
"""
import random
import subprocess
import sys

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
BIN = _build("beautifulsquare")


# ---------------------------------------------------------------- oracle ----
def hamiltonian_exists(n, r, c):
    """Exhaustive search for a Hamiltonian path in the n x n grid from (r,c)."""
    total = n * n
    seen = [[False] * (n + 2) for _ in range(n + 2)]
    sys.setrecursionlimit(10000)

    def dfs(x, y, k):
        if k == total:
            return True
        seen[x][y] = True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            u, v = x + dx, y + dy
            if 1 <= u <= n and 1 <= v <= n and not seen[u][v]:
                if dfs(u, v, k + 1):
                    seen[x][y] = False
                    return True
        seen[x][y] = False
        return False

    return dfs(r, c, 1)


def parity_rule(n, r, c):
    """What the published solution answers: NO only when n and r+c are both odd."""
    return not (n % 2 == 1 and (r + c) % 2 == 1)


# ------------------------------------------------------------ run + check ----
def run(cases):
    inp = ["%d" % len(cases)] + ["%d %d %d" % t for t in cases]
    out = subprocess.run(
        [BIN], input="\n".join(inp) + "\n", capture_output=True, text=True, timeout=600
    )
    if out.returncode != 0:
        raise SystemExit("binary failed (rc=%d): %s" % (out.returncode, out.stderr[-400:]))
    return out.stdout.split("\n")


def check(cases, lines):
    pos = 0
    for (n, r, c) in cases:
        verdict = lines[pos].strip()
        pos += 1
        want_yes = parity_rule(n, r, c)
        if verdict not in ("YES", "NO"):
            raise SystemExit("bad verdict %r for %s" % (verdict, (n, r, c)))
        if (verdict == "YES") != want_yes:
            raise SystemExit("verdict %s contradicts parity rule for %s" % (verdict, (n, r, c)))
        if verdict == "NO":
            continue
        grid = []
        for _ in range(n):
            row = list(map(int, lines[pos].split()))
            pos += 1
            if len(row) != n:
                raise SystemExit("row of length %d, expected %d, for %s" % (len(row), n, (n, r, c)))
            grid.append(row)
        # permutation of 1..n*n
        flat = sorted(v for row in grid for v in row)
        if flat != list(range(1, n * n + 1)):
            raise SystemExit("not a permutation of 1..n^2 for %s" % ((n, r, c),))
        # 1 sits at (r,c)
        if grid[r - 1][c - 1] != 1:
            raise SystemExit("1 is not at (%d,%d) for %s" % (r, c, (n, r, c)))
        # consecutive integers are edge-adjacent
        where = [None] * (n * n + 1)
        for i in range(n):
            for j in range(n):
                where[grid[i][j]] = (i, j)
        for v in range(1, n * n):
            (x1, y1), (x2, y2) = where[v], where[v + 1]
            if abs(x1 - x2) + abs(y1 - y2) != 1:
                raise SystemExit("%d and %d are not adjacent for %s" % (v, v + 1, (n, r, c)))


def main():
    # 1. oracle vs parity rule, exhaustively for n <= 4
    for n in range(1, 5):
        for r in range(1, n + 1):
            for c in range(1, n + 1):
                got = hamiltonian_exists(n, r, c)
                want = parity_rule(n, r, c)
                if got != want:
                    raise SystemExit(
                        "oracle disagrees with parity rule at n=%d r=%d c=%d: "
                        "exhaustive=%s rule=%s" % (n, r, c, got, want)
                    )
    print("oracle: exhaustive Hamiltonian-path search for n<=4 matches the parity rule")

    # 2+3. the binary, exhaustively over every start cell for n = 1..40
    cases = [(n, r, c) for n in range(1, 41) for r in range(1, n + 1) for c in range(1, n + 1)]
    for i in range(0, len(cases), 100):            # t <= 100 per the statement
        chunk = cases[i:i + 100]
        check(chunk, run(chunk))
    print("exhaustive: n=1..40, every (r,c)  -> %d cases OK" % len(cases))

    # the maximum-size cases, exhaustively
    for n in (99, 100):
        cases = [(n, r, c) for r in range(1, n + 1) for c in range(1, n + 1)]
        for i in range(0, len(cases), 100):
            chunk = cases[i:i + 100]
            check(chunk, run(chunk))
        print("exhaustive: n=%d, every (r,c) -> %d cases OK" % (n, n * n))

    # random spread over the whole range, batched exactly as the judge would
    rng = random.Random(20201212)
    for _ in range(40):
        chunk = []
        for _ in range(100):
            n = rng.randint(1, 100)
            chunk.append((n, rng.randint(1, n), rng.randint(1, n)))
        check(chunk, run(chunk))
    print("random: 4000 cases over 1<=n<=100 OK")

    # the statement's own sample
    check([(4, 1, 1), (5, 1, 2)], run([(4, 1, 1), (5, 1, 2)]))
    print("sample 1 OK")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
