"""Checks for kattis-colourful.

Two claims are tested.

(1) Feasibility: with n >= 2 and the graph connected, s can be turned into t iff
    every colour used in t already occurs in s (colours are only ever copied, so
    the set of live colours never grows); n == 1 needs s == t.  Checked by BFS
    over the whole configuration space of every connected graph on 2..4 vertices
    with k <= 3 colours.

(2) Construction within the 20000-step budget, in two phases.
    Phase A (fix the multiset): while some colour occurs fewer times than t
    needs, take a vertex whose colour is in surplus, BFS to the nearest vertex
    whose colour is in deficit, and walk the surplus one edge at a time towards
    it (each move is one vertex copying its neighbour).  Only surplus vertices
    are ever overwritten, so no needed colour is lost.
    Phase B (permute): the multiset now matches, so fix an assignment of holders
    to targets and realise that permutation with adjacent swaps on a spanning
    tree - a swap is legal because the step is simultaneous, both endpoints
    reading the other's old colour.  Peel leaves in reverse DFS order so the
    working set stays connected.
    Every emitted step is replayed and checked against the rules, and the step
    count is reported for adversarial n = 100 instances.
"""
import random
from collections import deque
from itertools import product


def feasible(n, adj, s, t):
    if n == 1:
        return s == t
    return set(t) <= set(s)


def brute_reachable(n, adj, s, t):
    start = tuple(s)
    goal = tuple(t)
    seen = {start}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            return True
        opts = []
        for v in range(n):
            opts.append(sorted({cur[v]} | {cur[u] for u in adj[v]}))
        for nxt in product(*opts):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return False


def construct(n, adj, s, t):
    """Returns the list of configurations C_0..C_L (C_0 = s, C_L = t)."""
    cur = list(s)
    seq = [tuple(cur)]

    def emit(newcfg):
        seq.append(tuple(newcfg))

    # ---- phase A: make the colour multiset equal to t's ----
    from collections import Counter
    need = Counter(t)

    def counts():
        return Counter(cur)

    while True:
        have = counts()
        deficit = [c for c in need if have[c] < need[c]]
        if not deficit:
            break
        defset = set(deficit)
        surplus = [v for v in range(n) if have[cur[v]] > need.get(cur[v], 0)]
        assert surplus
        # BFS from all surplus vertices to the nearest deficit-coloured vertex
        src = surplus[0]
        prev = {src: None}
        q = deque([src])
        hit = None
        while q:
            v = q.popleft()
            if cur[v] in defset:
                hit = v
                break
            for u in adj[v]:
                if u not in prev:
                    prev[u] = v
                    q.append(u)
        assert hit is not None
        path = []
        v = hit
        while v is not None:
            path.append(v)
            v = prev[v]
        path.reverse()           # src ... hit
        path = path[::-1]        # hit ... src  (walk the surplus towards hit)
        # path[-1] = src is the surplus vertex; move it one edge at a time
        for i in range(len(path) - 1, 0, -1):
            a, b = path[i], path[i - 1]   # a copies b
            cur[a] = cur[b]
            emit(cur)
            h2 = counts()
            if h2[cur[a]] <= need.get(cur[a], 0):
                pass
            # stop as soon as the deficit shrank
            if Counter(cur)[cur[a]] <= need.get(cur[a], 0):
                break

    # ---- phase B: permute into place ----
    # spanning tree by BFS
    par = [-1] * n
    order = []
    seen = [False] * n
    seen[0] = True
    q = deque([0])
    while q:
        v = q.popleft()
        order.append(v)
        for u in adj[v]:
            if not seen[u]:
                seen[u] = True
                par[u] = v
                q.append(u)
    kids = [[] for _ in range(n)]
    for v in range(n):
        if par[v] >= 0:
            kids[par[v]].append(v)
    # DFS preorder (removing in reverse keeps the rest connected)
    pre = []
    st = [0]
    while st:
        v = st.pop()
        pre.append(v)
        for u in kids[v]:
            st.append(u)

    token = list(range(n))           # token[v] = which holder currently sits at v
    colour_of_token = list(cur)
    # assignment: for each vertex, which token must end there
    by_colour = {}
    for v in range(n):
        by_colour.setdefault(cur[v], []).append(v)
    want = [None] * n
    ptr = {c: 0 for c in by_colour}
    for v in range(n):
        c = t[v]
        want[v] = by_colour[c][ptr[c]]
        ptr[c] += 1

    alive = [True] * n
    for v in reversed(pre):
        if token[v] != want[v]:
            # find the holder inside the still-alive part and walk it to v
            src = next(u for u in range(n) if alive[u] and token[u] == want[v])
            # path src -> v inside alive vertices
            prev = {src: None}
            q = deque([src])
            while q:
                x = q.popleft()
                if x == v:
                    break
                for y in adj[x]:
                    if alive[y] and y not in prev:
                        prev[y] = x
                        q.append(y)
            path = []
            x = v
            while x is not None:
                path.append(x)
                x = prev[x]
            path.reverse()
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                token[a], token[b] = token[b], token[a]
                cur[a], cur[b] = cur[b], cur[a]
                emit(cur)
        alive[v] = False
    return seq


def check_sequence(n, adj, s, t, seq):
    assert list(seq[0]) == list(s), "does not start at s"
    assert list(seq[-1]) == list(t), "does not end at t"
    for i in range(1, len(seq)):
        a, b = seq[i - 1], seq[i]
        for v in range(n):
            assert b[v] == a[v] or b[v] in (a[u] for u in adj[v]), "illegal step"
    return len(seq) - 1


def all_connected_graphs(n):
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    for mask in range(1 << len(edges)):
        adj = [[] for _ in range(n)]
        for b, (i, j) in enumerate(edges):
            if mask >> b & 1:
                adj[i].append(j)
                adj[j].append(i)
        seen = {0}
        q = [0]
        while q:
            v = q.pop()
            for u in adj[v]:
                if u not in seen:
                    seen.add(u)
                    q.append(u)
        if len(seen) == n:
            yield adj


def main():
    # (1) feasibility criterion, exhaustively
    bad = 0
    for n in range(1, 5):
        for adj in all_connected_graphs(n):
            for k in range(1, 4):
                for s in product(range(k), repeat=n):
                    for t in product(range(k), repeat=n):
                        got = feasible(n, adj, list(s), list(t))
                        exp = brute_reachable(n, adj, list(s), list(t))
                        if got != exp:
                            bad += 1
                            if bad < 5:
                                print("CRITERION MISMATCH", adj, s, t, got, exp)
    print("criterion over all connected graphs n<=4, k<=3: %s"
          % ("OK" if bad == 0 else "%d FAILURES" % bad))

    # (2) construction on random graphs, validated step by step
    rng = random.Random(9)
    worst = 0
    for trial in range(300):
        n = rng.randint(2, 9)
        k = rng.randint(1, 4)
        adj = [[] for _ in range(n)]
        perm = list(range(n))
        rng.shuffle(perm)
        for i in range(1, n):
            j = perm[rng.randrange(i)]
            adj[perm[i]].append(j)
            adj[j].append(perm[i])
        for _ in range(rng.randint(0, n)):
            a, b = rng.randrange(n), rng.randrange(n)
            if a != b and b not in adj[a]:
                adj[a].append(b)
                adj[b].append(a)
        s = [rng.randrange(k) for _ in range(n)]
        t = [rng.choice(s) for _ in range(n)]
        seq = construct(n, adj, s, t)
        worst = max(worst, check_sequence(n, adj, s, t, seq))
    print("300 random small instances constructed and replayed OK (max %d steps)" % worst)

    # (3) adversarial n = 100 shapes against the 20000-step budget
    worst = 0
    for shape in ("path", "star", "random", "cycle"):
        for trial in range(20):
            n, k = 100, 100
            adj = [[] for _ in range(n)]

            def link(a, b):
                adj[a].append(b)
                adj[b].append(a)
            if shape == "path":
                for i in range(n - 1):
                    link(i, i + 1)
            elif shape == "star":
                for i in range(1, n):
                    link(0, i)
            elif shape == "cycle":
                for i in range(n):
                    link(i, (i + 1) % n)
            else:
                for i in range(1, n):
                    link(i, random.randrange(i))
            s = [rng.randrange(k) for _ in range(n)]
            if trial % 3 == 0:
                s = [0] * n
                s[0] = 1
                t = [1] * n
            elif trial % 3 == 1:
                t = list(reversed(s))
            else:
                t = [rng.choice(s) for _ in range(n)]
            seq = construct(n, adj, s, t)
            steps = check_sequence(n, adj, s, t, seq)
            worst = max(worst, steps)
    print("n=100 adversarial instances: max %d steps (budget 20000)" % worst)


if __name__ == "__main__":
    main()
