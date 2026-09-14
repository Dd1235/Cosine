"""
Kattis "Bingo for the Win!" (ICPC WF 2024) -- brute-force verification.

Model: the multiset union of all n sheets (n*k numbers) is read in a uniformly
random order.  On each call of value v, the fastest (lowest-index) player that
still holds an uncrossed copy of v crosses one copy off.  A player's finish time
is the position at which they cross off their last number.  We want, for each
player, P(their finish time is the maximum).

Claimed closed form:
  For value v let m_v be its total multiplicity over all sheets and let
  last(v) be the largest-index player holding v.  Then
      P(player i finishes last) = (sum_{v : last(v)=i} m_v) / (n*k).
Reason: the r-th occurrence of v is claimed by the player p with
  (total multiplicity of v among players <= p) >= r for the first time, so the
  final (m_v-th) occurrence of v always goes to last(v).  Every call is claimed
  by exactly one player, so the player who claims the very last call of the
  whole sequence is the one finishing at time n*k, i.e. finishes last, and that
  call is the final occurrence of whatever value it is.

Brute force enumerates every distinct ordering of the multiset (weighted by its
number of labelled arrangements) and simulates.
"""
import itertools, random
from collections import Counter
from fractions import Fraction


def simulate_last(sheets, order):
    """Return index of the player who finishes last for this call order."""
    n = len(sheets)
    remaining = [Counter(s) for s in sheets]
    left = [len(s) for s in sheets]          # numbers still to cross off
    finish = [None] * n
    for t, v in enumerate(order):
        for p in range(n):                    # fastest player with a copy left
            if remaining[p][v] > 0:
                remaining[p][v] -= 1
                left[p] -= 1
                if left[p] == 0:
                    finish[p] = t
                break
        else:
            raise AssertionError("call with no taker -- model is wrong")
    assert all(f is not None for f in finish)
    assert len(set(finish)) == n, "finish times must be distinct"
    return max(range(n), key=lambda p: finish[p])


def brute(sheets):
    """Exact probabilities by enumerating all distinct multiset orderings."""
    pool = []
    for s in sheets:
        pool.extend(s)
    total = 0
    win = [0] * len(sheets)
    # distinct permutations of the multiset, each weighted by its multiplicity
    # in the labelled permutation space (which is identical for all of them).
    seen = set()
    for perm in itertools.permutations(pool):
        if perm in seen:
            continue
        seen.add(perm)
        total += 1
        win[simulate_last(sheets, perm)] += 1
    return [Fraction(w, total) for w in win]


def formula(sheets):
    n = len(sheets)
    mult = Counter()
    last_holder = {}
    for i, s in enumerate(sheets):
        for v in s:
            mult[v] += 1
        for v in set(s):
            last_holder[v] = i          # players processed in speed order
    nk = sum(len(s) for s in sheets)
    out = [Fraction(0)] * n
    for v, i in last_holder.items():
        out[i] += Fraction(mult[v], nk)
    return out


def check_samples():
    s1 = [[1, 2, 3, 4], [1, 2, 5, 6], [3, 4, 7, 8]]
    exp1 = [Fraction(0), Fraction(1, 2), Fraction(1, 2)]
    s2 = [[1, 2], [3, 4], [10, 5], [7, 8]]
    exp2 = [Fraction(1, 4)] * 4
    for s, exp in ((s1, exp1), (s2, exp2)):
        got = formula(s)
        assert got == exp, (s, got, exp)
    print("samples OK:", [float(x) for x in formula(s1)], [float(x) for x in formula(s2)])


def random_tests(trials=400, seed=1):
    rng = random.Random(seed)
    for t in range(trials):
        while True:
            n = rng.randint(1, 3)
            k = rng.randint(1, 3)
            if n * k <= 7:
                break
        pool_size = rng.randint(1, 4)          # small pool -> many collisions
        sheets = [[rng.randint(1, pool_size) for _ in range(k)] for _ in range(n)]
        b = brute(sheets)
        f = formula(sheets)
        assert sum(b) == 1 and sum(f) == 1, (sheets, b, f)
        if b != f:
            print("MISMATCH", sheets)
            print("  brute  ", [str(x) for x in b])
            print("  formula", [str(x) for x in f])
            return False
    print(f"{trials} random tests OK (n<=3, k<=3, values from tiny pools)")
    return True


if __name__ == "__main__":
    check_samples()
    ok = random_tests()
    # a couple of hand-picked heavy-duplicate cases
    for sheets in ([[1, 1, 1], [1, 1, 1]], [[1, 1], [1, 2], [2, 2]], [[2, 2], [1, 1], [1, 2]]):
        b, f = brute(sheets), formula(sheets)
        print(sheets, "brute", [str(x) for x in b], "formula", [str(x) for x in f],
              "OK" if b == f else "MISMATCH")
        ok = ok and b == f
    print("ALL OK" if ok else "FAILED")
