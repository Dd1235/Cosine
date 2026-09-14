"""Verify the published solution for Kattis 'inspectingillumination' (interactive).

Hidden data: a permutation pi with switch i controlling source pi(i); the query
"ASK k a_1..a_k" toggles those switches and returns the *set* pi({a_i}) (in any
order, with no hint of which switch produced which source).  We must output b
with b[source] = switch, i.e. b = pi^{-1}, within 32 queries for n <= 1000.

Two solutions are checked here.

  * `solve_published` -- a faithful transcription of the accepted C++
    (inspectingillumination.cpp).  It builds the segment-tree recursion over the
    switch interval [1,n] and, for each depth d, asks ONE query containing the
    union of every *left* child interval at depth d (the root counts as a left
    child).  Because the left halves at a fixed depth are pairwise disjoint and
    disjoint from all right halves at that depth, the reply for depth d+1 splits
    the source set already known to belong to a node [L,R] into the part coming
    from [L,mid] (present in the reply) and the part coming from [mid+1,R]
    (absent).  Recursing to the leaves pins every source to one switch.  The
    queries are non-adaptive and there is one per depth, so
    ceil(log2 n) + 1 <= 11 <= 32 for n <= 1000.

  * `solve_bits` -- the equivalent textbook phrasing: for each bit j ask the set
    of switches whose index has bit j set; source s is in the reply exactly when
    pi^{-1}(s) has bit j set.  floor(log2 n) + 1 <= 10 queries.

Checks: the statement's sample permutation, exhaustive over every permutation
for n <= 6, randomised up to n = 1000 (plus the powers-of-two boundaries), the
query budget, and agreement between the two solutions.
"""
import itertools
import math
import random
import sys
from collections import defaultdict

sys.setrecursionlimit(100000)

MAX_QUERIES = 32


class Interactor:
    def __init__(self, n, pi):
        self.n = n
        self.pi = pi                 # pi[i] = source controlled by switch i (1-based)
        self.queries = 0
        self.state = [0] * (n + 1)   # actual on/off state, for realism

    def ask(self, switches):
        switches = list(switches)
        assert 1 <= len(switches) <= self.n, "k out of range"
        assert len(set(switches)) == len(switches), "duplicate switch in query"
        assert all(1 <= a <= self.n for a in switches), "switch out of range"
        self.queries += 1
        assert self.queries <= MAX_QUERIES, "query budget exceeded"
        out = []
        for a in switches:
            s = self.pi[a]
            self.state[s] ^= 1
            out.append(s)
        random.shuffle(out)          # "in any order"
        return out


# --------------------------------------------------------------- published
def solve_published(n, io):
    """Transcription of inspectingillumination.cpp.  Returns b[1..n]."""
    ques = defaultdict(list)     # depth -> switches asked at that depth
    node_id = {}                 # (L,R) -> id
    depths = defaultdict(list)   # depth -> intervals

    def ask_query_sets(L, R, deg, question):
        if question:
            ques[deg].extend(range(L, R + 1))
        if L == R:
            return
        mid = (L + R) >> 1
        ask_query_sets(L, mid, deg + 1, True)
        ask_query_sets(mid + 1, R, deg + 1, False)

    def ask_ids(L, R, deg):
        depths[deg].append((L, R))
        node_id[(L, R)] = len(node_id)
        if L == R:
            return
        mid = (L + R) >> 1
        ask_ids(L, mid, deg + 1)
        ask_ids(mid + 1, R, deg + 1)

    ask_query_sets(1, n, 0, True)
    ask_ids(1, n, 0)

    lm = max(depths)
    ans = {}
    for d in range(lm, -1, -1):
        assert ques[d], "the C++ spins forever on an empty query set at depth %d" % d
        ans[d] = io.ask(ques[d])

    res = defaultdict(list)
    res[node_id[(1, n)]] = list(ans[0])
    kq = []

    def get(L, R, deg):
        if L == R:
            vals = res[node_id[(L, R)]]
            assert len(vals) == 1, (L, R, vals)
            kq.append(vals[0])
            return
        mid = (L + R) >> 1
        in_left = set(ans[deg + 1])
        left_id = node_id[(L, mid)]
        right_id = node_id[(mid + 1, R)]
        for x in res[node_id[(L, R)]]:
            if x in in_left:
                res[left_id].append(x)
            else:
                res[right_id].append(x)
        get(L, mid, deg + 1)
        get(mid + 1, R, deg + 1)

    get(1, n, 0)
    assert len(kq) == n
    b = [0] * (n + 1)
    for i in range(n):
        b[kq[i]] = i + 1         # kq[i] is the source driven by switch i+1
    return b


# -------------------------------------------------------------------- bits
def solve_bits(n, io):
    b = [0] * (n + 1)
    j = 0
    while (1 << j) <= n:
        S = [i for i in range(1, n + 1) if (i >> j) & 1]
        if S:
            for s in io.ask(S):
                b[s] |= (1 << j)
        j += 1
    return b


def run(n, pi, solver):
    io = Interactor(n, pi)
    b = solver(n, io)
    inv = [0] * (n + 1)
    for i in range(1, n + 1):
        inv[pi[i]] = i
    assert all(1 <= b[s] <= n for s in range(1, n + 1)), (n, pi, b)
    return all(b[s] == inv[s] for s in range(1, n + 1)), io.queries


def main():
    random.seed(11)

    # sample interaction: n = 5, ANSWER 1 4 2 3 5 means source i <- switch b_i
    b_sample = [0, 1, 4, 2, 3, 5]
    pi = [0] * 6
    for s in range(1, 6):
        pi[b_sample[s]] = s
    for name, solver in (("published", solve_published), ("bits", solve_bits)):
        ok, q = run(5, pi, solver)
        print("sample permutation recovered by %-9s: %s (%d queries)" % (name, ok, q))
        assert ok

    # exhaustive for small n
    for name, solver in (("published", solve_published), ("bits", solve_bits)):
        worst = 0
        for n in range(1, 7):
            for perm in itertools.permutations(range(1, n + 1)):
                ok, q = run(n, [0] + list(perm), solver)
                assert ok, (name, n, perm)
                worst = max(worst, q)
        print("%-9s: every permutation for n <= 6 recovered, <= %d queries"
              % (name, worst))

    # randomised, including the limit and the powers-of-two boundaries
    for name, solver in (("published", solve_published), ("bits", solve_bits)):
        worst = 0
        for _ in range(400):
            n = random.randint(1, 1000)
            perm = list(range(1, n + 1))
            random.shuffle(perm)
            ok, q = run(n, [0] + perm, solver)
            assert ok, (name, n)
            worst = max(worst, q)
        for n in (1, 2, 3, 511, 512, 513, 999, 1000):
            perm = list(range(1, n + 1))
            random.shuffle(perm)
            ok, q = run(n, [0] + perm, solver)
            assert ok and q <= MAX_QUERIES, (name, n, q)
            worst = max(worst, q)
        print("%-9s: 400 random n<=1000 plus boundary sizes recovered; worst "
              "query count %d (budget %d)" % (name, worst, MAX_QUERIES))

    # the two solvers must agree exactly
    for _ in range(200):
        n = random.randint(1, 200)
        perm = list(range(1, n + 1))
        random.shuffle(perm)
        b1 = solve_published(n, Interactor(n, [0] + perm))
        b2 = solve_bits(n, Interactor(n, [0] + perm))
        assert b1 == b2, (n, perm)
    print("published and bitwise solvers agree on 200 random instances")

    # the sample's one-switch-at-a-time strategy would need n-1 queries
    print("naive per-switch strategy at n=1000 would need", 1000 - 1,
          "queries -> exceeds", MAX_QUERIES)
    bits = math.log2(math.factorial(1000))
    print("log2(1000!) = %.0f bits; each query returns a subset of [1,n], so "
          "~10-11 queries is comfortably enough" % bits)

    print("\nAll checks passed.")


main()
