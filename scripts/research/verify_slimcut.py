"""Brute force check for kattis-slimcut.

Characterisation under test: a cut whose heaviest crossing edge is at most W is
exactly a union of connected components of the graph restricted to edges of
weight > W, and those components are the components of the MAXIMUM spanning
tree with its edges of weight <= W deleted.  So only the n-1 maximum-spanning-
tree weights are candidate thresholds, and at threshold W the best denominator
is best(W) = the largest subset sum of component sizes that is at most
floor(n/2) (take the complement whenever a union exceeds half).  The answer is
min over the tree weights w of w / best(w).

Compared here against exhaustive enumeration of all 2^(n-1) - 1 cuts.
"""
import random
from itertools import combinations


def solve(n, edges):
    # maximum spanning tree by Kruskal on decreasing weight
    par = list(range(n))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    tree = []
    for x, y, w in sorted(edges, key=lambda e: -e[2]):
        a, b = find(x), find(y)
        if a != b:
            par[a] = b
            tree.append((x, y, w))
    best_ratio = float("inf")
    half = n // 2
    for W in sorted({w for _, _, w in tree}):
        # components using tree edges of weight > W
        par2 = list(range(n))

        def find2(x):
            while par2[x] != x:
                par2[x] = par2[par2[x]]
                x = par2[x]
            return x

        for x, y, w in tree:
            if w > W:
                a, b = find2(x), find2(y)
                if a != b:
                    par2[a] = b
        sizes = {}
        for v in range(n):
            r = find2(v)
            sizes[r] = sizes.get(r, 0) + 1
        comp = list(sizes.values())
        if len(comp) < 2:
            continue
        reach = 1  # bitset of attainable subset sums
        for s in comp:
            reach |= reach << s
        best = 0
        for x in range(half, 0, -1):
            if reach >> x & 1:
                best = x
                break
        if best:
            best_ratio = min(best_ratio, W / best)
    return best_ratio


def brute(n, edges):
    best = float("inf")
    for size in range(1, n):
        for S in combinations(range(n), size):
            s = set(S)
            cross = [w for x, y, w in edges if (x in s) != (y in s)]
            if not cross:
                continue
            best = min(best, max(cross) / min(len(s), n - len(s)))
    return best


def main():
    sample = [(0, 1, 3), (1, 2, 4), (0, 3, 1), (1, 4, 1), (2, 5, 5), (3, 4, 2), (4, 5, 4)]
    got = solve(6, sample)
    assert abs(got - 4 / 3) < 1e-9, got
    print("sample OK (%.11f)" % got)

    rng = random.Random(31)
    bad = 0
    for _ in range(300):
        n = rng.randint(2, 8)
        # random connected graph
        edges = []
        used = set()
        for i in range(1, n):
            j = rng.randrange(i)
            edges.append((i, j, rng.randint(1, 12)))
            used.add((min(i, j), max(i, j)))
        extra = rng.randint(0, n)
        for _ in range(extra):
            a, b = rng.randrange(n), rng.randrange(n)
            if a != b and (min(a, b), max(a, b)) not in used:
                used.add((min(a, b), max(a, b)))
                edges.append((a, b, rng.randint(1, 12)))
        a, b = solve(n, edges), brute(n, edges)
        if abs(a - b) > 1e-9:
            bad += 1
            print("MISMATCH n=%d edges=%s mine=%s brute=%s" % (n, edges, a, b))
            if bad > 5:
                return
    print("random trials %s" % ("OK" if bad == 0 else "%d FAILURES" % bad))

    # the union of several components really is needed (a single component is not enough)
    star = [(0, i, 10) for i in range(1, 13, 3)]
    for blob in range(1, 13, 3):
        star += [(blob, blob + 1, 100), (blob + 1, blob + 2, 100)]
    n = 13
    print("blob star: solve=%.6f brute=%.6f (single-component-only would give %.6f)"
          % (solve(n, star), brute(n, star), 10 / 3))


if __name__ == "__main__":
    main()
