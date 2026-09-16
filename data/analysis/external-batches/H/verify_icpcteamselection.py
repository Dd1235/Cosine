"""icpcteamselection: greedy (sort desc, take every 2nd of the top 2N) vs exhaustive partition brute force."""
import random, itertools

def solve(n, p):
    a = sorted(p, reverse=True)
    # discard the n smallest; from the top 2n, medians are positions 1,3,5,...
    return sum(a[1:2*n:2])

def brute(n, p):
    best = [0]
    items = list(range(3*n))
    def rec(rem, acc):
        if not rem:
            best[0] = max(best[0], acc); return
        first = rem[0]
        rest = rem[1:]
        for pair in itertools.combinations(rest, 2):
            team = sorted([p[first], p[pair[0]], p[pair[1]]])
            nrem = [x for x in rest if x not in pair]
            rec(nrem, acc + team[1])
    rec(items, 0)
    return best[0]

random.seed(7)
# sample
assert solve(2, [8,8,6,9,10,9]) == 17, solve(2,[8,8,6,9,10,9])
bad = 0
for t in range(400):
    n = random.randint(1, 3)
    p = [random.randint(1, 20) for _ in range(3*n)]
    s, b = solve(n, p), brute(n, p)
    if s != b:
        bad += 1; print("MISMATCH", n, p, s, b)
print("sample ok; random trials done, mismatches =", bad)
