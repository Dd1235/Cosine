"""olympiadtraining: cost(S) = sum_j max_{i in S} a[i][j] for every subset S, obtained by writing
max as a sum of prefix-threshold contributions  max = sum_k (v_k - v_{k+1})*[S meets top-k]  and
turning "meets" into its complement, so cost(S) = TOT - sum_{T superset S} W[T]  -- one superset-sum
(SOS) DP over 2^N.  Then the answer for K is the min over subsets of size K.
Brute force: evaluate every subset directly."""
import random, itertools

def solve(a, N, M):
    W = [0]*(1 << N)
    TOT = 0
    for j in range(M):
        order = sorted(range(N), key=lambda i: -a[i][j])
        v = [a[i][j] for i in order] + [0]
        TOT += v[0]
        pref = 0
        for k in range(N):
            pref |= 1 << order[k]
            wgt = v[k] - v[k+1]
            if wgt: W[((1 << N) - 1) ^ pref] += wgt   # subsets avoiding the top-k
    G = W[:]
    for b in range(N):                                # superset sum
        for S in range(1 << N):
            if not (S >> b) & 1:
                G[S] += G[S | (1 << b)]
    cost = [TOT - G[S] for S in range(1 << N)]
    best = [None]*(N+1)
    for S in range(1 << N):
        k = bin(S).count('1')
        if k and (best[k] is None or cost[S] < best[k]): best[k] = cost[S]
    return best

def brute(a, N, M):
    best = [None]*(N+1)
    for k in range(1, N+1):
        for S in itertools.combinations(range(N), k):
            c = sum(max(a[i][j] for i in S) for j in range(M))
            if best[k] is None or c < best[k]: best[k] = c
    return best

# samples
assert solve([[1,3],[3,2]], 2, 2)[1] == 4
r = solve([[1,4,9],[2,6,3],[3,5,5]], 3, 3)
assert r[1:] == [11,14,18], r

random.seed(17)
bad = 0
for t in range(200):
    N = random.randint(1, 7); M = random.randint(1, 5)
    a = [[random.randint(0, 20) for _ in range(M)] for _ in range(N)]
    s, b = solve(a, N, M), brute(a, N, M)
    if s[1:] != b[1:]:
        bad += 1; print("MISMATCH", a, s, b)
print("samples ok (4 / 11,14,18); mismatches =", bad)
