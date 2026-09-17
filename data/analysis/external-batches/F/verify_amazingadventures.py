"""Amazing Adventures: min-cost flow model vs exhaustive simple-path search.

A simple path B -> ... -> C -> ... -> G is exactly a pair of paths B->C and
G->C that share no vertex except C.  Split every cell into in/out with capacity
1 (capacity 2 for C), give every grid step cost 1, delete U, and push 2 units
from a super source feeding B_in and G_in into C_out.  Min cost = min number of
steps; infeasible = NO.  Costs are non-negative so no flow decomposition cycle
can appear, and the two units decompose into vertex-disjoint paths.
"""
import random
from heapq import heappush, heappop

INF = float('inf')


class MCMF:
    def __init__(self, n):
        self.n = n
        self.to = []
        self.cap = []
        self.cost = []
        self.g = [[] for _ in range(n)]

    def add(self, u, v, cap, cost):
        self.g[u].append(len(self.to)); self.to.append(v); self.cap.append(cap); self.cost.append(cost)
        self.g[v].append(len(self.to)); self.to.append(u); self.cap.append(0); self.cost.append(-cost)

    def run(self, s, t, need):
        n = self.n
        pot = [0] * n
        flow = 0
        total = 0
        while flow < need:
            dist = [INF] * n
            pe = [-1] * n
            dist[s] = 0
            pq = [(0, s)]
            while pq:
                d, u = heappop(pq)
                if d > dist[u]:
                    continue
                for e in self.g[u]:
                    if self.cap[e] <= 0:
                        continue
                    v = self.to[e]
                    nd = d + self.cost[e] + pot[u] - pot[v]
                    if nd < dist[v]:
                        dist[v] = nd
                        pe[v] = e
                        heappush(pq, (nd, v))
            if dist[t] == INF:
                return None
            for i in range(n):
                if dist[i] < INF:
                    pot[i] += dist[i]
            f = need - flow
            v = t
            while v != s:
                e = pe[v]
                f = min(f, self.cap[e])
                v = self.to[e ^ 1]
            v = t
            while v != s:
                e = pe[v]
                self.cap[e] -= f
                self.cap[e ^ 1] += f
                total += f * self.cost[e]
                v = self.to[e ^ 1]
            flow += f
        return total


def solve(N, M, B, C, G, U):
    idx = lambda r, c: r * M + c
    cells = N * M
    IN = lambda v: 2 * v
    OUT = lambda v: 2 * v + 1
    S = 2 * cells
    T = 2 * cells + 1
    f = MCMF(2 * cells + 2)
    for r in range(N):
        for c in range(M):
            if (r, c) == U:
                continue
            v = idx(r, c)
            f.add(IN(v), OUT(v), 2 if (r, c) == C else 1, 0)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < M and (nr, nc) != U:
                    f.add(OUT(v), IN(idx(nr, nc)), 2, 1)
    f.add(S, IN(idx(*B)), 1, 0)
    f.add(S, IN(idx(*G)), 1, 0)
    f.add(OUT(idx(*C)), T, 2, 0)
    return f.run(S, T, 2)


def brute(N, M, B, C, G, U):
    best = [None]
    seen = set([B])

    def dfs(cur, length, hitC):
        if best[0] is not None and length >= best[0]:
            return
        if cur == G:
            if hitC:
                best[0] = length
            return
        r, c = cur
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = (r + dr, c + dc)
            if not (0 <= nx[0] < N and 0 <= nx[1] < M):
                continue
            if nx == U or nx in seen:
                continue
            seen.add(nx)
            dfs(nx, length + 1, hitC or nx == C)
            seen.discard(nx)
    dfs(B, 0, B == C)
    return best[0]


def main():
    # sample 1: 3x3, B=(1,1) C=(3,3) G=(2,1) U=(2,2) -> RRUULLD, 7 steps
    assert solve(3, 3, (0, 0), (2, 2), (1, 0), (1, 1)) == 7
    # sample 2: 3x4, B=(1,1) C=(3,4) G=(2,1) U=(1,2) -> NO
    assert solve(3, 4, (0, 0), (2, 3), (1, 0), (0, 1)) is None
    # sample 3: 2x2, B=(2,1) C=(2,2) G=(1,2) U=(1,1) -> RD, 2 steps
    assert solve(2, 2, (1, 0), (1, 1), (0, 1), (0, 0)) == 2
    print("samples ok")
    random.seed(4)
    tested = 0
    while tested < 400:
        N = random.randint(1, 4)
        M = random.randint(1, 4)
        if N * M < 4:
            continue
        cells = [(r, c) for r in range(N) for c in range(M)]
        B, C, G, U = random.sample(cells, 4)
        a, b = solve(N, M, B, C, G, U), brute(N, M, B, C, G, U)
        assert a == b, (N, M, B, C, G, U, a, b)
        tested += 1
    print("400 random grids (<=4x4) match exhaustive simple-path search")


main()
