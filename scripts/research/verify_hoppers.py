"""hoppers: brute-force check of the claimed formula.

Claim: a single compromised host infects everything iff the graph is connected
AND non-bipartite (propagation = even-length walks).  So the minimum number of
added edges is  k-1  if some component has an odd cycle, else  k,  where k is
the number of connected components (isolated vertices included).

Brute force: try every set of added non-edges in increasing size; for each
resulting graph literally simulate the "infect everything two hops away"
closure from every start vertex.
"""
import itertools, random
from itertools import combinations


def infects_all(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    for s in range(n):
        seen = {s}; stack = [s]
        while stack:
            x = stack.pop()
            for v in adj[x]:
                for w in adj[v]:
                    if w not in seen:
                        seen.add(w); stack.append(w)
        if len(seen) == n:
            return True
    return False


def brute(n, edges):
    es = set(map(lambda e: tuple(sorted(e)), edges))
    non = [e for e in combinations(range(n), 2) if e not in es]
    for k in range(0, len(non) + 1):
        for add in combinations(non, k):
            if infects_all(n, list(es) + list(add)):
                return k
    return None


def formula(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v); adj[v].append(u)
    color = [-1] * n
    comps = 0
    odd = False
    for s in range(n):
        if color[s] != -1:
            continue
        comps += 1
        color[s] = 0; stack = [s]
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if color[y] == -1:
                    color[y] = color[x] ^ 1; stack.append(y)
                elif color[y] == color[x]:
                    odd = True
    return comps - 1 if odd else comps


def run(n, edges, want=None):
    b, f = brute(n, edges), formula(n, edges)
    assert b == f, (n, sorted(edges), 'brute', b, 'formula', f)
    if want is not None:
        assert f == want, (n, edges, f, want)
    return f


# ---- samples (1-indexed in the statement, 0-indexed here) ----
def dec(es): return [(u - 1, v - 1) for u, v in es]

run(3, dec([(1, 2), (2, 3)]), want=1)
run(5, dec([(1,2),(2,3),(3,4),(4,5),(5,1),(1,3),(2,4),(3,5),(4,1),(5,2)]), want=0)
print("samples ok")

# sample 3 is N=12 -- too big to brute force, check the formula only
s3 = dec([(2,3),(3,4),(4,5),(5,2),(6,7),(7,8),(8,9),(9,10),(10,7),
          (9,12),(12,11),(11,6),(12,7)])
assert formula(12, s3) == 3, formula(12, s3)
print("sample 3 formula ok")

# ---- exhaustive over all graphs on 3,4 vertices; random on 5,6 ----
random.seed(7)
tested = 0
for n in (3, 4):
    allp = list(combinations(range(n), 2))
    for mask in range(1 << len(allp)):
        edges = [allp[i] for i in range(len(allp)) if mask >> i & 1]
        run(n, edges); tested += 1
for n in (5, 6):
    allp = list(combinations(range(n), 2))
    for _ in range(400):
        m = random.randint(0, len(allp))
        run(n, random.sample(allp, m)); tested += 1
print("ok:", tested, "graphs agree with the formula")
