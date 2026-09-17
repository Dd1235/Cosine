"""Special Tour -- verification.

Claim:  an N x M closed tour whose consecutive Manhattan distances are all 2 or
3 exists for every N, M except the sixteen pairs
    1xM / Mx1 with M in {1,2,3,4,6,7,8,9}   and   2x2.

Two independent programs below:
  * ham_cycle(N,M): exhaustive DFS (with connectivity / degree pruning) over the
    move graph -- ground truth for small boards, also used to fetch the tours of
    the constant-size blocks;
  * special_tour(N,M): the O(N*M) construction -- cut the board into blocks
    whose sides are 2..5 (never 2x2), take each block's own closed tour, and
    splice a new block into the growing cycle by deleting one edge (u,v) of the
    cycle and one edge (u',v') of the block and adding (u,u') and (v,v').

The checks run here:
  1. both samples;
  2. exhaustive DFS on every board with N*M <= 14 (plus every 1xM with M <= 16)
     agrees with the claimed impossible set;
  3. the construction produces a tour for every remaining N, M <= 24 and every
     produced tour is validated cell-by-cell (permutation of the board, every
     step of Manhattan length 2 or 3, closing step included);
  4. the construction is validated on large boards, up to 200 x 200.
"""
import sys
import time

sys.setrecursionlimit(100000)


# --------------------------------------------------------------- ground truth
def ham_cycle(N, M):
    """exhaustive search for a closed tour of the N x M board (0-indexed)"""
    cells = [(r, c) for r in range(N) for c in range(M)]
    idx = {p: i for i, p in enumerate(cells)}
    n = len(cells)
    if n < 2:
        return None
    adj = [[] for _ in range(n)]
    for i, (r, c) in enumerate(cells):
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) in (2, 3):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < N and 0 <= cc < M:
                        adj[i].append(idx[(rr, cc)])
    if any(len(a) < 2 for a in adj):
        return None
    used = [False] * n
    used[0] = True
    path = [0]
    adjset = [set(a) for a in adj]

    def feasible(cur):
        rem = [i for i in range(n) if not used[i]]
        if not rem:
            return True
        seen = {cur}
        stack = [cur]
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if y not in seen and not used[y]:
                    seen.add(y)
                    stack.append(y)
        if not all(r in seen for r in rem):
            return False
        for r in rem:                       # every unused cell still needs two ends
            cnt = 0
            for y in adj[r]:
                if (not used[y]) or y == 0 or y == cur:
                    cnt += 1
            if cnt < 2:
                return False
        return True

    def dfs(cur):
        if len(path) == n:
            return 0 in adjset[cur]
        if not feasible(cur):
            return False
        for y in sorted((y for y in adj[cur] if not used[y]),
                        key=lambda y: sum(1 for z in adj[y] if not used[z])):
            used[y] = True
            path.append(y)
            if dfs(y):
                return True
            path.pop()
            used[y] = False
        return False

    return [cells[i] for i in path] if dfs(0) else None


# --------------------------------------------------------------- construction
def step_ok(p, q):
    return abs(p[0] - q[0]) + abs(p[1] - q[1]) in (2, 3)


_blocks = {}


def block_cycle(a, b):
    if (a, b) not in _blocks:
        t = ham_cycle(a, b)
        assert t is not None, "block %dx%d has no tour" % (a, b)
        _blocks[(a, b)] = t
    return _blocks[(a, b)]


def parts(x):
    """x == 2 -> [2]; x >= 3 -> parts drawn from {3,4,5}"""
    if x == 2:
        return [2]
    out = []
    while x > 5:
        out.append(3)
        x -= 3
    out.append(x)
    return out


def cycle_to_adj(cyc):
    n = len(cyc)
    return {p: [cyc[(i - 1) % n], cyc[(i + 1) % n]] for i, p in enumerate(cyc)}


def _swap(adj, p, old, new):
    lst = adj[p]
    for i in range(2):
        if lst[i] == old:
            lst[i] = new
            return
    raise AssertionError("edge missing")


def merge(adj, near, newcyc):
    """splice the cycle newcyc into adj through an edge of the block `near`"""
    newadj = cycle_to_adj(newcyc)
    done = set()
    for u in near:
        if u not in adj:
            continue
        for v in adj[u]:
            if v not in near:
                continue
            key = (min(u, v), max(u, v))
            if key in done:
                continue
            done.add(key)
            for up in newcyc:
                for vp in newadj[up]:
                    if step_ok(u, up) and step_ok(v, vp):
                        _swap(adj, u, v, up)
                        _swap(adj, v, u, vp)
                        for p in newcyc:
                            adj[p] = list(newadj[p])
                        _swap(adj, up, vp, u)
                        _swap(adj, vp, up, v)
                        return True
    return False


def walk(adj):
    start = next(iter(adj))
    out = [start]
    prev, cur = None, start
    while True:
        a, b = adj[cur]
        nxt = a if a != prev else b
        if nxt == start:
            return out
        out.append(nxt)
        prev, cur = cur, nxt


def row_tour(M):
    """single row: M == 5, or M >= 10 as a 10..14 base plus blocks of five"""
    if M == 5:
        return [(0, c) for c in (0, 2, 4, 1, 3)]
    if M < 10:
        return None
    base = 10 + (M - 10) % 5
    adj = cycle_to_adj(ham_cycle(1, base))
    col = base
    while col < M:
        blk = [(0, col + c) for c in (0, 2, 4, 1, 3)]
        near = [(0, c) for c in range(max(0, col - 3), col)]
        assert merge(adj, near, blk), ("row merge failed", M, col)
        col += 5
    return walk(adj)


def special_tour(N, M):
    """a closed tour of the N x M board, 0-indexed, or None"""
    if N == 1 and M == 1:
        return None
    if N == 1:
        return row_tour(M)
    if M == 1:
        t = row_tour(N)
        return None if t is None else [(c, r) for (r, c) in t]
    if N == 2 and M == 2:
        return None
    rp, cp = parts(N), parts(M)
    roff, coff, s = [], [], 0
    for a in rp:
        roff.append(s)
        s += a
    s = 0
    for b in cp:
        coff.append(s)
        s += b

    def cells(i, j):
        return [(roff[i] + r, coff[j] + c)
                for r in range(rp[i]) for c in range(cp[j])]

    adj = cycle_to_adj([(roff[0] + r, coff[0] + c)
                        for (r, c) in block_cycle(rp[0], cp[0])])
    for i in range(len(rp)):
        for j in range(len(cp)):
            if i == 0 and j == 0:
                continue
            blk = [(roff[i] + r, coff[j] + c)
                   for (r, c) in block_cycle(rp[i], cp[j])]
            near = cells(i, j - 1) if j > 0 else cells(i - 1, j)
            if not merge(adj, near, blk):
                alt = cells(i - 1, j) if (j > 0 and i > 0) else None
                assert alt is not None and merge(adj, alt, blk), \
                    "merge failed at %s" % ((N, M, i, j),)
    return walk(adj)


def check(N, M, tour):
    assert len(tour) == N * M, ("length", N, M)
    assert len(set(tour)) == N * M, ("repeated cell", N, M)
    for (r, c) in tour:
        assert 0 <= r < N and 0 <= c < M, ("off board", N, M)
    for k in range(len(tour)):
        p, q = tour[k], tour[(k + 1) % len(tour)]
        d = abs(p[0] - q[0]) + abs(p[1] - q[1])
        assert d in (2, 3), ("bad step", N, M, p, q, d)


IMPOSSIBLE = set()
for m in (1, 2, 3, 4, 6, 7, 8, 9):
    IMPOSSIBLE.add((1, m))
    IMPOSSIBLE.add((m, 1))
IMPOSSIBLE.add((2, 2))


def main():
    t0 = time.time()

    # 1 -- samples
    t = special_tour(2, 3)
    check(2, 3, t)
    print("sample 1 (2x3): tour %s" %
          " ".join("(%d,%d)" % (r + 1, c + 1) for r, c in t))
    assert special_tour(1, 1) is None
    print("sample 2 (1x1): -1")

    # 2 -- exhaustive search agrees with the claimed impossible set
    todo = set()
    for N in range(1, 17):
        for M in range(1, 17):
            if N * M <= 16:
                todo.add((N, M))
    for M in range(1, 21):
        todo.add((1, M))
        todo.add((M, 1))
    todo |= {(2, 9), (2, 10), (3, 6), (4, 5), (5, 5)}
    checked = 0
    for (N, M) in sorted(todo):
        got = ham_cycle(N, M) is not None
        assert got == ((N, M) not in IMPOSSIBLE), ("DFS disagrees", N, M)
        checked += 1
    print("exhaustive DFS: %d small boards agree with the claimed answer set "
          "(the 16 impossible pairs are 1xM/Mx1 for M in {1,2,3,4,6,7,8,9} "
          "and 2x2)" % checked)

    # 3 -- the construction, validated everywhere it should succeed
    built = 0
    for N in range(1, 25):
        for M in range(1, 25):
            t = special_tour(N, M)
            if (N, M) in IMPOSSIBLE:
                assert t is None, ("built an impossible board", N, M)
                continue
            assert t is not None, ("construction failed", N, M)
            check(N, M, t)
            built += 1
    print("construction: %d boards up to 24x24 built and validated cell by cell"
          % built)

    # 4 -- scale
    for (N, M) in [(200, 200), (199, 197), (1, 200), (200, 1), (2, 200),
                   (200, 2), (3, 199), (197, 5), (1, 196), (123, 77)]:
        t = special_tour(N, M)
        assert t is not None
        check(N, M, t)
    print("construction: 200x200 and nine other large boards validated "
          "(%.1fs total)" % (time.time() - t0))
    print("PASS")


main()
