"""naturereserve: MST over (E_ij + L) with the S initial stations merged into one component,
vs brute force over all edge subsets (checks every station reachable from some initial station)."""
import random, itertools

def solve(n, edges, L, sources):
    par = list(range(n))
    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    def u(a, b):
        a, b = f(a), f(b)
        if a == b: return False
        par[a] = b; return True
    comp = n - 1                      # components to merge away
    for s in sources[1:]:
        if u(sources[0], s): comp -= 1
    tot = 0
    for w, a, b in sorted((w + L, a, b) for a, b, w in edges):
        if u(a, b):
            tot += w; comp -= 1
    return tot if comp == 0 else None  # graph is connected by statement, so never None

def brute(n, edges, L, sources):
    best = None
    for r in range(len(edges) + 1):
        for sub in itertools.combinations(range(len(edges)), r):
            par = list(range(n))
            def f(x):
                while par[x] != x: par[x] = par[par[x]]; x = par[x]
                return x
            for i in sub:
                a, b, w = edges[i]
                par[f(a)] = f(b)
            for s in sources: par[f(s)] = f(sources[0])
            if len({f(v) for v in range(n)}) == 1:
                c = sum(edges[i][2] + L for i in sub)
                if best is None or c < best: best = c
    return best

# sample
edges = [(0,1,4),(0,2,8),(0,3,1),(1,2,2),(1,3,5),(2,3,20)]
assert solve(4, edges, 10, [2]) == 37, solve(4, edges, 10, [2])
random.seed(11)
bad = 0
for t in range(300):
    n = random.randint(2, 6)
    alled = [(a,b) for a in range(n) for b in range(a+1, n)]
    random.shuffle(alled)
    m = random.randint(n-1, len(alled))
    es = [(a,b,random.randint(1,9)) for a,b in alled[:m]]
    # ensure connected
    par=list(range(n))
    def f(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for a,b,w in es: par[f(a)]=f(b)
    if len({f(v) for v in range(n)})>1: continue
    L = random.randint(1,5)
    k = random.randint(1,n)
    src = random.sample(range(n), k)
    s, b = solve(n, es, L, src), brute(n, es, L, src)
    if s != b:
        bad += 1; print("MISMATCH", n, es, L, src, s, b)
print("sample ok (37); mismatches =", bad)
