"""Brute force check for kattis-scaffolding.

Model: cell (column i, level h), 1 <= h <= H_i, must all be placed.  A round is
a walk that starts on the ground, only steps left / right / up onto cells of the
target shape, and places at most M of the cells it walks over.

Claimed solution: cells of the shape at level h form maximal intervals; interval
[l,r] at level h has as children the maximal intervals it splits into at level
h+1, which is the Cartesian tree of H by minimum.  Every round is a root-to-node
path of that tree, so the number of rounds through a node v is at least the sum
over its children and at least ceil(cells(v) / M), where cells(v) counts the
whole subtree from v's base level up.  f(v) = max(sum_children f, ceil(cells/M)),
answer = sum over roots.  Tested against BFS over filled-cell sets.
"""
import random
from functools import lru_cache
from math import ceil


def solve(H, M):
    n = len(H)

    def rec(l, r, base):
        if l > r:
            return 0
        m = min(H[l:r + 1])
        cells = sum(H[i] - base + 1 for i in range(l, r + 1))
        if cells <= 0:
            return 0
        child = 0
        i = l
        while i <= r:
            if H[i] > m:
                j = i
                while j <= r and H[j] > m:
                    j += 1
                child += rec(i, j - 1, m + 1)
                i = j
            else:
                i += 1
        return max(child, -(-cells // M))

    total = 0
    i = 0
    while i < n:
        if H[i] >= 1:
            j = i
            while j < n and H[j] >= 1:
                j += 1
            total += rec(i, j - 1, 1)
            i = j
        else:
            i += 1
    return total


def brute(H, M):
    n = len(H)
    cells = [(c, h) for c in range(n) for h in range(1, H[c] + 1)]
    idx = {cell: i for i, cell in enumerate(cells)}
    full = (1 << len(cells)) - 1
    if full == 0:
        return 0

    def one_round(state):
        """All filled-sets reachable by a single round from `state`."""
        out = set()
        seen = set()
        stack = []
        for c in range(n):
            stack.append((c, 0, state, 0))
        while stack:
            c, h, st, used = stack.pop()
            key = (c, h, st, used)
            if key in seen:
                continue
            seen.add(key)
            out.add(st)
            for nc, nh in ((c - 1, h), (c + 1, h), (c, h + 1)):
                if nc < 0 or nc >= n:
                    continue
                if nh == 0:
                    stack.append((nc, nh, st, used))
                    continue
                if nh > H[nc]:
                    continue
                bit = 1 << idx[(nc, nh)]
                if st & bit:
                    stack.append((nc, nh, st, used))
                elif used < M:
                    stack.append((nc, nh, st | bit, used + 1))
        return out

    # BFS over filled sets
    dist = {0: 0}
    frontier = [0]
    while frontier:
        nxt = []
        for st in frontier:
            for ns in one_round(st):
                if ns not in dist:
                    dist[ns] = dist[st] + 1
                    if ns == full:
                        return dist[ns]
                    nxt.append(ns)
        frontier = nxt
    return None


def main():
    assert solve([2, 1, 5], 4) == 2, solve([2, 1, 5], 4)
    assert solve([2, 1, 2, 1, 2], 10) == 3, solve([2, 1, 2, 1, 2], 10)
    print("samples OK")
    random.seed(11)
    bad = 0
    tried = 0
    for _ in range(300):
        n = random.randint(1, 5)
        maxh = random.randint(0, 4)
        H = [random.randint(0, maxh) for _ in range(n)]
        if sum(H) > 12:
            continue
        M = random.randint(1, 5)
        tried += 1
        a, b = solve(H, M), brute(H, M)
        if a != b:
            bad += 1
            print("MISMATCH H=%s M=%d mine=%s brute=%s" % (H, M, a, b))
            if bad > 6:
                return
    print("%d random cases, %s" % (tried, "OK" if bad == 0 else "%d FAILURES" % bad))


if __name__ == "__main__":
    main()
