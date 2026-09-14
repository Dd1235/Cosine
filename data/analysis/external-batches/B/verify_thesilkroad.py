"""
kattis-thesilkroad  --  ICPC WF 2024 "The Silk Road ... with Robots!"

Model derived from the statement (confirmed by sample day 3):
a robot starting at p that walks and ends up having visited exactly the
interval [l,r] (l <= p <= r) pays  (r-l) + min(p-l, r-p)  meters and
collects every store inside [l,r].  Each store pays out at most once.

Claim: an optimal plan uses pairwise-DISJOINT intervals, one robot each.
That is what the DP below assumes; the brute force does NOT assume it
(it enumerates an arbitrary interval per robot, overlaps allowed), so the
cross-check validates the claim too.

DP (the intended solution): sweep the compressed positions left to right.
The label of each gap between consecutive positions is one of
    out              not covered              multiplier 0
    A  left part, right part will cost 1x     multiplier 2
    B  left part, right part will cost 2x     multiplier 1
    C  right part, left part cost 2x          multiplier 1
    D  right part, left part cost 1x          multiplier 2
A covered interval is a maximal run  A*C*  or  B*D*  whose A->C / B->D
(or out->C/D, or B->out) boundary sits exactly on a robot.
5 states, transitions only at points => the whole day is a max-plus
product of 5x5 matrices, so a segment tree over the (offline) compressed
positions answers every day in O(log n * 5^3): O(n log n) overall.
Here we just recompute the DP each day (O(n^2)) since n is tiny.
"""
import random, itertools, json, hashlib, sys

NEG = float('-inf')
OUT, A, B, C, D = 0, 1, 2, 3, 4
MULT = [0, 2, 1, 1, 2]

# (u, v, needs_robot).  Covered(u,v) is True unless u==v==OUT.
TRANS = [
    (OUT, OUT, False),
    (OUT, A, False), (OUT, B, False),
    (OUT, C, True),  (OUT, D, True),
    (A, A, False),   (A, C, True),
    (B, B, False),   (B, D, True),  (B, OUT, True),
    (C, C, False),   (C, OUT, False),
    (D, D, False),   (D, OUT, False),
]

def solve_dp(points):
    """points: list of (pos, kind, c) with kind 1=robot 2=store, distinct pos."""
    pts = sorted(points)
    dp = [NEG] * 5
    dp[OUT] = 0
    prev = None
    for (pos, kind, c) in pts:
        if prev is not None:
            d = pos - prev
            for s in range(5):
                if dp[s] != NEG:
                    dp[s] -= MULT[s] * d
        nd = [NEG] * 5
        is_robot = (kind == 1)
        for (u, v, need) in TRANS:
            if need and not is_robot:
                continue
            if dp[u] == NEG:
                continue
            gain = 0
            if kind == 2 and not (u == OUT and v == OUT):
                gain = c
            val = dp[u] + gain
            if val > nd[v]:
                nd[v] = val
        dp = nd
        prev = pos
    return max(dp[OUT], dp[C], dp[D])


def solve_brute(points):
    """Exact: each robot independently picks any [l,r] containing it
    (endpoints from the position set), overlaps allowed, stores paid once."""
    robots = [p for (p, k, c) in points if k == 1]
    stores = [(p, c) for (p, k, c) in points if k == 2]
    if not robots or not stores:
        return 0
    coords = sorted(p for (p, k, c) in points)
    choices = []
    for r in robots:
        opts = []
        for l in coords:
            if l > r:
                continue
            for rr in coords:
                if rr < r:
                    continue
                cost = (rr - l) + min(r - l, rr - r)
                mask = 0
                for i, (sp, sc) in enumerate(stores):
                    if l <= sp <= rr:
                        mask |= 1 << i
                opts.append((cost, mask))
        # prune dominated options
        best = {}
        for cost, mask in opts:
            if mask not in best or cost < best[mask]:
                best[mask] = cost
        choices.append([(c_, m) for m, c_ in best.items()])
    ans = 0
    for combo in itertools.product(*choices):
        cost = sum(c_ for c_, m in combo)
        mask = 0
        for c_, m in combo:
            mask |= m
        gain = sum(sc for i, (sp, sc) in enumerate(stores) if mask >> i & 1)
        ans = max(ans, gain - cost)
    return ans


def run(events, solver):
    out = []
    cur = []
    for e in events:
        cur.append(e)
        out.append(solver(list(cur)))
    return out


def sample():
    events = [(20, 1, 0), (15, 2, 15), (40, 2, 50), (50, 1, 0), (80, 2, 20), (70, 2, 30)]
    exp = [0, 10, 35, 50, 50, 60]
    got = run(events, solve_dp)
    print("sample dp   :", got)
    print("sample want :", exp)
    assert got == exp, "SAMPLE MISMATCH"
    gotb = run(events, solve_brute)
    print("sample brute:", gotb)
    assert gotb == exp, "SAMPLE BRUTE MISMATCH"
    print("sample OK")


def stress(iters=3000, seed=1):
    rnd = random.Random(seed)
    for it in range(iters):
        n = rnd.randint(1, 7)
        maxpos = rnd.choice([12, 25, 60])
        poss = rnd.sample(range(0, maxpos), n)
        events = []
        nrob = 0
        for p in poss:
            if rnd.random() < 0.45 and nrob < 4:
                events.append((p, 1, 0))
                nrob += 1
            else:
                events.append((p, 2, rnd.randint(0, 20)))
        a = run(events, solve_dp)
        b = run(events, solve_brute)
        if a != b:
            print("MISMATCH on", events)
            print(" dp   ", a)
            print(" brute", b)
            return False
    print("stress OK (%d random cases)" % iters)
    return True


if __name__ == "__main__":
    sample()
    ok = stress()
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------------------
# The intended ONLINE solution: offline-compress all n positions, keep a
# segment tree of 5x5 max-plus matrices (leaf i = "cross the gap to p_i,
# then apply point p_i"); adding a robot/store is one point update, the day's
# answer is read off the root.  O(n log n * 5^3).
# Validated below against the straight-line DP.
# ---------------------------------------------------------------------------
def _leaf_matrix(gap, kind, c):
    M = [[NEG] * 5 for _ in range(5)]
    is_robot = (kind == 1)
    for (u, v, need) in TRANS:
        if need and not is_robot:
            continue
        gain = 0
        if kind == 2 and not (u == OUT and v == OUT):
            gain = c
        val = -MULT[u] * gap + gain           # gap is crossed in state u
        if val > M[u][v]:
            M[u][v] = val
    return M

IDENT = [[0 if i == j else NEG for j in range(5)] for i in range(5)]

def _mul(X, Y):
    R = [[NEG] * 5 for _ in range(5)]
    for i in range(5):
        Xi = X[i]
        Ri = R[i]
        for k in range(5):
            a = Xi[k]
            if a == NEG:
                continue
            Yk = Y[k]
            for j in range(5):
                b = Yk[j]
                if b != NEG and a + b > Ri[j]:
                    Ri[j] = a + b
    return R

def solve_segtree(events):
    """events in arrival order: (pos, kind, c).  Returns answer per day."""
    coords = sorted(p for (p, k, c) in events)
    idx = {p: i for i, p in enumerate(coords)}
    m = len(coords)
    size = 1
    while size < m:
        size *= 2
    tree = [IDENT] * (2 * size)
    active = [False] * m

    def rebuild_leaf(i):
        # gap from the previous ACTIVE position to coords[i]
        j = i - 1
        while j >= 0 and not active[j]:
            j -= 1
        gap = coords[i] - coords[j] if j >= 0 else 0
        kind, c = info[i]
        tree[size + i] = _leaf_matrix(gap, kind, c)
        x = (size + i) >> 1
        while x:
            tree[x] = _mul(tree[2 * x], tree[2 * x + 1])
            x >>= 1

    def clear_leaf(i):
        tree[size + i] = IDENT
        x = (size + i) >> 1
        while x:
            tree[x] = _mul(tree[2 * x], tree[2 * x + 1])
            x >>= 1

    info = [None] * m
    out = []
    for (p, kind, c) in events:
        i = idx[p]
        info[i] = (kind, c)
        active[i] = True
        rebuild_leaf(i)
        # the next active position's gap shrank: refresh it
        j = i + 1
        while j < m and not active[j]:
            j += 1
        if j < m:
            rebuild_leaf(j)
        root = tree[1]
        out.append(max(root[OUT][OUT], root[OUT][C], root[OUT][D]))
    return out


def stress_segtree(iters=300, seed=7, nmax=40):
    rnd = random.Random(seed)
    for it in range(iters):
        n = rnd.randint(1, nmax)
        poss = rnd.sample(range(0, 400), n)
        rnd.shuffle(poss)
        events = []
        for p in poss:
            if rnd.random() < 0.4:
                events.append((p, 1, 0))
            else:
                events.append((p, 2, rnd.randint(0, 60)))
        a = run(events, solve_dp)
        b = solve_segtree(events)
        if a != b:
            print("SEGTREE MISMATCH", events)
            print(a)
            print(b)
            return False
    print("segtree OK (%d cases, n<=%d)" % (iters, nmax))
    return True
