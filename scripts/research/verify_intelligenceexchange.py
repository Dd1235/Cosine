"""kattis-intelligenceexchange -- 'Intelligence Exchange' (ICPC Asia Can Tho 2020).

Carmen walks hc -> sc and Juni walks hj -> sj on an undirected weighted graph,
both leaving at t=0, both at unit speed, each free to pick ANY of their own
shortest paths, and both waiting forever once they arrive.  Count the distinct
LOCATIONS (points of the metric graph -- vertices or interior points of edges)
at which the two can be at the same place at the same moment; print -1 if that
set is infinite (statement: if r > 1e9, and a finite answer is at most n+m<=1e6,
so -1 really means "infinitely many").

Published solution (_tooling/solutions/intelligenceexchange.cpp): four
Dijkstras -- from hc, sc, hj, sj -- then one O(n+m) classification.
  * a point p is reachable by Carmen at time dc(p) iff dhc(p)+dsc(p)=Dc, and she
    is additionally at sc for every time >= Dc (same for Juni).  So a VERTEX u is
    a meeting point iff it lies on a shortest path of both and dhc(u)=dhj(u), or
    it is one walker's school, lies on the other's path, and the other passes it
    no earlier than the owner arrives.
  * an edge (u,v,w) can lie on Carmen's shortest paths in at most one direction
    (w>=1), so the only interior meetings are head-on: Carmen u->v during
    [a, a+w], Juni v->u during [c, c+w].  They cross at time (a+c+w)/2, which
    lies strictly inside both intervals iff |a-c| < w; equality means they meet
    at an endpoint, already counted as a vertex.
  * infinitely many meeting points <=> the two traverse a whole edge together
    <=> some u with dhc(u)=dhj(u) on both shortest paths has an incident edge
    u->v lying on a shortest path of both in the SAME direction.

Independent brute force here: subdivide every edge into K unit pieces per unit
of length.  Every crossing point sits at a half-integer offset, so with K=2
EVERY meeting point is a vertex of the subdivided graph and the answer is just
"count the vertices that satisfy the vertex rule" -- no edge reasoning at all.
Running the same count at K=2 and K=4 also detects the infinite case without
knowing the co-traversal criterion: a finite meeting set is unchanged by
refining the mesh, a continuum roughly doubles.
"""
import heapq
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CPP = os.path.join(HERE, os.pardir, "_tooling", "solutions",
                   "intelligenceexchange.cpp")

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
    """Compile the published solution (bits/stdc++.h shimmed for libc++)."""
    cxx = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++")
    if cxx is None or not os.path.exists(CPP):
        return None
    os.makedirs(os.path.join(tmp, "bits"), exist_ok=True)
    with open(os.path.join(tmp, "bits", "stdc++.h"), "w") as f:
        f.write(SHIM)
    exe = os.path.join(tmp, "ie")
    r = subprocess.run([cxx, "-O2", "-std=c++17", "-I", tmp, "-o", exe, CPP],
                       capture_output=True, text=True)
    if r.returncode:
        print("compile failed:\n" + r.stderr[:2000], file=sys.stderr)
        return None
    return exe


# ---------------------------------------------------------------- brute force
def dijkstra(nv, adj, s):
    INF = float("inf")
    d = [INF] * nv
    d[s] = 0
    pq = [(0, s)]
    while pq:
        du, u = heapq.heappop(pq)
        if du != d[u]:
            continue
        for v, w in adj[u]:
            if du + w < d[v]:
                d[v] = du + w
                heapq.heappush(pq, (d[v], v))
    return d


def count_at_scale(n, edges, hc, sc, hj, sj, K):
    """Subdivide each edge of length w into K*w unit pieces, then count the
    subdivided VERTICES that are simultaneous-presence points."""
    nv = n
    adj = []
    for _ in range(n):
        adj.append([])
    for (u, v, w) in edges:
        pieces = K * w
        prev = u
        for k in range(pieces - 1):
            adj.append([])
            cur = nv
            nv += 1
            adj[prev].append((cur, 1))
            adj[cur].append((prev, 1))
            prev = cur
        adj[prev].append((v, 1))
        adj[v].append((prev, 1))
    dhc = dijkstra(nv, adj, hc)
    dsc = dijkstra(nv, adj, sc)
    dhj = dijkstra(nv, adj, hj)
    dsj = dijkstra(nv, adj, sj)
    Dc, Dj = dhc[sc], dhj[sj]
    cnt = 0
    for p in range(nv):
        onC = dhc[p] + dsc[p] == Dc
        onJ = dhj[p] + dsj[p] == Dj
        if (onC and onJ and dhc[p] == dhj[p]):
            cnt += 1
        elif p == sc and onJ and dhj[p] >= Dc:
            cnt += 1
        elif p == sj and onC and dhc[p] >= Dj:
            cnt += 1
    return cnt


def brute(n, edges, hc, sc, hj, sj):
    """-1 when the meeting set is a continuum (count grows with the mesh)."""
    c2 = count_at_scale(n, edges, hc, sc, hj, sj, 2)
    c4 = count_at_scale(n, edges, hc, sc, hj, sj, 4)
    return -1 if c4 != c2 else c2


# ---------------------------------------------------------------- driver
def to_input(cases):
    out = []
    for (n, edges, hc, sc, hj, sj) in cases:
        out.append("%d %d" % (n, len(edges)))
        out.append("%d %d %d %d" % (hc + 1, sc + 1, hj + 1, sj + 1))
        for (u, v, w) in edges:
            out.append("%d %d %d" % (u + 1, v + 1, w))
    out.append("0 0")
    return "\n".join(out) + "\n"


def run(exe, cases):
    r = subprocess.run([exe], input=to_input(cases), capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return [int(x) for x in r.stdout.split()]


# ---------------------------------------------------------------- samples
SAMPLE = ([(5, [(0, 1, 10), (1, 2, 20), (0, 2, 30), (3, 1, 10), (1, 4, 30),
                (3, 4, 40)], 0, 2, 3, 4),
           (5, [(0, 1, 10), (1, 2, 20), (0, 2, 20), (3, 1, 10), (1, 4, 30),
                (3, 4, 40)], 0, 2, 3, 4),
           (3, [(0, 2, 10), (1, 2, 20)], 0, 2, 1, 2)],
          [1, 0, 1])


def check_sample(exe):
    cases, want = SAMPLE
    got_b = [brute(*c) for c in cases]
    assert got_b == want, ("brute disagrees with the statement", got_b, want)
    if exe:
        got_c = run(exe, cases)
        assert got_c == want, ("cpp disagrees with the statement", got_c, want)
    print("sample: brute and published C++ both give", want)


# ---------------------------------------------------------------- random
def rand_case(rng):
    n = rng.randint(2, 6)
    # random spanning tree, then extra edges -- graph must be connected
    edges = []
    for v in range(1, n):
        edges.append((rng.randrange(v), v, rng.randint(1, 3)))
    pool = [(u, v) for u in range(n) for v in range(u + 1, n)]
    rng.shuffle(pool)
    for (u, v) in pool[:rng.randint(0, 3)]:
        edges.append((u, v, rng.randint(1, 3)))
    rng.shuffle(edges)
    hc, sc = rng.sample(range(n), 2)
    if rng.random() < 0.3:        # force shared endpoints often
        hj, sj = hc, sc
    elif rng.random() < 0.3:
        hj = hc
        sj = rng.choice([x for x in range(n) if x != hj])
    else:
        hj, sj = rng.sample(range(n), 2)
    return (n, edges, hc, sc, hj, sj)


def struct_case(rng):
    """Grids and cycles: these actually produce head-on crossings and several
    meeting points, which the sparse random graphs above rarely do."""
    if rng.random() < 0.5:
        R, C = rng.randint(2, 3), rng.randint(2, 4)
        n = R * C
        edges = []
        for r in range(R):
            for c in range(C):
                if r + 1 < R:
                    edges.append((r * C + c, (r + 1) * C + c, rng.choice([1, 1, 2])))
                if c + 1 < C:
                    edges.append((r * C + c, r * C + c + 1, rng.choice([1, 1, 2])))
    else:
        n = rng.randint(4, 9)
        edges = [(i, (i + 1) % n, rng.randint(1, 3)) for i in range(n)]
        for _ in range(rng.randint(0, 2)):
            u, v = rng.sample(range(n), 2)
            edges.append((u, v, rng.randint(1, 3)))
    rng.shuffle(edges)
    hc, sc = rng.sample(range(n), 2)
    hj, sj = rng.sample(range(n), 2)
    return (n, edges, hc, sc, hj, sj)


def rand_test(exe, trials=600, seed=11, gen=rand_case):
    rng = random.Random(seed)
    cases = [gen(rng) for _ in range(trials)]
    exp = [brute(*c) for c in cases]
    if exe:
        got = run(exe, cases)
        assert len(got) == len(exp), (len(got), len(exp))
        for c, g, e in zip(cases, got, exp):
            assert g == e, ("mismatch", c, "cpp=%s" % g, "brute=%s" % e)
    inf = sum(1 for e in exp if e == -1)
    print("random(seed=%d): %d graphs agree (%d of them infinite -> -1), "
          "answers up to %d" % (seed, len(cases), inf, max(exp)))


def check_limits(exe):
    """n = m = 5e5 must finish well inside a contest limit: 4 Dijkstras."""
    if not exe:
        return
    import time
    rng = random.Random(5)
    n = 500000
    edges = [(rng.randrange(v), v, rng.randint(1, 10 ** 9)) for v in range(1, n)]
    while len(edges) < n:
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            edges.append((u, v, rng.randint(1, 10 ** 9)))
    case = (n, edges, 0, n - 1, 1, n - 2)
    t0 = time.time()
    out = run(exe, [case])
    print("limits: n=m=5e5 -> answer %s in %.2fs" % (out, time.time() - t0))


if __name__ == "__main__":
    tmp = tempfile.mkdtemp()
    exe = build(tmp)
    if exe is None:
        print("WARNING: no C++ compiler; brute force is checked alone")
    check_sample(exe)
    rand_test(exe)
    rand_test(exe, trials=600, seed=2024)
    rand_test(exe, trials=700, seed=5, gen=struct_case)
    rand_test(exe, trials=700, seed=909, gen=struct_case)
    check_limits(exe)
    print("OK")
