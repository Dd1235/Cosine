"""kattis-edgeremoval -- 'Edge Removal' (ICPC Asia Can Tho 2020).

Remove the fewest edges from a connected weighted graph so the remaining graph
has EXACTLY ONE minimum spanning tree.

Claimed solution (Kruskal by weight class):
  Process weight classes in increasing order with a DSU holding all edges of
  strictly smaller weight.
    * an edge whose endpoints are already joined by strictly lighter edges is a
      "loop" edge: it is in no MST and can never break uniqueness -> KEEP it free.
    * among the remaining class-w edges (which join distinct contracted nodes),
      the MST takes a spanning forest; since all have equal weight, uniqueness
      forces that graph to already BE a forest -> keep a spanning forest of the
      class, REMOVE every class-w edge that closes a cycle inside its own class.
  Answer = m - (n-1) - L, where L = #loop edges.  (-1 if the graph is disconnected.)

Lower bound proof: in any kept set S that is connected with a unique MST, every
non-tree edge (u,v,w) must be strictly heavier than the whole tree path u..v
(otherwise swapping gives a second MST), so u,v are joined by edges of weight < w
in S and hence in the original graph -> that edge is a loop edge.  So
|S| <= (n-1) + L.  The construction attains it, and it keeps the exact same
Kruskal connectivity at every weight prefix, so each class is a forest -> unique.

Published solution (_tooling/solutions/edgeremoval.cpp) does exactly this: it
sorts the edges by weight, and inside each weight class first collects the
edges that still join two distinct DSU components ("goodEdges"), then unions
them one at a time, recording the index of every one that has meanwhile become
redundant.  Its removal count is therefore (#good edges) - (n-1) = m - L - (n-1),
the same number.  O(m log m) time, O(n + m) space; it also union-finds every
edge once up front to print -1 for a disconnected graph.  This script compiles
that file and compares it against the brute force as well.

Brute force: for k = 0,1,2,... try every subset of k edges to delete; a graph is
accepted iff it is connected and the number of minimum-weight spanning trees
(enumerated over all C(m, n-1) edge subsets) equals 1.
"""
import os
import random
import shutil
import subprocess
import sys
import tempfile
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
CPP = os.path.join(HERE, os.pardir, "_tooling", "solutions", "edgeremoval.cpp")

SHIM = """#pragma once
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <numeric>
#include <queue>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <utility>
#include <vector>
"""


def build(tmp):
    """Compile the published solution.  Two portability edits, neither of them
    touching the algorithm: bits/stdc++.h is shimmed, and `operator<` is made
    const (libc++ rejects the non-const member that libstdc++ accepts)."""
    cxx = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++")
    if cxx is None or not os.path.exists(CPP):
        return None
    os.makedirs(os.path.join(tmp, "bits"), exist_ok=True)
    with open(os.path.join(tmp, "bits", "stdc++.h"), "w") as f:
        f.write(SHIM)
    src = open(CPP).read().replace("bool operator < (const edges &A) {",
                                   "bool operator < (const edges &A) const {")
    path = os.path.join(tmp, "edgeremoval.cpp")
    with open(path, "w") as f:
        f.write(src)
    exe = os.path.join(tmp, "er")
    r = subprocess.run([cxx, "-O2", "-std=c++17", "-I", tmp, "-o", exe, path],
                       capture_output=True, text=True)
    if r.returncode:
        print("compile failed:\n" + r.stderr[:2000], file=sys.stderr)
        return None
    return exe


def run_cpp(exe, cases):
    """cases: list of (n, edges).  Returns list of None (-1) or removal lists."""
    lines = [str(len(cases))]
    for n, edges in cases:
        lines.append("%d %d" % (n, len(edges)))
        for (u, v, w) in edges:
            lines.append("%d %d %d" % (u + 1, v + 1, w))
    r = subprocess.run([exe], input="\n".join(lines) + "\n",
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    tok = r.stdout.split()
    out, i = [], 0
    for _ in cases:
        k = int(tok[i]); i += 1
        if k == -1:
            out.append(None)
            continue
        out.append([int(x) for x in tok[i:i + k]])
        i += k
    assert i == len(tok), "unparsed output"
    return out


# ---------------------------------------------------------------- solution
class DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        self.p[a] = b
        return True


def solve(n, edges):
    """edges: list of (u, v, w) 0-indexed vertices. Returns None if disconnected,
    else the list of 1-based indices of edges to remove."""
    order = sorted(range(len(edges)), key=lambda i: edges[i][2])
    dsu = DSU(n)
    removed = []
    i = 0
    while i < len(order):
        j = i
        w = edges[order[i]][2]
        while j < len(order) and edges[order[j]][2] == w:
            j += 1
        klass = order[i:j]
        local = DSU(n)          # only same-weight edges are unioned here
        pending = []
        for idx in klass:
            u, v, _ = edges[idx]
            ru, rv = dsu.find(u), dsu.find(v)
            if ru == rv:
                continue        # loop edge: free to keep
            if not local.union(ru, rv):
                removed.append(idx + 1)   # closes a cycle within its own class
            else:
                pending.append((u, v))
        for u, v in pending:
            dsu.union(u, v)
        i = j
    root = dsu.find(0)
    if any(dsu.find(x) != root for x in range(n)):
        return None
    return removed


def formula(n, m, edges):
    """m - (n-1) - L, independent recomputation of the count only."""
    order = sorted(range(m), key=lambda i: edges[i][2])
    dsu = DSU(n)
    loops = 0
    i = 0
    while i < m:
        j = i
        w = edges[order[i]][2]
        while j < m and edges[order[j]][2] == w:
            j += 1
        for idx in order[i:j]:
            u, v, _ = edges[idx]
            if dsu.find(u) == dsu.find(v):
                loops += 1
        for idx in order[i:j]:
            u, v, _ = edges[idx]
            dsu.union(u, v)
        i = j
    if len({dsu.find(x) for x in range(n)}) != 1:
        return None
    return m - (n - 1) - loops


# ---------------------------------------------------------------- brute force
def is_connected(n, es):
    if n == 1:
        return True
    adj = [[] for _ in range(n)]
    for u, v, _ in es:
        adj[u].append(v)
        adj[v].append(u)
    seen = {0}
    st = [0]
    while st:
        x = st.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                st.append(y)
    return len(seen) == n


def count_msts(n, es):
    """Number of minimum-weight spanning trees, by literal enumeration."""
    if n == 1:
        return 1
    best, cnt = None, 0
    for comb in combinations(range(len(es)), n - 1):
        sub = [es[i] for i in comb]
        d = DSU(n)
        ok = True
        for u, v, _ in sub:
            if not d.union(u, v):
                ok = False
                break
        if not ok:
            continue
        tot = sum(e[2] for e in sub)
        if best is None or tot < best:
            best, cnt = tot, 1
        elif tot == best:
            cnt += 1
    return cnt


def good(n, es):
    return is_connected(n, es) and count_msts(n, es) == 1


def brute(n, edges):
    m = len(edges)
    if not is_connected(n, edges):
        return None
    for k in range(m + 1):
        for rem in combinations(range(m), k):
            keep = [edges[i] for i in range(m) if i not in rem]
            if good(n, keep):
                return k
    raise AssertionError("unreachable: empty-ish graph always terminates")


# ---------------------------------------------------------------- sample
def check_sample(exe):
    edges = [(1, 6, 1), (1, 2, 2), (4, 5, 3), (3, 4, 4), (5, 6, 5), (2, 3, 5),
             (0, 6, 6), (0, 1, 9), (0, 2, 9), (0, 3, 9), (0, 4, 9), (0, 5, 9)]
    rem = solve(7, edges)
    assert rem is not None and len(rem) == 1, rem
    assert formula(7, 12, edges) == 1
    keep = [edges[i] for i in range(12) if (i + 1) not in rem]
    assert good(7, keep), "constructed removal does not give a unique MST"
    msg = ""
    if exe:
        (cr,) = run_cpp(exe, [(7, edges)])
        assert cr is not None and len(cr) == 1, cr
        ck = [edges[i] for i in range(12) if (i + 1) not in cr]
        assert good(7, ck), "C++ removal does not give a unique MST"
        msg = "; published C++ emits k=1 removing %s" % cr
    print("sample: k=1 removing edge index", rem,
          "(judge prints 2, any optimal set is accepted)" + msg)


# ---------------------------------------------------------------- random tests
def rand_test(exe, trials=400, seed=7):
    rng = random.Random(seed)
    checked = disc = 0
    cases = []
    for _ in range(trials):
        n = rng.randint(1, 6)
        allp = [(u, v) for u in range(n) for v in range(u + 1, n)]
        rng.shuffle(allp)
        m = rng.randint(0, min(len(allp), 8))
        maxw = rng.choice([1, 2, 3, 5])
        edges = [(u, v, rng.randint(0, maxw)) for u, v in allp[:m]]
        got = solve(n, edges)
        f = formula(n, len(edges), edges)
        exp = brute(n, edges)
        if exp is None:
            assert got is None and f is None, (n, edges, got, f)
            disc += 1
            continue
        assert got is not None, (n, edges)
        assert len(got) == exp, ("count mismatch", n, edges, len(got), exp)
        assert f == exp, ("formula mismatch", n, edges, f, exp)
        keep = [edges[i] for i in range(len(edges)) if (i + 1) not in got]
        assert good(n, keep), ("removal set invalid", n, edges, got)
        cases.append(((n, edges), exp))
        checked += 1
    print(f"random: {checked} connected cases matched brute force "
          f"(count AND validity of the emitted set), {disc} disconnected -> -1")
    if exe:
        outs = run_cpp(exe, [c for c, _ in cases])
        for ((n, edges), exp), cr in zip(cases, outs):
            assert cr is not None and len(cr) == exp, \
                ("cpp count mismatch", n, edges, cr, exp)
            keep = [edges[i] for i in range(len(edges)) if (i + 1) not in cr]
            assert good(n, keep), ("cpp removal set invalid", n, edges, cr)
        print(f"        published C++ agrees on all {len(cases)} of them "
              f"(count optimal AND its own removal set verified)")


def check_limits(exe):
    """Sum n = 2e5, sum m = 3e5 with every weight equal -- the worst case for
    the per-class scan -- must stay fast."""
    if not exe:
        return
    import time
    rng = random.Random(4)
    n, m = 200000, 300000
    edges = [(rng.randrange(v), v, 7) for v in range(1, n)]
    seen = {(u, v) for u, v, _ in edges}
    while len(edges) < m:
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v and (min(u, v), max(u, v)) not in seen:
            seen.add((min(u, v), max(u, v)))
            edges.append((u, v, 7))
    t0 = time.time()
    (out,) = run_cpp(exe, [(n, edges)])
    assert len(out) == len(edges) - (n - 1), (len(out), len(edges) - (n - 1))
    print("limits: n=2e5, m=3e5, all weights equal -> k=%d in %.2fs"
          % (len(out), time.time() - t0))


if __name__ == "__main__":
    tmp = tempfile.mkdtemp()
    exe = build(tmp)
    if exe is None:
        print("WARNING: no C++ compiler; only the Python transcription is checked")
    check_sample(exe)
    rand_test(exe)
    rand_test(exe, trials=250, seed=99)
    check_limits(exe)
    print("OK")
