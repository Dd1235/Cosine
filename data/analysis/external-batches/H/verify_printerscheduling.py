"""printerscheduling: preemptive scheduling of n jobs on m identical machines with release times and
deadlines.  Horn's feasibility test: cut the timeline at the sorted distinct r_i/d_i values (<= 400
boundaries), then max-flow  S -> job i (cap p_i) -> interval k (cap len_k, only if [t_k,t_k+1) is
inside [r_i,d_i]) -> T (cap m*len_k); feasible iff the flow saturates sum p_i.  The per-interval
amounts are then turned into an actual schedule by McNaughton's wrap-around rule (each amount is
<= len_k, so a job never runs on two printers at the same instant).
Checks: (a) vs a unit-time-slot flow, (b) vs an exhaustive DFS for tiny inputs, (c) the emitted
schedule is re-validated against every rule in the statement."""
import random
from collections import deque

class Dinic:
    def __init__(s, n):
        s.n = n; s.to = []; s.cap = []; s.g = [[] for _ in range(n)]
    def add(s, u, v, c):
        s.g[u].append(len(s.to)); s.to.append(v); s.cap.append(c)
        s.g[v].append(len(s.to)); s.to.append(u); s.cap.append(0)
        return len(s.to)-2
    def maxflow(s, src, dst):
        flow = 0
        while True:
            lvl = [-1]*s.n; lvl[src] = 0; q = deque([src])
            while q:
                u = q.popleft()
                for e in s.g[u]:
                    if s.cap[e] > 0 and lvl[s.to[e]] < 0:
                        lvl[s.to[e]] = lvl[u]+1; q.append(s.to[e])
            if lvl[dst] < 0: return flow
            it = [0]*s.n
            def dfs(u, f):
                if u == dst: return f
                while it[u] < len(s.g[u]):
                    e = s.g[u][it[u]]; v = s.to[e]
                    if s.cap[e] > 0 and lvl[v] == lvl[u]+1:
                        d = dfs(v, min(f, s.cap[e]))
                        if d: s.cap[e] -= d; s.cap[e^1] += d; return d
                    it[u] += 1
                return 0
            while True:
                f = dfs(src, 10**18)
                if not f: break
                flow += f

def solve(n, m, jobs):
    """jobs = [(p,r,d)]; returns None if infeasible else list per job of (x,y,printer)"""
    pts = sorted({t for p, r, d in jobs for t in (r, d)})
    iv = [(pts[k], pts[k+1]) for k in range(len(pts)-1)]
    K = len(iv)
    S = n + K; T = S + 1
    din = Dinic(T+1)
    for i, (p, r, d) in enumerate(jobs): din.add(S, i, p)
    eid = {}
    for k, (a, b) in enumerate(iv):
        ln = b - a
        for i, (p, r, d) in enumerate(jobs):
            if r <= a and b <= d: eid[(i, k)] = din.add(i, n+k, ln)
        din.add(n+k, T, m*ln)
    f = din.maxflow(S, T)
    if f != sum(p for p, r, d in jobs): return None
    sched = [[] for _ in range(n)]
    for k, (a, b) in enumerate(iv):
        ln = b - a
        amounts = [(i, din.cap[eid[(i, k)] ^ 1]) for i in range(n) if (i, k) in eid]
        amounts = [(i, x) for i, x in amounts if x > 0]
        pos = 0                                    # McNaughton wrap-around
        for i, x in amounts:
            while x > 0:
                pr = pos // ln; off = pos % ln
                take = min(x, ln - off)
                sched[i].append((a+off, a+off+take, pr+1))
                pos += take; x -= take
    return sched

def check(n, m, jobs, sched):
    for i, (p, r, d) in enumerate(jobs):
        tot = 0; segs = sorted(sched[i])
        for a, b, pr in segs:
            assert r <= a < b <= d, ("outside window", i, a, b, r, d)
            assert 1 <= pr <= m, ("bad printer", pr)
            tot += b-a
        for j in range(len(segs)-1):
            assert segs[j][1] <= segs[j+1][0], ("job overlaps itself", i, segs)
        assert tot == p, ("wrong page count", i, tot, p)
    per = {}
    for i in range(n):
        for a, b, pr in sched[i]: per.setdefault(pr, []).append((a, b))
    for pr, segs in per.items():
        segs.sort()
        for j in range(len(segs)-1):
            assert segs[j][1] <= segs[j+1][0], ("printer overlap", pr, segs)
    return True

def unitflow(n, m, jobs):
    """independent feasibility: one node per unit time slot"""
    lo = min(r for p, r, d in jobs); hi = max(d for p, r, d in jobs)
    Tn = hi - lo
    S = n + Tn; T = S+1
    din = Dinic(T+1)
    for i, (p, r, d) in enumerate(jobs): din.add(S, i, p)
    for t in range(Tn):
        for i, (p, r, d) in enumerate(jobs):
            if r <= lo+t and lo+t+1 <= d: din.add(i, n+t, 1)
        din.add(n+t, T, m)
    return din.maxflow(S, T) == sum(p for p, r, d in jobs)

def brute(n, m, jobs):
    """exhaustive DFS over unit time slots"""
    lo = min(r for p, r, d in jobs); hi = max(d for p, r, d in jobs)
    from functools import lru_cache
    import itertools
    @lru_cache(maxsize=None)
    def go(t, rem):
        if all(x == 0 for x in rem): return True
        if t >= hi: return False
        avail = [i for i in range(n) if rem[i] > 0 and jobs[i][1] <= t and t+1 <= jobs[i][2]]
        # must not let any job miss its deadline
        for i in range(n):
            if rem[i] > 0 and jobs[i][2] <= t: return False
        for k in range(min(m, len(avail)), -1, -1):
            for sub in itertools.combinations(avail, k):
                nr = list(rem)
                for i in sub: nr[i] -= 1
                if go(t+1, tuple(nr)): return True
        return False
    return go(lo, tuple(p for p, r, d in jobs))

jobs1 = [(4,2,7),(3,3,8),(3,4,7),(5,1,10)]
s = solve(4, 2, jobs1); assert s is not None and check(4,2,jobs1,s), s
assert solve(4, 1, jobs1) is None
random.seed(37)
bad = 0; feas = 0
for t in range(300):
    n = random.randint(1,3); m = random.randint(1,2)
    jobs = []
    for _ in range(n):
        r = random.randint(0,4); ln = random.randint(1,4); d = r+ln
        p = random.randint(1, ln)
        jobs.append((p,r,d))
    got = solve(n,m,jobs); uf = unitflow(n,m,jobs); bf = brute(n,m,jobs)
    if (got is not None) != uf or uf != bf:
        bad += 1
        if bad < 5: print("MISMATCH", n, m, jobs, got is not None, uf, bf)
    if got is not None:
        feas += 1; check(n,m,jobs,got)
# bigger random instances: compressed flow vs unit flow, and schedule validity
for t in range(60):
    n = random.randint(1,6); m = random.randint(1,3)
    jobs = []
    for _ in range(n):
        r = random.randint(0,20); ln = random.randint(1,15); d = r+ln
        p = random.randint(1, ln)
        jobs.append((p,r,d))
    got = solve(n,m,jobs)
    if (got is not None) != unitflow(n,m,jobs):
        bad += 1; print("MISMATCH big", n, m, jobs)
    if got is not None: check(n,m,jobs,got)
print("samples ok (YES/NO); feasible cases validated =", feas, "; mismatches =", bad)
