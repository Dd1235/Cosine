"""Jurassic Jungle: the answer set {C_n, K_{n/2,n/2}, K_n} vs exhaustive search.

'Every maximal simple path from every vertex is Hamiltonian and its far end is
adjacent to the start' is exactly the classical randomly-Hamiltonian (randomly
traceable) property.  Chartrand & Kronk: such graphs are exactly the cycle C_n,
the complete bipartite K_{n,n}, and the complete graph K_n.  So for given N, M
the answer is YES iff M == N, or M == (N/2)^2 with N even, or M == N(N-1)/2.
"""
import itertools


def happy(N, adj):
    """True iff every maximal simple path from every start is Hamiltonian and
    closes back to the start."""
    for s in range(N):
        stack = [(s, 1 << s, 1)]
        while stack:
            v, mask, cnt = stack.pop()
            nxt = [u for u in range(N) if (adj[v] >> u & 1) and not (mask >> u & 1)]
            if not nxt:
                if cnt != N or not (adj[v] >> s & 1):
                    return False
                continue
            for u in nxt:
                stack.append((u, mask | (1 << u), cnt + 1))
    return True


def formula_ok(N, M):
    if M == N:
        return True
    if N % 2 == 0 and M == (N // 2) ** 2:
        return True
    if M == N * (N - 1) // 2:
        return True
    return False


def build(N, M):
    if M == N:
        return [(i + 1, (i + 1) % N + 1) for i in range(N)]
    if N % 2 == 0 and M == (N // 2) ** 2:
        h = N // 2
        return [(i + 1, j + 1) for i in range(h) for j in range(h, N)]
    if M == N * (N - 1) // 2:
        return [(i + 1, j + 1) for i in range(N) for j in range(i + 1, N)]
    return None


def check_build(N, M):
    e = build(N, M)
    assert e is not None and len(e) == M, (N, M, len(e) if e else None)
    assert len(set(tuple(sorted(x)) for x in e)) == M
    adj = [0] * N
    for (u, v) in e:
        assert u != v
        adj[u - 1] |= 1 << (v - 1)
        adj[v - 1] |= 1 << (u - 1)
    assert happy(N, adj), (N, M)


def main():
    assert formula_ok(3, 3) and not formula_ok(5, 4)
    print("samples ok")
    for N in range(3, 7):
        full = N * (N - 1) // 2
        good_M = set()
        pairs = [(i, j) for i in range(N) for j in range(i + 1, N)]
        for mask in range(1 << full):
            adj = [0] * N
            m = 0
            for b, (i, j) in enumerate(pairs):
                if mask >> b & 1:
                    adj[i] |= 1 << j
                    adj[j] |= 1 << i
                    m += 1
            if happy(N, adj):
                good_M.add(m)
        pred = set(M for M in range(0, full + 1) if formula_ok(N, M))
        print("  N=%d exhaustive feasible M=%s  predicted=%s"
              % (N, sorted(good_M), sorted(pred)))
        assert good_M == pred, (N, good_M, pred)
    for N in range(3, 9):
        for M in range(0, N * (N - 1) // 2 + 1):
            if formula_ok(N, M):
                check_build(N, M)
    print("constructions for N<=8 all verified randomly-Hamiltonian")
    for N in range(3, 31):          # shape/size only for the full range
        for M in range(0, N * (N - 1) // 2 + 1):
            if formula_ok(N, M):
                e = build(N, M)
                assert len(e) == M and len(set(tuple(sorted(x)) for x in e)) == M
                assert all(1 <= u <= N and 1 <= v <= N and u != v for u, v in e)
    print("constructions for N<=30 are simple graphs with exactly M edges")


main()
