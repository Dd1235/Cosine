"""kattis-slidingblocks -- verification.

N x M board (N,M,B <= 4e5).  The target blocks form a tree under 4-adjacency;
the first listed block is already on the board.  A move injects a block from
one of the four edges along a given row/column; it travels until it bumps into
an existing block and stops in the cell just before it (a move that adds no
block is illegal).  Decide reachability and print the B-1 moves.

solve()  -- the judges' characterisation, implemented:
  * Root the tree at block 1.  Any legal history keeps the placed set connected
    and containing the root (every new block touches an existing one), so the
    placed set is always a root-containing subtree; hence when u is added its
    tree-neighbour that it bumps into cannot be a child (a child's own path to
    the root would run through the still-absent u), so it must be par(u).
    That FIXES the move for every u: it enters from the edge opposite par(u),
    along u's row if par(u) is horizontal, u's column if vertical.
  * Two orderings follow: par(u) before u, and every target block on the ray
    from u to its entry edge after u.  The second is O(B^2) edges written out
    in full, so only the edge to the NEAREST block on that ray is kept.
  * Kahn topological sort; a cycle means impossible.
Time O(B log B) (the sorting to find ray-neighbours), space O(B).

brute(...) -- BFS over the 2^B subsets of placed blocks, trying every one of
the 2(N+M) moves from each state, keeping only moves that land on an unplaced
TARGET cell (landing anywhere else can never be undone).  Ground truth for
tiny boards.

simulate(...) -- replays a produced move list on a real grid and checks the
final board equals the target exactly.
"""
import random
import sys
from collections import deque

DIRS = {'<': (0, 1), '>': (0, -1), '^': (1, 0), 'v': (-1, 0)}


# ------------------------------------------------------------------ solver
def solve(N, M, blocks):
    """blocks: list of (r,c), 1-indexed, blocks[0] = the pre-placed one.
    returns None (impossible) or a list of (char, k)."""
    B = len(blocks)
    idx = {p: i for i, p in enumerate(blocks)}
    if len(idx) != B:
        return None                                  # duplicate cells

    # ---- root the tree at block 0
    par = [-1] * B
    order = []
    seen = [False] * B
    seen[0] = True
    dq = deque([0])
    while dq:
        u = dq.popleft()
        order.append(u)
        r, c = blocks[u]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            w = idx.get((r + dr, c + dc))
            if w is not None and not seen[w]:
                seen[w] = True
                par[w] = u
                dq.append(w)
    if len(order) != B:
        return None                                  # not connected

    # ---- lines
    by_row, by_col = {}, {}
    for i, (r, c) in enumerate(blocks):
        by_row.setdefault(r, []).append((c, i))
        by_col.setdefault(c, []).append((r, i))
    for v in by_row.values():
        v.sort()
    for v in by_col.values():
        v.sort()
    rank_row, rank_col = {}, {}
    for v in by_row.values():
        for k, (_, i) in enumerate(v):
            rank_row[i] = k
    for v in by_col.values():
        for k, (_, i) in enumerate(v):
            rank_col[i] = k

    # ---- auxiliary prefix/suffix nodes.
    # A block must precede EVERY target block on the ray towards its entry
    # edge, which is O(B^2) edges written out.  The judges' debrief reduces
    # this to "an edge to the next block in that direction", which is only
    # sound when that next block slides the same way along the same line; it
    # is NOT sound in general (see the counterexample in main()).  Instead
    # give every line a chain of dummy nodes: PRE[j] means "all blocks of this
    # line up to index j", SUF[j] means "all from index j on".  One edge into
    # a dummy stands for the whole tail of the ray, so the graph stays O(B).
    nxt = [B]                                        # id allocator

    def build_chain(line, forward):
        """returns ids[j] : node meaning 'all line entries from j to the end'
        (forward=False: 'from the start down to j')"""
        k = len(line)
        ids = [0] * k
        rng = range(k - 1, -1, -1) if forward else range(k)
        prev = None
        for j in rng:
            nid = nxt[0]
            nxt[0] += 1
            ids[j] = nid
            aux_edges.append((nid, line[j][1]))
            if prev is not None:
                aux_edges.append((nid, prev))
            prev = nid
        return ids

    aux_edges = []
    row_suf, row_pre, col_suf, col_pre = {}, {}, {}, {}
    for r, line in by_row.items():
        row_suf[r] = build_chain(line, True)
        row_pre[r] = build_chain(line, False)
    for c, line in by_col.items():
        col_suf[c] = build_chain(line, True)
        col_pre[c] = build_chain(line, False)

    V = nxt[0]
    adj = [[] for _ in range(V)]
    indeg = [0] * V

    def add(u, v):
        adj[u].append(v)
        indeg[v] += 1

    for u, v in aux_edges:
        add(u, v)

    move = [None] * B
    for u in range(B):
        if u == 0:
            continue
        r, c = blocks[u]
        pr, pc = blocks[par[u]]
        if pr == r and pc == c - 1:                  # parent left -> from right
            move[u] = ('<', r)
            j = rank_row[u] + 1
            if j < len(by_row[r]):
                add(u, row_suf[r][j])
        elif pr == r and pc == c + 1:                # parent right -> from left
            move[u] = ('>', r)
            j = rank_row[u] - 1
            if j >= 0:
                add(u, row_pre[r][j])
        elif pc == c and pr == r - 1:                # parent above -> from bottom
            move[u] = ('^', c)
            j = rank_col[u] + 1
            if j < len(by_col[c]):
                add(u, col_suf[c][j])
        else:                                        # parent below -> from top
            move[u] = ('v', c)
            j = rank_col[u] - 1
            if j >= 0:
                add(u, col_pre[c][j])
        add(par[u], u)

    dq = deque(i for i in range(V) if indeg[i] == 0)
    topo = []
    cnt = 0
    while dq:
        u = dq.popleft()
        cnt += 1
        if u < B:
            topo.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                dq.append(v)
    if cnt != V:
        return None                                  # cycle -> impossible
    assert topo[0] == 0 and len(topo) == B
    return [move[u] for u in topo[1:]]


# ---------------------------------------------------------------- simulate
def simulate(N, M, blocks, moves):
    """replay; return the resulting set of cells, or None if a move is illegal"""
    cur = {blocks[0]}
    for ch, k in moves:
        if ch in '<>':
            if not (1 <= k <= N):
                return None
            cells = range(M, 0, -1) if ch == '<' else range(1, M + 1)
            landed = None
            for c in cells:
                if (k, c) in cur:
                    break
                landed = (k, c)
            else:
                return None                          # slid right through
            if landed is None:
                return None                          # no room: illegal
            cur.add(landed)
        else:
            if not (1 <= k <= M):
                return None
            cells = range(N, 0, -1) if ch == '^' else range(1, N + 1)
            landed = None
            for r in cells:
                if (r, k) in cur:
                    break
                landed = (r, k)
            else:
                return None
            if landed is None:
                return None
            cur.add(landed)
    return cur


# ------------------------------------------------------------------ brute
def brute(N, M, blocks):
    """True iff the target is reachable.  Exponential; tiny inputs only."""
    B = len(blocks)
    bit = {p: 1 << i for i, p in enumerate(blocks)}
    full = (1 << B) - 1
    start = bit[blocks[0]]
    seen = {start}
    dq = deque([start])
    while dq:
        st = dq.popleft()
        if st == full:
            return True
        cur = set(p for p, b in bit.items() if st & b)
        for ch in '<>^v':
            rng = range(1, N + 1) if ch in '<>' else range(1, M + 1)
            for k in rng:
                if ch in '<>':
                    cells = [(k, c) for c in
                             (range(M, 0, -1) if ch == '<' else range(1, M + 1))]
                else:
                    cells = [(r, k) for r in
                             (range(N, 0, -1) if ch == '^' else range(1, N + 1))]
                landed = None
                hit = False
                for cell in cells:
                    if cell in cur:
                        hit = True
                        break
                    landed = cell
                if not hit or landed is None:
                    continue
                b = bit.get(landed)
                if b is None or st & b:
                    continue                         # off-target / no-op
                ns = st | b
                if ns not in seen:
                    seen.add(ns)
                    dq.append(ns)
    return False


# ------------------------------------------------------- random tree boards
def random_tree_board(N, M, B, rng):
    """a uniformly-ish random tree-shaped block set of size <= B; the list is
    shuffled so the pre-placed block (index 0) is an arbitrary one."""
    start = (rng.randint(1, N), rng.randint(1, M))
    cells = [start]
    have = {start}
    while len(cells) < B:
        cand = []
        for (r, c) in have:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if not (1 <= nr <= N and 1 <= nc <= M) or (nr, nc) in have:
                    continue
                touch = sum(((nr + a, nc + b) in have)
                            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if touch == 1:
                    cand.append((nr, nc))
        if not cand:
            break                                    # cannot stay a tree
        p = cand[rng.randrange(len(cand))]
        have.add(p)
        cells.append(p)
    rng.shuffle(cells)
    return cells


# ------------------------------------------------------------------ driver
SAMPLES = [
    (3, 4, [(1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4)], True),
    (3, 4, [(3, 1), (2, 1), (1, 1), (1, 2), (1, 3), (1, 4),
            (2, 4), (3, 4), (3, 3)], False),
]


def main():
    for N, M, blocks, want in SAMPLES:
        got = solve(N, M, blocks)
        assert (got is not None) == want, (blocks, got, want)
        if want:
            res = simulate(N, M, blocks, got)
            assert res == set(blocks), (got, res)
            assert len(got) == len(blocks) - 1
            print("sample: possible, moves =",
                  " ".join("%s %d" % m for m in got))
        else:
            print("sample: impossible")
        assert brute(N, M, blocks) == want

    # regression: the board on which the debrief's literal edge reduction
    # ("edge to the next block in that direction") produces a wrong order.
    # (6,2) enters from the top of column 2 and so must precede BOTH (4,2)
    # and (2,2); the nearest-only edge reaches (4,2), whose own move is
    # horizontal and therefore never forces (2,2) later, and the resulting
    # order drops a block at (1,2).
    N, M = 7, 4
    cells = [(2, 3), (5, 4), (2, 2), (4, 3), (6, 4), (6, 2), (2, 4), (7, 3),
             (7, 4), (7, 2), (1, 3), (5, 3), (4, 2), (4, 1), (3, 3)]
    got = solve(N, M, cells)
    assert got is not None and simulate(N, M, cells, got) == set(cells), got
    assert brute(N, M, cells) is True
    print("counterexample to the debrief's edge reduction: handled")

    rng = random.Random(20260913)
    npos = nimp = 0
    for it in range(6000):
        N = rng.randint(1, 5)
        M = rng.randint(1, 5)
        B = rng.randint(1, min(9, N * M))
        cells = random_tree_board(N, M, B, rng)
        got = solve(N, M, cells)
        want = brute(N, M, cells)
        if (got is not None) != want:
            print("MISMATCH", N, M, cells, "solve:", got, "brute:", want)
            sys.exit(1)
        if got is not None:
            res = simulate(N, M, cells, got)
            if res != set(cells) or len(got) != len(cells) - 1:
                print("BAD MOVES", N, M, cells, got, res)
                sys.exit(1)
            npos += 1
        else:
            nimp += 1
    print("random small boards: %d possible + %d impossible, all agree with "
          "the 2^B BFS; every produced move list replays to the target"
          % (npos, nimp))

    # dense MAXIMAL trees (grow until the tree cannot be extended): these are
    # the spiral-ish boards where "impossible" actually happens, which random
    # sparse trees almost never produce.
    rng = random.Random(99)
    npos = nimp = 0
    for it in range(400):
        N = rng.randint(3, 5)
        M = rng.randint(3, 5)
        cells = random_tree_board(N, M, N * M, rng)
        if len(cells) > 12:
            continue
        got = solve(N, M, cells)
        want = brute(N, M, cells)
        if (got is not None) != want:
            print("MISMATCH(dense)", N, M, cells, got, want)
            sys.exit(1)
        if got is not None:
            assert simulate(N, M, cells, got) == set(cells), (N, M, cells, got)
            npos += 1
        else:
            nimp += 1
    print("dense maximal trees: %d possible + %d impossible, all agree"
          % (npos, nimp))

    # bigger boards, no brute force: only self-consistency of the move list
    rng = random.Random(7)
    for it in range(300):
        N = rng.randint(3, 9)
        M = rng.randint(3, 9)
        B = rng.randint(2, min(28, N * M))
        cells = random_tree_board(N, M, B, rng)
        got = solve(N, M, cells)
        if got is not None:
            assert simulate(N, M, cells, got) == set(cells), (N, M, cells, got)
    print("medium boards: every 'possible' answer replays exactly")

    # scale
    import time
    B = 400000
    cells = [(1, c) for c in range(1, B + 1)]        # a long horizontal line
    t0 = time.time()
    mv = solve(1, B, cells)
    print("B=400000 line ->", "possible" if mv else "impossible",
          "%.2fs" % (time.time() - t0))
    # comb: spine plus teeth, deep tree
    cells = []
    for c in range(1, 100001):
        cells.append((1, c))
    for c in range(1, 100001, 2):
        cells.append((2, c))
    t0 = time.time()
    mv = solve(3, 100001, cells)
    print("B=%d comb ->" % len(cells), "possible" if mv else "impossible",
          "%.2fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
