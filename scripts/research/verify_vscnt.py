"""
codechef-vscnt  (Virtual Sets Counting)

Claim derived:
  Let T be the current set.  score(T) = 0 unless T is LCA-closed (f(T)=T).
  If T is LCA-closed, let F be the virtual forest on T (parent of v = nearest
  proper ancestor of v inside T).  Then

      f(S) = T  <=>  S contains every vertex of T with <= 1 child in F,

  so score(T) = 2^B, B = #{v in T : v has >= 2 children in F}.

Why: every F-leaf must be in S (nothing else can create it), and a vertex with
2+ F-children then automatically has 2+ child subtrees hit by S, so it is an LCA
of two S-elements and is free to be in S or not.  A vertex with exactly one
F-child is never an LCA of two elements of f(S), so it must be in S.

Maintenance: keep T sorted by tin.  cnt[u] = #consecutive pairs (v_i,v_{i+1})
in tin order with lca = u.  Standard virtual-tree fact: for u in T the number of
F-children of u equals cnt[u]; for u not in T it is cnt[u]+1.  So
  B        = #{u : cnt[u] >= 2}                       (valid when T is closed)
  closed   <=>  every pair's lca is in T  <=>  bad == 0
Both are O(1) to update per changed adjacent pair, and a toggle of x changes
only the pairs around x -- plus the whole block cnt[x] flips good/bad at once,
handled with a single counter read.  O((N+Q) log N) overall.

This script: (a) checks both samples, (b) cross-checks the incremental solver
against a from-scratch recompute and against a subset-enumeration brute force
on random small trees.
"""
import random, sys
from bisect import insort, bisect_left
from itertools import combinations

MOD = 998244353

# ---------------- tree utilities ----------------
def build(n, edges):
    adj = [[] for _ in range(n + 1)]
    for u, v in edges:
        adj[u].append(v); adj[v].append(u)
    par = [0] * (n + 1); depth = [0] * (n + 1)
    tin = [0] * (n + 1); tout = [0] * (n + 1)
    timer = 0
    order = []
    st = [(1, 0)]
    par[1] = 0
    seen = [False] * (n + 1)
    while st:
        v, phase = st.pop()
        if phase == 0:
            if seen[v]:
                continue
            seen[v] = True
            tin[v] = timer; timer += 1
            order.append(v)
            st.append((v, 1))
            for w in adj[v]:
                if not seen[w]:
                    par[w] = v; depth[w] = depth[v] + 1
                    st.append((w, 0))
        else:
            tout[v] = timer
    return par, depth, tin, tout

def make_lca(n, par, depth):
    LOG = max(1, n.bit_length())
    up = [[0] * (n + 1) for _ in range(LOG)]
    up[0] = par[:]
    for k in range(1, LOG):
        prev = up[k - 1]; cur = up[k]
        for v in range(1, n + 1):
            cur[v] = prev[prev[v]]
    def lca(a, b):
        if depth[a] < depth[b]:
            a, b = b, a
        d = depth[a] - depth[b]
        k = 0
        while d:
            if d & 1:
                a = up[k][a]
            d >>= 1; k += 1
        if a == b:
            return a
        for k in range(LOG - 1, -1, -1):
            if up[k][a] != up[k][b]:
                a = up[k][a]; b = up[k][b]
        return par[a]
    return lca

# ---------------- incremental solver (the intended one) ----------------
class Solver:
    def __init__(self, n, edges):
        self.n = n
        self.par, self.depth, self.tin, self.tout = build(n, edges)
        self.lca = make_lca(n, self.par, self.depth)
        self.keys = []          # tins of members, sorted
        self.byTin = [0] * (n + 1)
        for v in range(1, n + 1):
            self.byTin[self.tin[v]] = v
        self.inT = [False] * (n + 1)
        self.cnt = [0] * (n + 1)
        self.bad = 0            # #adjacent pairs whose lca is outside T
        self.B = 0              # #{u : cnt[u] >= 2}
        self.pw = [1] * (n + 2)
        for i in range(1, n + 2):
            self.pw[i] = self.pw[i - 1] * 2 % MOD

    def _addpair(self, a, b):
        l = self.lca(a, b)
        if self.cnt[l] == 1:
            self.B += 1
        self.cnt[l] += 1
        if not self.inT[l]:
            self.bad += 1

    def _delpair(self, a, b):
        l = self.lca(a, b)
        self.cnt[l] -= 1
        if self.cnt[l] == 1:
            self.B -= 1
        if not self.inT[l]:
            self.bad -= 1

    def toggle(self, x):
        t = self.tin[x]
        i = bisect_left(self.keys, t)
        if self.inT[x]:
            p = self.byTin[self.keys[i - 1]] if i > 0 else None
            q = self.byTin[self.keys[i + 1]] if i + 1 < len(self.keys) else None
            if p is not None:
                self._delpair(p, x)
            if q is not None:
                self._delpair(x, q)
            self.keys.pop(i)
            self.inT[x] = False
            self.bad += self.cnt[x]          # x's own block turns bad
            if p is not None and q is not None:
                self._addpair(p, q)
        else:
            p = self.byTin[self.keys[i - 1]] if i > 0 else None
            q = self.byTin[self.keys[i]] if i < len(self.keys) else None
            if p is not None and q is not None:
                self._delpair(p, q)
            self.inT[x] = True
            self.bad -= self.cnt[x]          # x's own block turns good
            insort(self.keys, t)
            if p is not None:
                self._addpair(p, x)
            if q is not None:
                self._addpair(x, q)
        return 0 if self.bad else self.pw[self.B]

# ---------------- from-scratch recompute of the same formula ----------------
def recompute(sol, members):
    seq = sorted(members, key=lambda v: sol.tin[v])
    cnt = {}
    bad = 0
    ms = set(members)
    for a, b in zip(seq, seq[1:]):
        l = sol.lca(a, b)
        cnt[l] = cnt.get(l, 0) + 1
        if l not in ms:
            bad += 1
    if bad:
        return 0
    B = sum(1 for u, c in cnt.items() if c >= 2)
    return pow(2, B, MOD)

# ---------------- brute force: enumerate every subset ----------------
def closure(S, lca):
    cur = set(S)
    while True:
        add = set()
        for x, y in combinations(cur, 2):
            l = lca(x, y)
            if l not in cur:
                add.add(l)
        if not add:
            return cur
        cur |= add

def brute(members, lca):
    Tset = set(members)
    lst = sorted(Tset)
    total = 0
    for mask in range(1 << len(lst)):
        S = {lst[i] for i in range(len(lst)) if mask >> i & 1}
        if closure(S, lca) == Tset:
            total += 1
    return total % MOD

# ---------------- samples ----------------
def run_sample(n, edges, queries):
    s = Solver(n, edges)
    return [s.toggle(x) for x in queries]

def samples():
    ok = True
    got = run_sample(3, [(1, 2), (1, 3)], [1, 1, 2, 3, 1])
    exp = [1, 1, 1, 0, 2]
    print("sample1", got, "expected", exp); ok &= got == exp
    got = run_sample(6, [(1, 2), (2, 3), (2, 4), (3, 5), (3, 6)],
                     [6, 2, 4, 5, 3, 1, 6, 5, 2])
    exp = [1, 1, 2, 0, 4, 4, 2, 2, 0]
    print("sample2", got, "expected", exp); ok &= got == exp
    return ok

# ---------------- randomized cross-check ----------------
def random_tests(iters=400, seed=1):
    rng = random.Random(seed)
    for it in range(iters):
        n = rng.randint(2, 9)
        edges = [(rng.randint(1, v - 1), v) for v in range(2, n + 1)]
        # relabel so the root is not always a path start
        perm = list(range(1, n + 1)); rng.shuffle(perm)
        lab = {i + 1: perm[i] for i in range(n)}
        edges = [(lab[u], lab[v]) for u, v in edges]
        sol = Solver(n, edges)
        members = set()
        for _ in range(rng.randint(1, 14)):
            x = rng.randint(1, n)
            fast = sol.toggle(x)
            if x in members:
                members.discard(x)
            else:
                members.add(x)
            rec = recompute(sol, members)
            bf = brute(members, sol.lca)
            if not (fast == rec == bf):
                print("MISMATCH it=%d n=%d edges=%s T=%s fast=%s recompute=%s brute=%s"
                      % (it, n, edges, sorted(members), fast, rec, bf))
                return False
    return True

if __name__ == "__main__":
    a = samples()
    b = random_tests()
    print("samples ok:", a)
    print("random cross-check ok:", b)
    sys.exit(0 if (a and b) else 1)
