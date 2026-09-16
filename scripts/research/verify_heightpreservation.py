"""Height Preservation: grid H (m*n <= 1e6).  Assign S preserving, within every row
and within every column, equality and strict order of H.  Minimise the number of
distinct S values.

Solution: cells equal within a row/column must share an S value -> union-find them.
Between consecutive distinct values in a row (or column) add a DAG edge small->large.
The minimum number of levels is the length of the longest chain, i.e. longest path
in that DAG, computed by a topological-order DP; answer = max level.
O(mn log(mn)) time (sorting each row/column), O(mn) space.

Brute force: for tiny grids, search the minimum number of levels by trying L=1,2,...
and checking satisfiability of all order constraints by brute-force assignment.
"""
import random
from itertools import product

class DSU:
    def __init__(s,n): s.p=list(range(n))
    def f(s,x):
        while s.p[x]!=x: s.p[x]=s.p[s.p[x]]; x=s.p[x]
        return x
    def u(s,a,b):
        a,b=s.f(a),s.f(b)
        if a!=b: s.p[a]=b

def solve(m,n,H):
    N=m*n
    d=DSU(N)
    lines=[]
    for i in range(m): lines.append([i*n+j for j in range(n)])
    for j in range(n): lines.append([i*n+j for i in range(m)])
    for line in lines:
        line.sort(key=lambda c: H[c//n][c%n])
        for a,b in zip(line, line[1:]):
            if H[a//n][a%n]==H[b//n][b%n]: d.u(a,b)
    # build DAG on components
    adj={}; indeg={}
    for line in lines:
        prev=None
        for c in line:
            r=d.f(c)
            adj.setdefault(r,set()); indeg.setdefault(r,0)
            if prev is not None and H[prev//n][prev%n] < H[c//n][c%n]:
                pr=d.f(prev)
                if r not in adj[pr]:
                    adj[pr].add(r); indeg[r]=indeg.get(r,0)+1
            prev=c
    from collections import deque
    lvl={k:1 for k in adj}
    q=deque([k for k in adj if indeg[k]==0])
    seen=0
    while q:
        u=q.popleft(); seen+=1
        for v in adj[u]:
            if lvl[v]<lvl[u]+1: lvl[v]=lvl[u]+1
            indeg[v]-=1
            if indeg[v]==0: q.append(v)
    assert seen==len(adj), "cycle -- impossible"
    return max(lvl.values())

def brute(m,n,H):
    N=m*n
    cons=[]   # (a,b,'eq'/'lt')
    for i in range(m):
        for j in range(n):
            for k in range(j+1,n):
                a,b=i*n+j, i*n+k
                cons.append((a,b,'eq' if H[i][j]==H[i][k] else ('lt' if H[i][j]<H[i][k] else 'gt')))
    for j in range(n):
        for i in range(m):
            for k in range(i+1,m):
                a,b=i*n+j, k*n+j
                cons.append((a,b,'eq' if H[i][j]==H[k][j] else ('lt' if H[i][j]<H[k][j] else 'gt')))
    for L in range(1,N+1):
        for S in product(range(L), repeat=N):
            if len(set(S))!=L: continue
            ok=True
            for a,b,t in cons:
                if t=='eq' and S[a]!=S[b]: ok=False;break
                if t=='lt' and not S[a]<S[b]: ok=False;break
                if t=='gt' and not S[a]>S[b]: ok=False;break
            if ok: return L
    return None

def main():
    assert solve(2,3,[[8,12,17],[17,20,7]])==3
    print("sample OK")
    random.seed(3); bad=0
    for _ in range(300):
        m=random.randint(1,3); n=random.randint(1,3)
        H=[[random.randint(1,3) for _ in range(n)] for _ in range(m)]
        f=solve(m,n,H); b=brute(m,n,H)
        if f!=b:
            bad+=1
            if bad<6: print("MISMATCH", H, f, b)
    print("random 1..3 x 1..3, values 1..3: mismatches =", bad); assert bad==0
    bad=0
    for _ in range(80):
        m=random.randint(2,2); n=random.randint(4,4)
        H=[[random.randint(1,4) for _ in range(n)] for _ in range(m)]
        f=solve(m,n,H); b=brute(m,n,H)
        if f!=b:
            bad+=1; print("MISMATCH", H, f, b)
    print("random 2x4: mismatches =", bad); assert bad==0
    print("heightpreservation: OK")

main()
