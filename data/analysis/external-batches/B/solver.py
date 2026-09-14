import sys
from functools import lru_cache
sys.setrecursionlimit(100000)
INF = 10**9

def movables(pegs):
    return [d for peg in pegs for d in peg if d != INF]

@lru_cache(maxsize=None)
def G(pegs, target):
    mv = movables(pegs)
    if not mv: return 0
    m = max(mv)
    p = next(i for i in range(3) if m in pegs[i])
    idx = pegs[p].index(m)
    below = tuple(d for d in pegs[p][:idx] if d != INF)   # movable disks below m on peg p
    above = pegs[p][idx+1:]
    infs = tuple(d for d in pegs[p][:idx] if d == INF)
    if p == target and not below:
        np = list(pegs)
        np[p] = pegs[p][:idx] + (INF,) + pegs[p][idx+1:]
        return G(tuple(np), target)
    if p != target:
        q = 3 - p - target
        cfg1 = list(pegs)
        cfg1[p] = infs + (INF,) + above
        c1 = G(tuple(cfg1), q)
        U = sorted((d for d in mv if d != m and d not in below), reverse=True)
        cfg2 = [None]*3
        cfg2[p] = infs + below
        cfg2[q] = tuple(d for d in pegs[q] if d == INF) + tuple(U)
        cfg2[target] = tuple(d for d in pegs[target] if d == INF) + (INF,)
        c2 = G(tuple(cfg2), target)
        return c1 + 1 + c2
    # p == target, m not at bottom (below nonempty)
    best = None
    for X in range(3):
        if X == target: continue
        Y = 3 - X - target
        cfg1 = list(pegs)
        cfg1[target] = infs + (INF,) + above
        c1 = G(tuple(cfg1), Y)
        V = sorted((d for d in mv if d != m and d not in below), reverse=True)
        cfg2 = [None]*3
        cfg2[target] = infs + below
        cfg2[X] = tuple(d for d in pegs[X] if d == INF) + (INF,)
        cfg2[Y] = tuple(d for d in pegs[Y] if d == INF) + tuple(V)
        c2 = G(tuple(cfg2), Y)
        cnt = len(mv) - 1
        tot = c1 + 1 + c2 + 1 + (2**cnt - 1)
        if best is None or tot < best: best = tot
    return best
