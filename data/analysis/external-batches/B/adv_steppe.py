import sys, itertools, random, time
sys.setrecursionlimit(300000)
sys.path.insert(0,'/Users/dedeepya/Cosine/data/analysis/external-batches/B')

# re-import fast/feasible without running the script body: copy them
def feasible(n, par, w, R, f):
    NEG=-1
    need=[0]*(n+1); cov=[NEG]*(n+1); used=0
    for u in range(n,0,-1):
        if cov[u]>=need[u]: need[u]=NEG
        if need[u]>=0:
            pu=par[u]
            if pu==0 or need[u]+w[u]>R:
                used+=1
                if used>f: return False
                cov[u]=R; need[u]=NEG
        if u>1:
            p,e=par[u],w[u]
            if need[u]>=0 and need[u]+e>need[p]: need[p]=need[u]+e
            if cov[u]-e>cov[p]: cov[p]=cov[u]-e
    return used<=f
def fast(n,par,w,f):
    lo,hi=0,sum(w[2:n+1])
    while lo<hi:
        mid=(lo+hi)//2
        if feasible(n,par,w,mid,f): hi=mid
        else: lo=mid+1
    return lo

def brute_subsets(n,par,w,f):
    INF=float('inf')
    d=[[INF]*(n+1) for _ in range(n+1)]
    for u in range(1,n+1): d[u][u]=0
    for u in range(2,n+1): d[u][par[u]]=d[par[u]][u]=w[u]
    for k in range(1,n+1):
        for i in range(1,n+1):
            v=d[i][k]
            if v==INF: continue
            for j in range(1,n+1):
                if v+d[k][j]<d[i][j]: d[i][j]=v+d[k][j]
    best=INF
    for cs in itertools.combinations(range(1,n+1),min(f,n)):
        worst=max(min(d[u][c] for c in cs) for u in range(1,n+1))
        best=min(best,worst)
    return best

# independent solver: binary search over CANDIDATE DISTANCES, feasibility by
# a completely different formulation: DP over "min centers to cover subtree
# given (deepest uncovered depth, best cover reach)" -- here use an exact
# O(n^2) DP for small n via all-pairs + greedy on sorted-by-depth uncovered.
def min_centers_exact(n,par,w,R):
    # exact min #vertices S s.t. every vertex within R of some s in S.
    # tree => greedy from deepest leaf is optimal; implement DIFFERENTLY:
    # repeatedly take the uncovered vertex farthest from root; place center at
    # the highest ancestor within R of it.
    INF=float('inf')
    d=[[INF]*(n+1) for _ in range(n+1)]
    for u in range(1,n+1): d[u][u]=0
    for u in range(2,n+1): d[u][par[u]]=d[par[u]][u]=w[u]
    for k in range(1,n+1):
        for i in range(1,n+1):
            v=d[i][k]
            if v==INF: continue
            for j in range(1,n+1):
                if v+d[k][j]<d[i][j]: d[i][j]=v+d[k][j]
    depth=[0]*(n+1)
    for u in range(2,n+1): depth[u]=depth[par[u]]+w[u]
    uncov=set(range(1,n+1)); cnt=0
    while uncov:
        v=max(uncov,key=lambda x:depth[x])
        # highest ancestor a of v with d[v][a]<=R
        a=v; cur=v
        while par[cur]!=0 and d[v][par[cur]]<=R:
            cur=par[cur]; a=cur
        cnt+=1
        uncov={x for x in uncov if d[x][a]>R}
    return cnt

def indep(n,par,w,f):
    cands=sorted(set([0]))
    INF=float('inf')
    d=[[INF]*(n+1) for _ in range(n+1)]
    for u in range(1,n+1): d[u][u]=0
    for u in range(2,n+1): d[u][par[u]]=d[par[u]][u]=w[u]
    for k in range(1,n+1):
        for i in range(1,n+1):
            v=d[i][k]
            if v==INF: continue
            for j in range(1,n+1):
                if v+d[k][j]<d[i][j]: d[i][j]=v+d[k][j]
    cands=sorted(set(d[i][j] for i in range(1,n+1) for j in range(1,n+1)))
    lo,hi=0,len(cands)-1
    while lo<hi:
        mid=(lo+hi)//2
        if min_centers_exact(n,par,w,cands[mid])<=f: hi=mid
        else: lo=mid+1
    return cands[lo]

random.seed(7)
bad=0
shapes=['star','path','broom','binary','random','caterpillar']
for t in range(4000):
    n=random.randint(1,12); f=random.randint(1,n)
    sh=random.choice(shapes)
    par=[0]*(n+1); w=[0]*(n+1)
    for i in range(2,n+1):
        if sh=='star': par[i]=1
        elif sh=='path': par[i]=i-1
        elif sh=='broom': par[i]=i-1 if i<=n//2 else max(1,n//2)
        elif sh=='binary': par[i]=i//2
        elif sh=='caterpillar': par[i]= i-1 if i%2==0 else max(1,i-2)
        else: par[i]=random.randint(1,i-1)
        w[i]=random.choice([1,1,2,9999,10000,5000,3])
    a=fast(n,par,w,f); b=brute_subsets(n,par,w,f); c=indep(n,par,w,f)
    if not(a==b==c):
        bad+=1; print("MISMATCH",n,f,sh,par[2:],w[2:],a,b,c)
        if bad>4: break
print("adversarial-shape small trials done, mismatches",bad)

# scale adversarial: pure path, max weights, f=1 and f=2 (worst binary search)
for f in (1,2,3,100000):
    n=100000
    par=[0]*(n+1); w=[0]*(n+1)
    for i in range(2,n+1): par[i]=i-1; w[i]=10000
    t0=time.time(); ans=fast(n,par,w,f)
    print("path n=1e5 w=1e4 f=%d -> %d in %.2fs"%(f,ans,time.time()-t0))
# star
n=100000
par=[0]*(n+1); w=[0]*(n+1)
for i in range(2,n+1): par[i]=1; w[i]=10000
t0=time.time(); print("star f=1 ->",fast(n,par,w,1),"%.2fs"%(time.time()-t0))
# caterpillar w/ alternating tiny/huge weights
n=100000
par=[0]*(n+1); w=[0]*(n+1)
for i in range(2,n+1):
    par[i]=i-1; w[i]= 1 if i%2 else 10000
t0=time.time(); print("caterpillar f=500 ->",fast(n,par,w,500),"%.2fs"%(time.time()-t0))
