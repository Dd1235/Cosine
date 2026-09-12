"""kattis-kindergarten2 (ICPC World Finals 2024, "Kindergarten") -- verification.

Restatement.  Kid i is jealous of j[i] (j[i] < i for i >= 2, i.e. the jealousy
map is a tree rooted at kid 1 with parent(i) = j[i]; kid 1's j[1] is arbitrary,
so the functional graph i -> j[i] is that tree plus one back edge, giving
exactly one cycle: the root path 1 -> ... -> j[1]).  Kid i likes l[i].
An order is safe iff for every kid i:

    pos[j[i]] < pos[i]                       ("envied kid already went"), or
    pos[i] < pos[l[i]] < pos[j[i]]           ("liked kid strictly in between").

So every kid picks one of two sets of precedence edges:
    option A (i not inverted):  j[i] -> i
    option B (i inverted):      i -> l[i],  l[i] -> j[i]   (and i -> j[i])
and a safe order exists iff some choice makes the union a DAG; any topological
order of that DAG is an answer.

Algorithm (solve()).  Start with every kid on option A: the edge set is exactly
the jealousy graph reversed, whose only cycle is the root path plus the back
edge.  Repeatedly: topologically sort; if a cycle remains, at least one kid on
that cycle must be flipped to option B, so branch over the cycle's still-uncut
edges j[v] -> v.  Flipping v adds v -> l[v] and l[v] -> j[v]; that creates a new
cycle exactly when j[v] can still reach l[v] (l[v] a descendant of j[v] whose
tree path is unbroken), and the same rule recurses on that smaller cycle.
Branching over the edges of a cycle is complete (every solution must cut one of
them), so "no branch succeeds" means impossible.  Each level's work is
proportional to its own cycle, whose edges are never revisited deeper, so the
intended implementation is O(n) / O(n log n) (DFS numbering + a structure for
"is l[v] still reachable from j[v]"); n <= 200000.

This file checks: the two official samples, a permutation brute force on all
small instances, a subset brute force on larger random ones, and timing at the
maximum n.
"""
import itertools, random, sys, time
from collections import deque


# ---------- condition & brute forces -------------------------------------
def check(order, j, l):
    n = len(order)
    pos = [0] * (n + 1)
    for k, v in enumerate(order):
        pos[v] = k
    for a in range(1, n + 1):
        if pos[j[a]] < pos[a]:
            continue
        if pos[a] < pos[l[a]] < pos[j[a]]:
            continue
        return False
    return True


def brute(n, j, l):
    """slow reference: try every permutation"""
    for perm in itertools.permutations(range(1, n + 1)):
        if check(perm, j, l):
            return list(perm)
    return None


def edges_of(n, j, l, S):
    E = []
    for i in range(1, n + 1):
        if i in S:
            E += [(i, l[i]), (l[i], j[i]), (i, j[i])]
        else:
            E += [(j[i], i)]
    return E


def topo(n, E):
    adj = [[] for _ in range(n + 1)]
    indeg = [0] * (n + 1)
    for u, v in E:
        adj[u].append(v)
        indeg[v] += 1
    q = deque(x for x in range(1, n + 1) if indeg[x] == 0)
    out = []
    while q:
        u = q.popleft()
        out.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return out if len(out) == n else None


def subset_brute(n, j, l):
    """reference: try every option assignment"""
    for m in range(1 << n):
        S = set(i + 1 for i in range(n) if m >> i & 1)
        o = topo(n, edges_of(n, j, l, S))
        if o is not None:
            return o
    return None


# ---------- the solution --------------------------------------------------
def find_cycle(n, E):
    adj = [[] for _ in range(n + 1)]
    for u, v in E:
        adj[u].append(v)
    color = [0] * (n + 1)
    par = [0] * (n + 1)
    for s in range(1, n + 1):
        if color[s]:
            continue
        color[s] = 1
        st = [(s, iter(adj[s]))]
        while st:
            u, it = st[-1]
            for v in it:
                if color[v] == 0:
                    color[v] = 1
                    par[v] = u
                    st.append((v, iter(adj[v])))
                    break
                if color[v] == 1:
                    cyc = [v]
                    x = u
                    while x != v:
                        cyc.append(x)
                        x = par[x]
                    cyc.reverse()
                    return cyc
            else:
                color[u] = 2
                st.pop()
    return None


def solve(n, j, l, budget=None):
    """returns a safe order, or None if impossible"""
    seen = set()
    stats = [0]

    def rec(S):
        stats[0] += 1
        if budget and stats[0] > budget:
            raise RuntimeError("budget exceeded")
        if S in seen:
            return None
        seen.add(S)
        E = edges_of(n, j, l, S)
        cyc = find_cycle(n, E)
        if cyc is None:
            return topo(n, E)
        for k in range(len(cyc)):                 # branch over the cycle's cuttable edges
            u, v = cyc[k], cyc[(k + 1) % len(cyc)]
            if v not in S and j[v] == u:
                r = rec(S | {v})
                if r:
                    return r
        return None

    r = rec(frozenset())
    return r, stats[0]


# ---------- tests ---------------------------------------------------------
def gen(n, rng, kind="rand"):
    j = [0] * (n + 1)
    l = [0] * (n + 1)
    for i in range(2, n + 1):
        if kind == "star":
            j[i] = 1
        elif kind == "chain":
            j[i] = i - 1
        elif kind == "narrow":
            j[i] = rng.randrange(max(1, i - 3), i)
        else:
            j[i] = rng.randrange(1, i)
    j[1] = rng.randrange(2, n + 1)
    for i in range(1, n + 1):
        while True:
            c = rng.randrange(1, n + 1)
            if c != i and c != j[i]:
                l[i] = c
                break
    return j, l


def all_instances(n):
    jr = [range(2, n + 1)] + [range(1, i) for i in range(2, n + 1)]
    for js in itertools.product(*jr):
        j = [0] + list(js)
        lr = [[c for c in range(1, n + 1) if c != i and c != j[i]] for i in range(1, n + 1)]
        for ls in itertools.product(*lr):
            yield j, [0] + list(ls)


def main():
    # 1. official samples
    s1 = (4, [0, 4, 1, 2, 2], [0, 2, 4, 4, 1])
    s2 = (4, [0, 2, 1, 2, 1], [0, 3, 4, 1, 2])
    o1, _ = solve(*s1)
    o2, _ = solve(*s2)
    assert o1 is not None and check(o1, s1[1], s1[2]), o1
    assert o2 is None
    print("sample 1 ->", " ".join(map(str, o1)), "(judge printed 1 2 3 4; any safe order is accepted)")
    print("sample 2 -> impossible (matches judge)")

    # 2. exhaustive n = 3, 4 against the permutation brute force
    for n in (3, 4):
        tot = solv = bad = 0
        for j, l in all_instances(n):
            tot += 1
            b = brute(n, j, l)
            c, _ = solve(n, j, l)
            if c is not None:
                assert check(c, j, l), (j, l, c)
            if (b is None) != (c is None):
                bad += 1
            solv += b is not None
        print("exhaustive n=%d: %d instances, %d solvable, %d mismatches vs permutation brute"
              % (n, tot, solv, bad))

    # 3. exhaustive n = 5 against the subset brute force
    tot = solv = bad = 0
    for j, l in all_instances(5):
        tot += 1
        b = subset_brute(5, j, l)
        c, _ = solve(5, j, l)
        if c is not None:
            assert check(c, j, l), (j, l, c)
        if (b is None) != (c is None):
            bad += 1
        solv += b is not None
        if tot % 8000 == 0:
            sys.stdout.write("  ... %d\r" % tot); sys.stdout.flush()
    print("exhaustive n=5: %d instances, %d solvable, %d mismatches vs subset brute" % (tot, solv, bad))

    # 4. random cross-checks, several tree shapes
    rng = random.Random(20240)
    for kind in ("rand", "star", "chain", "narrow"):
        for n in (6, 7, 8, 9, 10):
            bad = tot = imp = 0
            worst = 0
            for _ in range(1500):
                j, l = gen(n, rng, kind)
                tot += 1
                b = brute(n, j, l) if n <= 8 else subset_brute(n, j, l)
                c, calls = solve(n, j, l)
                worst = max(worst, calls)
                if c is not None:
                    assert check(c, j, l), (j, l, c)
                else:
                    imp += 1
                if (b is None) != (c is None):
                    bad += 1
                    print("   MISMATCH", j[1:], l[1:], b, c)
            print("random %-6s n=%2d: %d instances, %d impossible, %d mismatches, max %d search nodes"
                  % (kind, n, tot, imp, bad, worst))

    # 5. the stated limit
    for kind in ("rand", "chain", "star", "narrow"):
        j, l = gen(200000, random.Random(7), kind)
        t = time.time()
        o, calls = solve(200000, j, l)
        dt = time.time() - t
        ok = o is not None and check(o, j, l)
        print("n=200000 %-6s: %s in %.2fs, %d search nodes (each node is one O(n) pass)"
              % (kind, "safe order verified" if ok else "IMPOSSIBLE", dt, calls))


if __name__ == "__main__":
    main()
