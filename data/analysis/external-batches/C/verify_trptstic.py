"""codechef-trptstic / TripTastic -- verification.

Problem: N x M grid of room capacities A. Place 1 mentor + K students.
Chebyshev distance max(|di|,|dj|).  Minimise the distance from the mentor's
room to the farthest occupied student room.  -1 if total capacity < K+1.

Claimed solution
----------------
Answer = min d such that there exists a cell (r,c) with A[r][c] >= 1 (the
mentor must physically fit in his own room) and the capacity sum of the
(2d+1)x(2d+1) Chebyshev ball centred at (r,c), clipped to the grid, is >= K+1.
People are interchangeable and unconstrained beyond per-room capacity, so
"an arrangement exists" is exactly "the ball's total capacity >= K+1".
The predicate is monotone in d (the ball only grows), so binary search d in
[0, max(N,M)] and test each candidate with 2D prefix sums: O(NM log max(N,M)).

Three implementations are cross-checked:
  solve_fast   -- binary search + 2D prefix sums (the intended one)
  solve_brute  -- every (centre, d) pair, square summed by direct loops
  feasible_exhaustive -- literal enumeration of every student distribution
                         over the rooms of a ball, for tiny cases; confirms
                         the "sum of capacities" reduction itself.
"""
import random, itertools, sys

# ---------------------------------------------------------------- fast
def solve_fast(N, M, K, A):
    total = sum(map(sum, A))
    if total < K + 1:
        return -1
    # 2D prefix sums, P[i][j] = sum of A[0..i-1][0..j-1]
    P = [[0] * (M + 1) for _ in range(N + 1)]
    for i in range(N):
        row = A[i]; Pi = P[i]; Pi1 = P[i + 1]
        run = 0
        for j in range(M):
            run += row[j]
            Pi1[j + 1] = Pi[j + 1] + run
    def rect(r1, c1, r2, c2):           # inclusive, already clipped
        return P[r2 + 1][c2 + 1] - P[r1][c2 + 1] - P[r2 + 1][c1] + P[r1][c1]
    def ok(d):
        for i in range(N):
            for j in range(M):
                if A[i][j] >= 1:        # mentor needs a slot in his own room
                    r1 = max(0, i - d); r2 = min(N - 1, i + d)
                    c1 = max(0, j - d); c2 = min(M - 1, j + d)
                    if rect(r1, c1, r2, c2) >= K + 1:
                        return True
        return False
    lo, hi = 0, max(N, M)               # hi always feasible: covers whole grid
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid): hi = mid
        else:       lo = mid + 1
    return lo

# --------------------------------------------------------------- brute
def solve_brute(N, M, K, A):
    if sum(map(sum, A)) < K + 1:
        return -1
    for d in range(max(N, M) + 1):
        for i in range(N):
            for j in range(M):
                if A[i][j] < 1:
                    continue
                s = 0
                for r in range(max(0, i - d), min(N - 1, i + d) + 1):
                    for c in range(max(0, j - d), min(M - 1, j + d) + 1):
                        s += A[r][c]
                if s >= K + 1:
                    return d
    raise AssertionError("no d found despite capacity check")

# ------------------------------------------- literal-semantics check
def feasible_exhaustive(N, M, K, A, i, j, d):
    """True iff K students + the mentor can literally be placed: mentor in
    (i,j), every student in a room within Chebyshev distance d, no room over
    capacity.  Enumerates distributions; tiny inputs only."""
    if A[i][j] < 1:
        return False
    cells = [(r, c) for r in range(max(0, i - d), min(N - 1, i + d) + 1)
                    for c in range(max(0, j - d), min(M - 1, j + d) + 1)]
    caps = []
    for (r, c) in cells:
        cap = A[r][c] - (1 if (r, c) == (i, j) else 0)   # mentor consumes one
        caps.append(cap)
    for combo in itertools.product(*[range(c + 1) for c in caps]):
        if sum(combo) == K:
            return True
    return K == 0

def solve_semantic(N, M, K, A):
    """Answer computed straight from the literal placement semantics."""
    for d in range(max(N, M) + 1):
        for i in range(N):
            for j in range(M):
                if feasible_exhaustive(N, M, K, A, i, j, d):
                    return d
    return -1

# --------------------------------------------------------------- tests
SAMPLES = [
    ((1, 7, 5, [[2, 1, 0, 1, 3, 0, 1]]), 3),
    ((2, 4, 3, [[1, 0, 4, 0], [0, 2, 0, 3]]), 0),
    ((2, 2, 7, [[1, 0], [4, 1]]), -1),
    ((3, 2, 3, [[0, 2], [1, 0], [1, 0]]), 1),
]

def main():
    for (N, M, K, A), want in SAMPLES:
        got_f, got_b = solve_fast(N, M, K, A), solve_brute(N, M, K, A)
        assert got_f == want, ("sample fast", N, M, K, A, got_f, want)
        assert got_b == want, ("sample brute", N, M, K, A, got_b, want)
    print("4/4 samples pass (fast and brute)")

    random.seed(20260912)
    # (a) fast vs brute on many random grids
    for t in range(4000):
        N = random.randint(1, 5); M = random.randint(1, 5)
        cap = random.choice([1, 2, 3, 6])
        A = [[random.randint(0, cap) for _ in range(M)] for _ in range(N)]
        K = random.randint(1, max(1, sum(map(sum, A)) + 2))
        f, b = solve_fast(N, M, K, A), solve_brute(N, M, K, A)
        assert f == b, ("fast vs brute", N, M, K, A, f, b)
    print("4000 random grids: fast == brute")

    # (b) the capacity-sum reduction vs literal placement enumeration
    for t in range(400):
        N = random.randint(1, 3); M = random.randint(1, 3)
        A = [[random.randint(0, 2) for _ in range(M)] for _ in range(N)]
        K = random.randint(1, 5)
        f, s = solve_fast(N, M, K, A), solve_semantic(N, M, K, A)
        assert f == s, ("fast vs semantic", N, M, K, A, f, s)
    print("400 tiny grids: fast == literal placement enumeration")

    # (c) thin grids, the shape the constraints actually allow (N*M <= 1e6)
    for t in range(600):
        if random.random() < .5: N, M = 1, random.randint(1, 12)
        else:                    N, M = random.randint(1, 12), 1
        A = [[random.randint(0, 3) for _ in range(M)] for _ in range(N)]
        K = random.randint(1, 12)
        f, b = solve_fast(N, M, K, A), solve_brute(N, M, K, A)
        assert f == b, ("thin", N, M, K, A, f, b)
    print("600 thin 1xM / Nx1 grids: fast == brute")

    # (d) monotonicity of the predicate (what licenses the binary search)
    for t in range(300):
        N = random.randint(1, 4); M = random.randint(1, 4)
        A = [[random.randint(0, 3) for _ in range(M)] for _ in range(N)]
        K = random.randint(1, 10)
        def ok(d):
            for i in range(N):
                for j in range(M):
                    if A[i][j] >= 1:
                        s = sum(A[r][c]
                                for r in range(max(0, i - d), min(N - 1, i + d) + 1)
                                for c in range(max(0, j - d), min(M - 1, j + d) + 1))
                        if s >= K + 1: return True
            return False
        seq = [ok(d) for d in range(max(N, M) + 1)]
        assert seq == sorted(seq), ("not monotone", N, M, K, A, seq)
    print("300 grids: feasibility predicate monotone in d")

    # (e) the zero-capacity-centre trap: a cell with A=0 may not host the mentor
    A = [[2, 0, 0], [0, 0, 0], [0, 0, 3]]
    # capacity 5 == K+1, split across two opposite corners: either legal centre
    # needs its ball to reach the other corner, so d = 2
    assert solve_fast(3, 3, 4, A) == 2, solve_fast(3, 3, 4, A)
    assert solve_brute(3, 3, 4, A) == 2
    A2 = [[3, 0, 0, 0, 3]]
    # centre (0,2) has A=0; best legal centres are (0,0)/(0,4), each needing d=4
    assert solve_fast(1, 5, 5, A2) == 4, solve_fast(1, 5, 5, A2)
    assert solve_brute(1, 5, 5, A2) == 4
    print("zero-capacity-centre cases behave as specified")

    # (f) scale: worst allowed total size, T=1
    import time
    N, M = 1000, 1000
    A = [[random.randint(0, 100000) for _ in range(M)] for _ in range(N)]
    t0 = time.time(); r = solve_fast(N, M, 10**9, A); t1 = time.time()
    print(f"1000x1000, K=1e9 -> {r}  ({t1-t0:.2f}s in pure Python; C++ is ~100x faster)")
    N, M = 1, 10**6
    A = [[random.randint(0, 3) for _ in range(M)]]
    t0 = time.time(); r = solve_fast(N, M, 10**9, A); t1 = time.time()
    print(f"1x1000000, K=1e9 -> {r}  ({t1-t0:.2f}s, 20 binary-search rounds)")
    print("ALL CHECKS PASS")

main()
