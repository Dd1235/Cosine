"""ultimatepipegame: every empty cell must use exactly 2 of its 4 sides, and a side is used iff the
neighbour across it uses its opposite side -- i.e. a spanning degree-2 subgraph of the empty cells.
Cost is 0 unless the two sides are opposite (L+R costs h, U+D costs v), which is a CONVEX cost on the
number of units (1 or 2) leaving a cell horizontally, so it becomes a min-cost flow:
 S -> black cell (cap 2); cell -> Hport via two parallel edges (1,0) and (1,h); likewise Vport with v;
 Hport(black) -> Hport(left/right neighbour), Vport(black) -> Vport(up/down neighbour) (cap 1);
 white side mirrored into the sink.  Feasible iff the flow saturates 2*#black (needs #black==#white).
Brute force: enumerate all 6 side-pairs per empty cell."""
import random, itertools
from collections import deque
INF = float('inf')

class MCMF:
    def __init__(s, n):
        s.n = n; s.g = [[] for _ in range(n)]
    def add(s, u, v, cap, cost):
        s.g[u].append([v, cap, cost, len(s.g[v])])
        s.g[v].append([u, 0, -cost, len(s.g[u])-1])
    def run(s, src, dst):
        flow = cost = 0
        while True:
            dist = [INF]*s.n; dist[src] = 0; inq = [False]*s.n
            pv = [None]*s.n
            q = deque([src]); inq[src] = True
            while q:
                u = q.popleft(); inq[u] = False
                for i, e in enumerate(s.g[u]):
                    v, cap, c, _ = e
                    if cap > 0 and dist[u] + c < dist[v]:
                        dist[v] = dist[u] + c; pv[v] = (u, i)
                        if not inq[v]: inq[v] = True; q.append(v)
            if dist[dst] == INF: return flow, cost
            f = INF; v = dst
            while v != src:
                u, i = pv[v]; f = min(f, s.g[u][i][1]); v = u
            v = dst
            while v != src:
                u, i = pv[v]; s.g[u][i][1] -= f; e = s.g[u][i]; s.g[e[0]][e[3]][1] += f; v = u
            flow += f; cost += f*dist[dst]

def solve(m, n, grid, h, v):
    idx = {}
    for i in range(m):
        for j in range(n):
            if grid[i][j] == '.': idx[(i, j)] = len(idx)
    k = len(idx)
    if k == 0: return 0
    black = [c for c in idx if (c[0]+c[1]) % 2 == 0]
    white = [c for c in idx if (c[0]+c[1]) % 2 == 1]
    if len(black) != len(white): return None
    N = 3*k + 2; S, T = 3*k, 3*k+1
    def node(c): return idx[c]
    def Hn(c): return k + idx[c]
    def Vn(c): return 2*k + idx[c]
    mc = MCMF(N)
    for c in black:
        i, j = c
        mc.add(S, node(c), 2, 0)
        mc.add(node(c), Hn(c), 1, 0); mc.add(node(c), Hn(c), 1, h[i][j])
        mc.add(node(c), Vn(c), 1, 0); mc.add(node(c), Vn(c), 1, v[i][j])
        for dj in (-1, 1):
            if (i, j+dj) in idx: mc.add(Hn(c), Hn((i, j+dj)), 1, 0)
        for di in (-1, 1):
            if (i+di, j) in idx: mc.add(Vn(c), Vn((i+di, j)), 1, 0)
    for c in white:
        i, j = c
        mc.add(Hn(c), node(c), 1, 0); mc.add(Hn(c), node(c), 1, h[i][j])
        mc.add(Vn(c), node(c), 1, 0); mc.add(Vn(c), node(c), 1, v[i][j])
        mc.add(node(c), T, 2, 0)
    f, cost = mc.run(S, T)
    return cost if f == 2*len(black) else None

PAIRS = [('L','R'), ('U','D'), ('L','U'), ('L','D'), ('R','U'), ('R','D')]
DELTA = {'L': (0,-1), 'R': (0,1), 'U': (-1,0), 'D': (1,0)}
OPP = {'L':'R','R':'L','U':'D','D':'U'}

def brute(m, n, grid, h, v):
    cells = [(i,j) for i in range(m) for j in range(n) if grid[i][j]=='.']
    best = None
    for combo in itertools.product(range(6), repeat=len(cells)):
        ch = dict(zip(cells, [set(PAIRS[c]) for c in combo]))
        ok = True
        for c in cells:
            i, j = c
            for d in ch[c]:
                di, dj = DELTA[d]; nb = (i+di, j+dj)
                if nb not in ch or OPP[d] not in ch[nb]: ok = False; break
            if not ok: break
        if not ok: continue
        cost = 0
        for (i,j) in cells:
            s = ch[(i,j)]
            if s == {'L','R'}: cost += h[i][j]
            elif s == {'U','D'}: cost += v[i][j]
        if best is None or cost < best: best = cost
    return best

# samples
g1 = ["##..","##..","..##","..##"]
h1 = [[0,0,1,2],[0,0,3,0],[1,2,0,0],[2,3,0,0]]
assert solve(4,4,g1,h1,h1) == 0, solve(4,4,g1,h1,h1)
g2 = ["...#",".#..","...."]
h2 = [[1,2,3,0],[4,0,1,2],[3,1,2,3]]
v2 = [[3,2,1,0],[5,0,2,2],[3,1,2,3]]
assert solve(3,4,g2,h2,v2) == 10, solve(3,4,g2,h2,v2)
g3 = ["...","...","..."]
h3 = [[0]*3]*3; v3 = [[1]*3]*3
assert solve(3,3,g3,h3,v3) is None, solve(3,3,g3,h3,v3)

random.seed(29)
bad = 0; trials = 0
for t in range(120):
    m = random.randint(2, 3); n = random.randint(2, 3)
    grid = [''.join(random.choice('..#') for _ in range(n)) for _ in range(m)]
    if sum(r.count('.') for r in grid) > 8: continue
    h = [[random.randint(0,6) for _ in range(n)] for _ in range(m)]
    v = [[random.randint(0,6) for _ in range(n)] for _ in range(m)]
    s, b = solve(m,n,grid,h,v), brute(m,n,grid,h,v)
    trials += 1
    if s != b:
        bad += 1
        if bad < 4: print("MISMATCH", grid, h, v, s, b)
print("samples ok (0 / 10 / NO); brute-forced", trials, "random grids; mismatches =", bad)
