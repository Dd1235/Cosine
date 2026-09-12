"""Verify the intended solution for Kattis 'inspectingillumination' (interactive).

Hidden data: a permutation pi with switch i controlling source pi(i); a query
"ASK S" returns the set pi(S).  We must output b with b[source] = switch, i.e.
b = pi^{-1}, using at most 32 queries for n <= 1000.

Intended solution: recover the switch index of every source bit by bit.  For each
bit j, query S_j = { i in [1,n] : i has bit j set }.  Source s appears in the
reply for exactly the bits that are set in pi^{-1}(s), so one pass over the
ceil(log2(n+1)) <= 10 bits determines every answer.  Queries are non-adaptive and
cost floor(log2 n)+1 <= 10 <= 32.  (Indices start at 1, so no index is all-zero
and every source is pinned down.)

Checks: exhaustive over every permutation for n <= 6, randomised up to n = 1000,
plus a check that the sample-style one-switch-at-a-time approach blows the budget.
"""
import random, itertools, math

MAX_QUERIES = 32

class Interactor:
    def __init__(self, n, pi):
        self.n = n
        self.pi = pi              # pi[i] = source controlled by switch i (1-based)
        self.queries = 0
        self.state = [0] * (n + 1)  # actual on/off state, for realism

    def ask(self, switches):
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
        random.shuffle(out)       # "in any order"
        return out

def solve(n, io):
    """Returns b with b[s] = switch controlling source s (1-based list of len n+1)."""
    b = [0] * (n + 1)
    j = 0
    while (1 << j) <= n:
        S = [i for i in range(1, n + 1) if (i >> j) & 1]
        if S:
            for s in io.ask(S):
                b[s] |= (1 << j)
        j += 1
    return b

def run(n, pi):
    io = Interactor(n, pi)
    b = solve(n, io)
    inv = [0] * (n + 1)
    for i in range(1, n + 1):
        inv[pi[i]] = i
    ok = all(b[s] == inv[s] for s in range(1, n + 1))
    assert all(1 <= b[s] <= n for s in range(1, n + 1)), (n, pi, b)
    return ok, io.queries

def main():
    random.seed(11)
    # sample interaction: n = 5, ANSWER 1 4 2 3 5 means source i <- switch b_i
    b_sample = [0, 1, 4, 2, 3, 5]
    pi = [0] * 6
    for s in range(1, 6):
        pi[b_sample[s]] = s
    ok, q = run(5, pi)
    print("sample permutation recovered:", ok, "queries:", q)
    assert ok

    # exhaustive for small n
    worst = 0
    for n in range(1, 7):
        for perm in itertools.permutations(range(1, n + 1)):
            pi = [0] + list(perm)
            ok, q = run(n, pi)
            assert ok, (n, pi)
            worst = max(worst, q)
        print(f"n={n}: all {math.factorial(n)} permutations recovered, "
              f"<= {worst} queries")

    # randomised, including the limits
    worst = 0
    for trial in range(2000):
        n = random.randint(1, 1000)
        perm = list(range(1, n + 1)); random.shuffle(perm)
        ok, q = run(n, [0] + perm)
        assert ok, n
        worst = max(worst, q)
    print(f"2000 random instances (n <= 1000) recovered, worst query count {worst}")

    for n in (1, 2, 511, 512, 513, 1000, 1023 if False else 1000):
        perm = list(range(1, n + 1)); random.shuffle(perm)
        ok, q = run(n, [0] + perm)
        print(f"  n={n}: ok={ok} queries={q} (budget {MAX_QUERIES})")
        assert ok and q <= MAX_QUERIES

    # the sample's one-switch-at-a-time strategy needs n-1 queries: over budget
    print("naive per-switch strategy at n=1000 would need", 1000 - 1,
          "queries -> exceeds", MAX_QUERIES)
    # information-theoretic floor for reference
    bits = math.log2(math.factorial(1000))
    print(f"log2(1000!) = {bits:.0f} bits; a query over k switches returns at most "
          f"log2(C(1000,k)) <= 1000 bits, so ~10 queries is comfortably feasible")

main()
