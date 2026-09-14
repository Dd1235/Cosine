#!/usr/bin/env python3
"""Kattis 'conveyorbelts' (2018 ICPC Asia Singapore) -- solver + independent brute force.

Intended solution
-----------------
A product of producer j is created at minute x*K+j and its route is fixed, so if a
route uses its (d+1)-th belt then that belt is busy at minutes x*K+j+d for every
x >= 0, i.e. exactly at the minutes congruent to (j+d) mod K.  Two products clash on
a belt iff their (producer + depth) values agree mod K.  So build the "phase" graph
on states (v, p), v a junction and p in Z_K: belt (a,b) gives an arc
(a,p) -> (b, p+1 mod K) of capacity 1 for each p (that arc IS the resource "belt at
phase p", usable once).  Producer j starts at state (j, j mod K); every state (N,p)
is a sink.  A set of producers is simultaneously routable iff there is an integral
flow of that size, so the answer is the max flow with unit source edges.
Nodes N*K <= 90000, arcs M*K <= 300000, flow value <= K <= 300 -- Dinic is instant.

The brute force below does NOT use the phase argument: it enumerates routes and
checks conflicts by literally simulating which minute each product sits on each belt
(real minutes x*K+j+d over many periods, never a residue class).  Two cheap exact
prunings keep it finishable -- routes with identical slot sets collapse, and a route
whose slots are a superset of another's is never needed -- and a case whose distinct
route count still exceeds MAX_OPTIONS is skipped and counted rather than hung on.
"""
import random
import sys
import threading
import time
from collections import deque
from itertools import combinations


# ---------------------------------------------------------------- intended solution
class Dinic:
    def __init__(self, n):
        self.n = n
        self.to = []
        self.cap = []
        self.g = [[] for _ in range(n)]

    def add(self, u, v, c):
        self.g[u].append(len(self.to))
        self.to.append(v)
        self.cap.append(c)
        self.g[v].append(len(self.to))
        self.to.append(u)
        self.cap.append(0)

    def maxflow(self, s, t):
        flow = 0
        while True:
            level = [-1] * self.n
            level[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for e in self.g[u]:
                    if self.cap[e] > 0 and level[self.to[e]] < 0:
                        level[self.to[e]] = level[u] + 1
                        q.append(self.to[e])
            if level[t] < 0:
                return flow
            it = [0] * self.n

            def dfs(u, f):
                if u == t:
                    return f
                while it[u] < len(self.g[u]):
                    e = self.g[u][it[u]]
                    v = self.to[e]
                    if self.cap[e] > 0 and level[v] == level[u] + 1:
                        d = dfs(v, min(f, self.cap[e]))
                        if d:
                            self.cap[e] -= d
                            self.cap[e ^ 1] += d
                            return d
                    it[u] += 1
                return 0

            while True:
                f = dfs(s, 10 ** 9)
                if not f:
                    break
                flow += f


def solve(n, k, edges):
    """Max number of producers that can keep running."""
    sys.setrecursionlimit(10000 + n * k * 4)
    idx = lambda v, p: (v - 1) * k + p          # noqa: E731
    S, T = n * k, n * k + 1
    din = Dinic(n * k + 2)
    for j in range(1, k + 1):
        din.add(S, idx(j, j % k), 1)
    for (a, b) in edges:
        for p in range(k):
            din.add(idx(a, p), idx(b, (p + 1) % k), 1)
    INF = 10 ** 9
    for p in range(k):
        din.add(idx(n, p), T, INF)
    return din.maxflow(S, T)


# ------------------------------------------------------------------- brute force
def all_routes(n, k, edges, j, cap_states=None):
    """Every route (list of belt indices) from junction j to junction N that never
    repeats a (junction, minutes-elapsed mod K) state.  Repeating a state can always
    be cut out: the shortened route delivers to N just as well and occupies a subset
    of the belt/minute slots, so restricting to these loses no optimum."""
    out = []
    adj = [[] for _ in range(n + 1)]
    for i, (a, b) in enumerate(edges):
        adj[a].append((i, b))
    seen = set()

    def rec(v, p, path):
        if v == n:
            out.append(tuple(path))
            return                       # stop at the warehouse
        for (ei, w) in adj[v]:
            st = (w, (p + 1) % k)
            if st in seen:
                continue
            seen.add(st)
            path.append(ei)
            rec(w, (p + 1) % k, path)
            path.pop()
            seen.discard(st)

    seen.add((j, j % k))
    rec(j, j % k, [])
    return out


HORIZON = 40
MAX_OPTIONS = 400          # safety valve: above this the subset search is hopeless


class TooWide(Exception):
    """Raised when a case has too many distinct routes to brute force honestly."""


def occupancy(j, k, route):
    """(belt, minute) slots literally used by every product of producer j.
    Product born at minute x*K+j rides belt route[d] during minute x*K+j+d.
    Deliberately expressed in real minutes, not in phases mod K -- the phase
    argument is the thing under test, so the brute force must not assume it."""
    slots = []
    for x in range(HORIZON):
        birth = x * k + j
        for d, ei in enumerate(route):
            slots.append((ei, birth + d))
    return slots


def route_options(n, k, edges, j):
    """The distinct, non-dominated slot sets producer j could occupy.

    Two routes matter only through the set of (belt, minute) slots they occupy, so
    identical slot sets collapse; and if one route's slots are a subset of
    another's, the bigger one is never needed (swapping it for the smaller keeps
    every disjointness that held).  Without this the plain route list reaches many
    thousands of entries and the subset search below never finishes.
    """
    out = []
    for route in all_routes(n, k, edges, j):
        slots = occupancy(j, k, route)
        if len(set(slots)) != len(slots):       # self-collision: illegal route
            continue
        out.append(frozenset(slots))
    out = list(set(out))
    if len(out) > MAX_OPTIONS:
        raise TooWide(len(out))
    minimal = [a for i, a in enumerate(out)
               if not any(i != m and b <= a for m, b in enumerate(out))]
    # `b <= a` with equal sets cannot happen twice: duplicates were removed above
    return minimal


def brute(n, k, edges):
    options = {j: route_options(n, k, edges, j) for j in range(1, k + 1)}
    producers = [j for j in range(1, k + 1) if options[j]]

    def try_subset(sub):
        def rec(i, used):
            if i == len(sub):
                return True
            for slots in options[sub[i]]:
                if slots.isdisjoint(used):
                    if rec(i + 1, used | slots):
                        return True
            return False

        return rec(0, frozenset())

    for size in range(len(producers), 0, -1):
        for sub in combinations(producers, size):
            if try_subset(list(sub)):
                return size
    return 0


# ------------------------------------------------------------------------ testing
SAMPLES = [
    ((4, 2, [(1, 3), (2, 3), (3, 4)]), 2),
    ((5, 2, [(1, 3), (3, 4), (2, 4), (4, 5)]), 1),
    ((5, 2, [(1, 4), (2, 3), (3, 4), (4, 5), (2, 4), (3, 3)]), 2),
]


def compare(n, k, edges, tally):
    """solve vs brute on one case; returns False if the case was too wide to brute."""
    try:
        b = brute(n, k, edges)
    except TooWide:
        tally["skipped"] += 1
        return False
    a = solve(n, k, edges)
    if a != b:
        print("MISMATCH", n, k, edges, "flow", a, "brute", b)
        sys.exit(1)
    tally["checked"] += 1
    if 0 < a < k:
        tally["hard"] += 1
    return True


def main():
    for (args, want) in SAMPLES:
        got = solve(*args)
        print("sample", args, "want", want, "got", got)
        assert got == want, "SAMPLE FAILED"
        assert brute(*args) == want, "BRUTE DISAGREES WITH SAMPLE"
    print("all three samples agree with both the flow model and the simulation")

    tally = {"checked": 0, "skipped": 0, "hard": 0}
    random.seed(11)
    for _ in range(3000):
        n = random.randint(1, 5)
        k = random.randint(1, n)
        m = random.randint(0, 6)
        edges = [(random.randint(1, n), random.randint(1, n)) for _ in range(m)]
        compare(n, k, edges, tally)
    print("small random: %(checked)d checked, %(skipped)d too wide, %(hard)d needed "
          "a producer switched off" % tally)

    tally = {"checked": 0, "skipped": 0, "hard": 0}
    random.seed(7)
    for _ in range(400):
        n = random.randint(2, 7)
        k = random.randint(1, min(n, 3))
        m = random.randint(0, 9)
        edges = [(random.randint(1, n), random.randint(1, n)) for _ in range(m)]
        compare(n, k, edges, tally)
    print("larger random: %(checked)d checked, %(skipped)d too wide, %(hard)d hard" % tally)

    # bottleneck generator: every producer is forced through a narrow waist, which is
    # where the "same belt, different minute" accounting actually decides the answer.
    tally = {"checked": 0, "skipped": 0, "hard": 0}
    random.seed(23)
    for _ in range(600):
        n = random.randint(4, 7)
        k = random.randint(2, min(n - 1, 4))
        waist = n - 1
        edges = [(waist, n)]                       # the single exit belt
        for j in range(1, k + 1):                  # producers feed the waist
            hops = random.randint(1, 2)
            v = j
            for _ in range(hops):
                w = random.randint(1, n - 1)
                edges.append((v, w))
                v = w
            edges.append((v, waist))
        for _ in range(random.randint(0, 3)):
            edges.append((random.randint(1, n - 1), random.randint(1, n - 1)))
        compare(n, k, edges, tally)
    print("bottleneck: %(checked)d checked, %(skipped)d too wide, %(hard)d had to "
          "switch producers off" % tally)

    # phase-collision generator: every producer reaches one shared exit belt, but by
    # chains of different lengths, so the exit belt is contested exactly when two
    # producers' (index + route length) values agree modulo K
    tally = {"checked": 0, "skipped": 0, "hard": 0}
    random.seed(41)
    for _ in range(600):
        k = random.randint(2, 3)
        nxt = k + 1
        edges = []
        hub_pred = []
        for j in range(1, k + 1):
            v = j
            for _ in range(random.randint(1, 3) - 1):   # fresh intermediate nodes
                edges.append((v, nxt))
                v = nxt
                nxt += 1
            hub_pred.append(v)
        hub = nxt
        nxt += 1
        for v in hub_pred:
            edges.append((v, hub))
        n = nxt                                          # the warehouse
        edges.append((hub, n))
        if random.random() < 0.3:                        # sometimes a second exit belt
            edges.append((hub, n))
        compare(n, k, edges, tally)
    print("phase-collision: %(checked)d checked, %(skipped)d too wide, %(hard)d had "
          "to switch producers off" % tally)

    # cost at the stated limit (answer unverifiable at this size, this is timing only)
    random.seed(3)
    n, k, m = 300, 300, 1000
    edges = [(random.randint(1, n), random.randint(1, n)) for _ in range(m)]
    t = time.time()
    f = solve(n, k, edges)
    print("N=K=300, M=1000: %d nodes, %d arcs, flow %d, %.1fs even in Python"
          % (n * k + 2, m * k, f, time.time() - t))


if __name__ == "__main__":
    threading.stack_size(512 * 1024 * 1024)   # the Dinic dfs recurses per node
    th = threading.Thread(target=main)
    th.start()
    th.join()
