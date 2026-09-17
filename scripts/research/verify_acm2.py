"""Kattis acm2 (2015 ICPC Singapore, C).

Task: 300-minute contest, N<=13 solve-time estimates, problem p must be attempted
first.  Maximise the number solved, then minimise ICPC penalty (sum of the
finishing times of the solved problems).

Solution under test: if t[p] > 300 the answer is "0 0"; otherwise solve p first,
then take the remaining problems in increasing order of time while the running
clock stays <= 300.  Penalty = sum of the prefix sums.  O(N log N) / O(N).

Brute force: all permutations that start with p (N <= 8).
"""
import itertools, random

LIMIT = 300

def solve(n, p, t):
    if t[p] > LIMIT:
        return (0, 0)
    clock = t[p]
    ac, pen = 1, clock
    for x in sorted(t[i] for i in range(n) if i != p):
        if clock + x <= LIMIT:
            clock += x
            ac += 1
            pen += clock
    return (ac, pen)

def brute(n, p, t):
    best = (0, 0)
    for perm in itertools.permutations([i for i in range(n) if i != p]):
        order = (p,) + perm
        clock, ac, pen = 0, 0, 0
        for i in order:
            if clock + t[i] > LIMIT:
                break
            clock += t[i]
            ac += 1
            pen += clock
        if ac > best[0] or (ac == best[0] and ac > 0 and pen < best[1]):
            best = (ac, pen)
    return best

def samples():
    cases = [((7, 0, [30, 270, 995, 996, 997, 998, 999]), (2, 330)),
             ((7, 1, [30, 270, 995, 996, 997, 998, 999]), (2, 570)),
             ((7, 2, [30, 270, 995, 996, 997, 998, 999]), (0, 0)),
             ((3, 0, [1, 300, 299]), (2, 301))]
    for (n, p, t), want in cases:
        got = solve(n, p, t)
        assert got == want, (n, p, t, got, want)
    print("samples OK")

def fuzz(trials=2000):
    rnd = random.Random(11)
    for _ in range(trials):
        n = rnd.randint(2, 7)
        t = rnd.sample(range(1, 400), n)      # distinct, as the statement promises
        p = rnd.randrange(n)
        a, b = solve(n, p, t), brute(n, p, t)
        if a != b:
            print("MISMATCH", n, p, t, a, b)
            return False
    print("fuzz OK (%d random cases, n<=7)" % trials)
    return True

if __name__ == "__main__":
    samples()
    assert fuzz()
