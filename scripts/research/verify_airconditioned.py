"""Kattis airconditioned (2015 ICPC Singapore, A).

Task: given N intervals [L,U], choose the fewest temperatures (points) so that
every interval contains at least one chosen point == minimum piercing set.

Solution under test: greedy, sort by right endpoint, place a point at U whenever
the current interval is not already pierced.  O(N log N) time, O(N) space.

Brute force: exhaustive search over subsets of candidate points (all endpoints
suffice: an optimal piercing set can always be pushed right onto some U).
"""
import itertools, random

def greedy(iv):
    rooms = 0
    last = None
    for l, u in sorted(iv, key=lambda p: p[1]):
        if last is None or l > last:
            rooms += 1
            last = u
    return rooms

def brute(iv):
    cands = sorted({u for _, u in iv} | {l for l, _ in iv})
    for k in range(0, len(cands) + 1):
        for comb in itertools.combinations(cands, k):
            if all(any(l <= c <= u for c in comb) for l, u in iv):
                return k
    return len(iv)

def samples():
    s1 = [(1, 2), (2, 4), (5, 6)]
    s2 = [(1, 2), (3, 5), (4, 6), (7, 9), (8, 10)]
    assert greedy(s1) == 2, greedy(s1)
    assert greedy(s2) == 3, greedy(s2)
    print("samples OK")

def fuzz(trials=3000):
    rnd = random.Random(7)
    for t in range(trials):
        n = rnd.randint(2, 7)
        iv = []
        for _ in range(n):
            a = rnd.randint(1, 2 * n)
            b = rnd.randint(1, 2 * n)
            if a > b:
                a, b = b, a
            iv.append((a, b))
        g, b_ = greedy(iv), brute(iv)
        if g != b_:
            print("MISMATCH", iv, g, b_)
            return False
    print("fuzz OK (%d random cases, n<=7)" % trials)
    return True

if __name__ == "__main__":
    samples()
    assert fuzz()
