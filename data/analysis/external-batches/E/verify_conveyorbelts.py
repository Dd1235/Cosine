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
checks conflicts by literally simulating which minute each product sits on each belt.
"""
import random
import sys
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


def occupancy(j, k, route):
    """(belt, minute) slots literally used by every product of producer j.
    Product born at minute x*K+j rides belt route[d] during minute x*K+j+d."""
    slots = []
    for x in range(HORIZON):
        birth = x * k + j
        for d, ei in enumerate(route):
            slots.append((ei, birth + d))
    return slots


def brute(n, k, edges):
    routes = {}
    for j in range(1, k + 1):
        routes[j] = all_routes(n, k, edges, j)
    producers = [j for j in range(1, k + 1) if routes[j]]
    best = 0

    def try_subset(sub):
        used = set()

        def rec(i):
            if i == len(sub):
                return True
            j = sub[i]
            for r in routes[j]:
                slots = occupancy(j, k, r)
                if any(s in used for s in slots):
                    continue
                if len(set(slots)) != len(slots):      # self-collision
                    continue
                used.update(slots)
                if rec(i + 1):
                    return True
                used.difference_update(slots)
            return False

        return rec(0)

    for size in range(len(producers), 0, -1):
        for sub in combinations(producers, size):
            if try_subset(list(sub)):
                return size
    return best


# ------------------------------------------------------------------------ testing
SAMPLES = [
    ((4, 2, [(1, 3), (2, 3), (3, 4)]), 2),
    ((5, 2, [(1, 3), (3, 4), (2, 4), (4, 5)]), 1),
    ((5, 2, [(1, 4), (2, 3), (3, 4), (4, 5), (2, 4), (3, 3)]), 2),
]


def main():
    for (args, want) in SAMPLES:
        got = solve(*args)
        print("sample", args, "want", want, "got", got)
        assert got == want, "SAMPLE FAILED"

    random.seed(11)
    for it in range(3000):
        n = random.randint(1, 5)
        k = random.randint(1, n)
        m = random.randint(0, 6)
        edges = [(random.randint(1, n), random.randint(1, n)) for _ in range(m)]
        a, b = solve(n, k, edges), brute(n, k, edges)
        if a != b:
            print("MISMATCH", n, k, edges, "flow", a, "brute", b)
            sys.exit(1)
    print("3000 random small cases: flow model == faithful simulation brute force")

    # a couple of larger random checks against the brute force with more room
    random.seed(7)
    for it in range(300):
        n = random.randint(2, 7)
        k = random.randint(1, min(n, 3))
        m = random.randint(0, 9)
        edges = [(random.randint(1, n), random.randint(1, n)) for _ in range(m)]
        a, b = solve(n, k, edges), brute(n, k, edges)
        if a != b:
            print("MISMATCH", n, k, edges, "flow", a, "brute", b)
            sys.exit(1)
    print("300 larger random cases OK")

    # bottleneck generator: every producer is forced through a narrow waist, which is
    # where the "same belt, different minute" accounting actually decides the answer.
    random.seed(23)
    hard = 0
    for it in range(600):
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
        a, b = solve(n, k, edges), brute(n, k, edges)
        if a != b:
            print("MISMATCH", n, k, edges, "flow", a, "brute", b)
            sys.exit(1)
        if 0 < a < k:
            hard += 1
    print("600 bottleneck cases OK (%d of them had to switch producers off)" % hard)


if __name__ == "__main__":
    main()
