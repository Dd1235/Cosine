"""Joining Networks: trees A (N<=5e4) and B (M<=5e4); add one edge (a,b); the cost
of a network is sum over unordered pairs of dist^2.  Minimise.

Solution: cost(C) = in(A) + in(B) + cross, and for a cross pair (u,v)
d = dA(u,a)+1+dB(v,b), so
cross(a,b) = M*S2A(a) + 2M*S1A(a) + N*S2B(b) + 2N*S1B(b) + 2*S1A(a)*S1B(b) + N*M,
where S1(x)=sum_u d(u,x), S2(x)=sum_u d(u,x)^2 (both via rerooting DP in O(n)).
For a fixed b this is min over a of a LINE  y = S1A(a)*t + M*S2A(a)  at
t = 2M + 2*S1B(b) > 0, so a lower-hull / convex-hull-trick sweep answers all b in
O((N+M) log).  Total O(N log N + M log M), O(N+M) space.

Check: rerooting S1/S2 vs BFS, and the CHT minimisation vs the O(N*M) double loop,
on random trees; plus both samples.
"""
import random
from collections import deque

def bfs_dists(adj, n, src):
    d = [-1]*(n+1); d[src] = 0; q = deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if d[v] < 0:
                d[v] = d[u]+1; q.append(v)
    return d

def reroot(adj, n):
    """returns S1[x], S2[x] for all x, via two passes"""
    order = []; par = [0]*(n+1); vis=[False]*(n+1)
    st=[1]; vis[1]=True
    while st:
        u=st.pop(); order.append(u)
        for v in adj[u]:
            if not vis[v]:
                vis[v]=True; par[v]=u; st.append(v)
    cnt=[1]*(n+1); s1=[0]*(n+1); s2=[0]*(n+1)
    for u in reversed(order[1:]):
        p=par[u]
        cnt[p]+=cnt[u]
        s2[p]+= s2[u] + 2*s1[u] + cnt[u]
        s1[p]+= s1[u] + cnt[u]
    S1=[0]*(n+1); S2=[0]*(n+1); S1[1]=s1[1]; S2[1]=s2[1]
    for u in order[1:]:
        p=par[u]
        # remove u's subtree contribution from p
        ps1 = S1[p] - (s1[u] + cnt[u])
        ps2 = S2[p] - (s2[u] + 2*s1[u] + cnt[u])
        pc  = n - cnt[u]
        S1[u] = s1[u] + ps1 + pc
        S2[u] = s2[u] + ps2 + 2*ps1 + pc
    return S1, S2

def internal(S1, n, adj):
    # sum over unordered pairs of d^2 = (1/2) sum_x S2[x]
    _, S2 = reroot(adj, n)
    return sum(S2[1:])//2

class Hull:
    """lower envelope of lines y = m*t + c, queries at increasing t"""
    def __init__(self):
        self.ms=[]; self.cs=[]
    def bad(self, i, j, k):
        m1,c1=self.ms[i],self.cs[i]; m2,c2=self.ms[j],self.cs[j]; m3,c3=self.ms[k],self.cs[k]
        return (c3-c1)*(m1-m2) <= (c2-c1)*(m1-m3)
    def add(self, m, c):
        self.ms.append(m); self.cs.append(c)
        while len(self.ms)>=3 and self.bad(len(self.ms)-3, len(self.ms)-2, len(self.ms)-1):
            self.ms.pop(-2); self.cs.pop(-2)
    def query(self, t):
        lo,hi=0,len(self.ms)-1
        while lo<hi:
            mid=(lo+hi)//2
            if self.ms[mid]*t+self.cs[mid] <= self.ms[mid+1]*t+self.cs[mid+1]: hi=mid
            else: lo=mid+1
        return self.ms[lo]*t+self.cs[lo]

def solve_fast(N, ea, M, eb):
    adjA=[[] for _ in range(N+1)]
    for u,v in ea: adjA[u].append(v); adjA[v].append(u)
    adjB=[[] for _ in range(M+1)]
    for u,v in eb: adjB[u].append(v); adjB[v].append(u)
    S1A,S2A = reroot(adjA,N); S1B,S2B = reroot(adjB,M)
    inA = sum(S2A[1:])//2; inB = sum(S2B[1:])//2
    pts = sorted(set((S1A[a], M*S2A[a]) for a in range(1,N+1)))
    # keep min c per m
    best={}
    for m,c in pts:
        if m not in best or c<best[m]: best[m]=c
    h=Hull()
    for m in sorted(best, reverse=True):     # decreasing slope for increasing t
        h.add(m, best[m])
    ans=None
    for b in range(1,M+1):
        t = 2*M + 2*S1B[b]
        val = h.query(t) + N*S2B[b] + 2*N*S1B[b] + N*M
        if ans is None or val<ans: ans=val
    return inA+inB+ans

def solve_slow(N, ea, M, eb):
    adjA=[[] for _ in range(N+1)]
    for u,v in ea: adjA[u].append(v); adjA[v].append(u)
    adjB=[[] for _ in range(M+1)]
    for u,v in eb: adjB[u].append(v); adjB[v].append(u)
    dA=[bfs_dists(adjA,N,x) for x in range(N+1)]
    dB=[bfs_dists(adjB,M,x) for x in range(M+1)]
    best=None
    for a in range(1,N+1):
        for b in range(1,M+1):
            tot=0
            # pairs inside A
            for u in range(1,N+1):
                for v in range(u+1,N+1): tot+=dA[u][v]**2
            for u in range(1,M+1):
                for v in range(u+1,M+1): tot+=dB[u][v]**2
            for u in range(1,N+1):
                for v in range(1,M+1):
                    tot += (dA[a][u]+1+dB[b][v])**2
            if best is None or tot<best: best=tot
    return best

def rand_tree(n):
    return [(random.randint(1,i-1), i) for i in range(2,n+1)]

def main():
    assert solve_fast(3,[(1,2),(2,3)],4,[(1,2),(1,3),(1,4)]) == 96
    assert solve_fast(7,[(1,2),(2,3),(2,4),(4,5),(5,6),(5,7)],5,[(1,2),(1,3),(1,4),(1,5)]) == 551
    print("samples OK")
    random.seed(11); bad=0
    for _ in range(120):
        n=random.randint(1,7); m=random.randint(1,7)
        ea=rand_tree(n); eb=rand_tree(m)
        f=solve_fast(n,ea,m,eb); s=solve_slow(n,ea,m,eb)
        if f!=s:
            bad+=1; print("MISMATCH", n,ea,m,eb,f,s)
    print("random small trees: mismatches =", bad); assert bad==0
    print("joiningnetwork: OK")

main()
