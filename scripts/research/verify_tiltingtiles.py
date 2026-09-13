"""Kattis 'tiltingtiles' (ICPC World Finals 2023, h,w <= 500).

Given a start and a target arrangement of colored tiles on an h x w grid,
decide whether some sequence of tilts (L/R/U/D, gravity-style) maps start
to target.

Structure of this file
  1. tilt simulator + BFS over the whole reachable set (ground truth)
  2. structural experiments:
       (a) opposite/equal tilts collapse  ->  words alternate axes
       (b) does the SHAPE (set of occupied cells) become invariant under a
           repeated 4-cycle of directions, and how fast?
       (c) is every reachable configuration reachable along one of the 8
           rotationally periodic sequences?
  3. candidate solver: 8 periodic sequences x 4 phases, burn in until the
     shape is cycle-invariant, decompose the induced permutation into cycles,
     match each cycle's color string against the target by rotation
     (all valid rotations of one cycle = arithmetic progression with
     difference = minimal period), then CRT the per-cycle congruences.
  4. randomized cross-check candidate vs BFS
  5. the three sample inputs
"""
import random, sys
from collections import deque
from math import gcd

DIRS = "LRUD"
OPP = {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}

# ----------------------------------------------------------------- 1. model
def tilt(g, h, w, d):
    """g: tuple of h strings ('.' = empty). Returns the tilted board."""
    if d in 'LR':
        rows = []
        for r in g:
            t = [c for c in r if c != '.']
            pad = '.' * (w - len(t))
            rows.append(''.join(t) + pad if d == 'L' else pad + ''.join(t))
        return tuple(rows)
    cols = []
    for c in range(w):
        col = [g[r][c] for r in range(h) if g[r][c] != '.']
        pad = ['.'] * (h - len(col))
        cols.append(col + pad if d == 'U' else pad + col)
    return tuple(''.join(cols[c][r] for c in range(w)) for r in range(h))

def bfs(start, h, w, cap=400000):
    seen = {start}
    q = deque([start])
    while q:
        g = q.popleft()
        for d in DIRS:
            n = tilt(g, h, w, d)
            if n not in seen:
                seen.add(n)
                q.append(n)
                if len(seen) > cap:
                    raise RuntimeError("reachable set too big")
    return seen

def rand_board(h, w, ncol, fill, rng):
    letters = "abcdefghijklmnopqrstuvwxyz"[:ncol]
    return tuple(''.join(rng.choice(letters) if rng.random() < fill else '.'
                         for _ in range(w)) for _ in range(h))

# ------------------------------------------------ 2. structural experiments
def exp_collapse(trials=400, rng=None):
    """L o R == L  (applying R then L equals just L), and X o X == X."""
    rng = rng or random.Random(1)
    for _ in range(trials):
        h, w = rng.randint(1, 4), rng.randint(1, 4)
        g = rand_board(h, w, 3, 0.5, rng)
        for d in DIRS:
            assert tilt(tilt(g, h, w, d), h, w, d) == tilt(g, h, w, d)
            # tilt opposite then d  ==  tilt d
            assert tilt(tilt(g, h, w, OPP[d]), h, w, d) == tilt(g, h, w, d)
    return "equal/opposite adjacent tilts collapse: OK"

ROTATIONS = ["LURD", "LDRU", "ULDR", "URDL", "RDLU", "RULD", "DRUL", "DLUR"]

def shape(g):
    return tuple(''.join('#' if c != '.' else '.' for c in row) for row in g)

def exp_shape_period(trials=300, rng=None, maxhw=6, rounds=40):
    """How many tilts until the shape becomes invariant under the 4-cycle?"""
    rng = rng or random.Random(2)
    worst = 0
    for _ in range(trials):
        h, w = rng.randint(1, maxhw), rng.randint(1, maxhw)
        g = rand_board(h, w, 3, rng.choice([0.2, 0.4, 0.6, 0.85]), rng)
        for seq in ROTATIONS:
            cur, shapes = g, []
            for t in range(4 * rounds):
                cur = tilt(cur, h, w, seq[t % 4])
                shapes.append(shape(cur))
            # first index i such that shapes[j] == shapes[j+4] for all j >= i
            i = len(shapes) - 4
            while i > 0 and shapes[i - 1] == shapes[i + 3]:
                i -= 1
            worst = max(worst, i)
    return "max tilts before the shape is 4-cycle-invariant (h,w<=%d): %d" % (maxhw, worst)

def exp_only_rotations(trials=120, rng=None, steps=200):
    """Is every BFS-reachable configuration hit by one of the 8 periodic seqs?"""
    rng = rng or random.Random(3)
    bad = 0
    for _ in range(trials):
        h, w = rng.randint(1, 3), rng.randint(1, 3)
        g = rand_board(h, w, 2, 0.55, rng)
        R = bfs(g, h, w)
        got = {g}
        for seq in ROTATIONS:
            cur = g
            for t in range(steps):
                cur = tilt(cur, h, w, seq[t % 4])
                got.add(cur)
        if got != R:
            bad += 1
            if bad == 1:
                print("   counterexample h=%d w=%d %r  missing=%r"
                      % (h, w, g, sorted(R - got)[:3]))
    return "boards where the 8 periodic sequences miss something: %d/%d" % (bad, trials)

# ----------------------------------------------------------- 3. candidate
def to_cells(g, h, w):
    return {(r, c): g[r][c] for r in range(h) for c in range(w) if g[r][c] != '.'}

def tilt_cells(cells, h, w, d):
    """Tilt a dict pos->payload; payload order along each row/column is kept."""
    out = {}
    if d in 'LR':
        for r in range(h):
            row = [cells[(r, c)] for c in range(w) if (r, c) in cells]
            base = 0 if d == 'L' else w - len(row)
            for i, v in enumerate(row):
                out[(r, base + i)] = v
    else:
        for c in range(w):
            col = [cells[(r, c)] for r in range(h) if (r, c) in cells]
            base = 0 if d == 'U' else h - len(col)
            for i, v in enumerate(col):
                out[(base + i, c)] = v
    return out

def rotations_matching(a, b):
    """All k with b[(i+k)%L] == a[i] for all i, as (k0, step) or None.
    Equivalently b = a rotated right by k.  Found by locating b inside a+a;
    the occurrence set is an arithmetic progression with difference equal to
    the minimal period of the string (a standard periodicity fact, asserted
    against brute force in test_rotations)."""
    L = len(a)
    if L == 0:
        return (0, 1)
    ks = [k for k in range(L) if all(b[(i + k) % L] == a[i] for i in range(L))]
    if not ks:
        return None
    step = ks[1] - ks[0] if len(ks) > 1 else L
    return (ks[0], step)

def crt(cons):
    """cons: list of (rem, mod).  True iff simultaneously satisfiable."""
    R, M = 0, 1
    for r, m in cons:
        g = gcd(M, m)
        if (r - R) % g:
            return False
        mm = m // g
        t = 0 if mm == 1 else ((r - R) // g * pow(M // g, -1, mm)) % mm
        R += M * t
        M = M // g * m
        R %= M
    return True

def solve(start, target, h, w, burn=None):
    if start == target:
        return True
    S, T = to_cells(start, h, w), to_cells(target, h, w)
    if sorted(S.values()) != sorted(T.values()):
        return False
    if burn is None:
        burn = 4 * (h + w + 4)          # generous; the real bound is small
    for seq in ROTATIONS:
        cur = S
        pre = []
        for t in range(burn + 8):
            cur = tilt_cells(cur, h, w, seq[t % 4])
            if cur == T:
                return True
            pre.append(cur)
        # now the shape is cycle-invariant; consider the 4 phases
        for r in range(4):
            A = pre[burn + r - 1] if burn + r >= 1 else S
            lab = {p: p for p in A}          # track where each tile goes
            for j in range(4):
                lab = tilt_cells(lab, h, w, seq[(burn + r + j) % 4])
            if set(lab) != set(A) or set(A) != set(T):
                continue                     # shape not invariant / mismatched
            nxt = {old: new for new, old in lab.items()}
            seen, cons, ok = set(), [], True
            for p in A:
                if p in seen:
                    continue
                cyc, q = [], p
                while q not in seen:
                    seen.add(q); cyc.append(q); q = nxt[q]
                m = rotations_matching(''.join(A[x] for x in cyc),
                                       ''.join(T[x] for x in cyc))
                if m is None:
                    ok = False; break
                cons.append(m)
            if ok and crt(cons):
                return True
    return False

# --------------------------------------------------------- 4. cross-checks
def test_rotations(trials=3000, rng=None):
    """occurrence set of rotations really is an arithmetic progression."""
    rng = rng or random.Random(7)
    for _ in range(trials):
        L = rng.randint(1, 9)
        a = ''.join(rng.choice('ab') for _ in range(L))
        b = ''.join(rng.choice('ab') for _ in range(L)) if rng.random() < .5 \
            else (lambda k: ''.join(a[(i - k) % L] for i in range(L)))(rng.randrange(L))
        ks = [k for k in range(L) if all(b[(i + k) % L] == a[i] for i in range(L))]
        m = rotations_matching(a, b)
        if not ks:
            assert m is None
        else:
            k0, st = m
            assert ks == list(range(k0, L, st)), (a, b, ks, m)
    return "rotation sets are arithmetic progressions: OK (%d)" % trials

def cross_check(trials=400, rng=None, maxh=3, maxw=3, cap=6000):
    rng = rng or random.Random(11)
    checked = mism = 0
    for _ in range(trials):
        h, w = rng.randint(1, maxh), rng.randint(1, maxw)
        ncol = rng.choice([1, 2, 2, 3])
        g = rand_board(h, w, ncol, rng.choice([0.3, 0.5, 0.7, 0.9]), rng)
        try:
            R = bfs(g, h, w, cap)
        except RuntimeError:
            continue
        # candidate targets: everything reachable, plus same-multiset decoys
        cells = [c for row in g for c in row if c != '.']
        cand = set(R)
        for _ in range(25):
            perm = cells[:]; rng.shuffle(perm)
            it = iter(perm)
            cand.add(tuple(''.join(next(it) if ch != '.' else '.' for ch in row)
                           for row in g))
        for t in cand:
            checked += 1
            exp = t in R
            got = solve(g, t, h, w, burn=4 * (h + w + 4))
            if exp != got:
                mism += 1
                if mism <= 3:
                    print("   MISMATCH h=%d w=%d start=%r target=%r bfs=%s cand=%s"
                          % (h, w, g, t, exp, got))
    return "cross-check %dx%d: %d pairs, %d mismatches" % (maxh, maxw, checked, mism)

SAMPLES = [
    ((".r..", "rgyb", ".b..", ".yr."), ("yrbr", "..yr", "...g", "...b"), True),
    (("....x..",), ("..x....",), False),
    (("yr.", "..b", "ry.", "b.."), ("...", "..b", ".ry", "byb"), False),
]

def run_samples():
    out = []
    for s, t, exp in SAMPLES:
        h, w = len(s), len(s[0])
        got = solve(s, t, h, w)
        out.append("sample %s expected=%s got=%s" % (len(out) + 1, exp, got))
        assert got == exp, out[-1]
    return "; ".join(out)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "1"):
        print(exp_collapse())
        print(test_rotations())
    if which in ("all", "2"):
        print(exp_shape_period(trials=120, maxhw=5))
        print(exp_shape_period(trials=40, maxhw=8))
    if which in ("all", "3"):
        print(exp_only_rotations(trials=80))
    if which in ("all", "4"):
        print(run_samples())
    if which in ("all", "5"):
        print(cross_check(trials=250, maxh=3, maxw=3))
    if which == "6":
        print(cross_check(trials=60, maxh=4, maxw=4, cap=200000))

def near_miss_check(trials=200, rng=None, maxh=3, maxw=4, cap=200000):
    """Hardest case for the CRT step: targets that live on a REACHABLE shape
    but with the colors permuted, so only the per-cycle rotation congruences
    can tell reachable from unreachable."""
    rng = rng or random.Random(31)
    checked = mism = 0
    for _ in range(trials):
        h, w = rng.randint(2, maxh), rng.randint(2, maxw)
        g = rand_board(h, w, rng.choice([2, 3, 4]), rng.choice([0.5, 0.7, 0.9]), rng)
        try:
            R = bfs(g, h, w, cap)
        except RuntimeError:
            continue
        Rl = list(R)
        cand = set()
        for _ in range(40):
            base = rng.choice(Rl)
            cells = [c for row in base for c in row if c != '.']
            rng.shuffle(cells)
            it = iter(cells)
            cand.add(tuple(''.join(next(it) if ch != '.' else '.' for ch in row)
                           for row in base))
        for t in cand:
            checked += 1
            exp, got = t in R, solve(g, t, h, w, burn=4 * (h + w + 4))
            if exp != got:
                mism += 1
                if mism <= 3:
                    print("   MISMATCH h=%d w=%d %r -> %r bfs=%s cand=%s"
                          % (h, w, g, t, exp, got))
    return "near-miss check: %d pairs, %d mismatches" % (checked, mism)
