"""Grab a Graph: build both graphs for many A and recount shortest paths.

Both constructions use the same idea: lay vertices on a line with potentials
d_0 < d_1 < ... and give an edge (i, j) the weight d_j - d_i.  Any walk's weight
telescopes to at least |d_end - d_start|, with equality exactly for the
index-increasing walks, so *every* increasing path is a shortest path and the
count is a plain DAG count.
  Bash  (<=72 vertices, <=2525 edges): x_0..x_60 with d_i = i and every edge
    x_i - x_j, so #paths(x_j) = 2^(j-1); vertex 2 is joined to the x_{i+1} for
    every set bit i of A.  62 vertices, <= 1890 edges.
  Chikapu (<=88 vertices, <=214 edges): y_0..y_86 with only the two edges
    y_{i-2} - y_i and y_{i-1} - y_i, so #paths(y_i) = Fib(i+1); vertex 2 is
    joined to the Zeckendorf terms of A.  88 vertices, 171 + <=43 = <=214 edges.
"""
import random
from heapq import heappush, heappop

LIMIT = 10 ** 18


def bash_graph(A):
    if A == 0:
        return 2, []
    K = 60                                   # bits 0..59 cover A < 2^60
    # vertex ids: 1 = x_0, 2 = target, 3.. = x_1..x_K
    xid = {0: 1}
    for i in range(1, K + 1):
        xid[i] = 2 + i
    n = K + 2
    edges = []
    for i in range(0, K + 1):
        for j in range(i + 1, K + 1):
            edges.append((xid[i], xid[j], j - i))
    for b in range(60):
        if A >> b & 1:
            i = b + 1                        # #paths(x_i) = 2^(i-1) = 2^b
            edges.append((xid[i], 2, (K + 1) - i))
    return n, edges


def chikapu_graph(A):
    if A == 0:
        return 2, []
    K = 86                                   # y_0..y_86, #paths(y_i) = F(i+1)
    fib = [0, 1]
    while len(fib) < K + 3:
        fib.append(fib[-1] + fib[-2])
    yid = {0: 1}
    for i in range(1, K + 1):
        yid[i] = 2 + i
    n = K + 2
    edges = [(yid[0], yid[1], 1)]
    for i in range(2, K + 1):
        edges.append((yid[i - 1], yid[i], 1))
        edges.append((yid[i - 2], yid[i], 2))
    # Zeckendorf: A = sum of non-consecutive F(k), 2 <= k <= K+1
    assert A < fib[K + 2], "A must be below F(K+2) = %d" % fib[K + 2]
    rest = A
    k = K + 1
    terms = 0
    while rest > 0:
        while fib[k] > rest:
            k -= 1
        assert k >= 2
        edges.append((yid[k - 1], 2, (K + 1) - (k - 1)))
        rest -= fib[k]
        terms += 1
        k = max(2, k - 2)
    assert terms <= 43, terms
    return n, edges


def count_shortest(n, edges):
    g = [[] for _ in range(n + 1)]
    for (u, v, w) in edges:
        g[u].append((v, w))
        g[v].append((u, w))
    INF = float('inf')
    dist = [INF] * (n + 1)
    cnt = [0] * (n + 1)
    dist[1] = 0
    cnt[1] = 1
    pq = [(0, 1)]
    done = [False] * (n + 1)
    while pq:
        d, u = heappop(pq)
        if done[u]:
            continue
        done[u] = True
        for (v, w) in g[u]:
            if done[v]:
                continue
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                cnt[v] = cnt[u]
                heappush(pq, (nd, v))
            elif nd == dist[v]:
                cnt[v] += cnt[u]
    return cnt[2] if dist[2] < INF else 0


def check(A):
    n, e = bash_graph(A)
    assert n <= 72 and len(e) <= 2525, (A, n, len(e))
    validate(n, e)
    got = count_shortest(n, e)
    assert got == A, ("bash", A, got)
    n, e = chikapu_graph(A)
    assert n <= 88 and len(e) <= 214, (A, n, len(e), "chikapu size")
    validate(n, e)
    got = count_shortest(n, e)
    assert got == A, ("chikapu", A, got)


def validate(n, edges):
    seen = set()
    for (u, v, w) in edges:
        assert 1 <= u <= n and 1 <= v <= n and u != v
        assert 1 <= w <= 10 ** 9
        key = (min(u, v), max(u, v))
        assert key not in seen
        seen.add(key)
    assert 2 <= n


def main():
    for A in [0, 1, 2, 3, 4, 5, 6, 7, 8, 100, 12345]:
        check(A)
    print("small A ok (including A = 0 -> empty 2-vertex graph)")
    random.seed(2)
    worst_b = worst_c = 0
    tests = [LIMIT, LIMIT - 1, 2 ** 59, 679891637638612258, 679891637638612259,
             999999999999999999,
             2 ** 59 - 1,               # 59 set bits: worst case for Bash
             679891637638612257]        # F(87)-1: 43 Zeckendorf terms, worst for Chikapu
    tests += [random.randint(1, LIMIT) for _ in range(150)]
    tests += [random.randint(1, 10 ** 6) for _ in range(50)]
    for A in tests:
        check(A)
        worst_b = max(worst_b, len(bash_graph(A)[1]))
        worst_c = max(worst_c, len(chikapu_graph(A)[1]))
    print("%d values of A up to 1e18 verified by Dijkstra path counting" % (len(tests) + 11))
    print("  worst Bash edges = %d (<=2525), worst Chikapu edges = %d (<=214)"
          % (worst_b, worst_c))


main()
