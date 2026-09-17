"""Brute force check for kattis-teamup.

The classes form a laminar family, so inclusion gives a forest.  A set S_v is
covered either by one player of class v or by covering every child of v, and the
latter is only possible when the children's sets exactly partition S_v.  Hence
g(v) = cnt[v] + (min over children g(c) if the children tile S_v else 0), and the
answer is min over the maximal sets (roots) of g(root), or 0 when the roots do
not cover {1..n}.  Checked against an exhaustive max-disjoint-cover search, and
the emitted teaming is validated.
"""
import random
from functools import lru_cache


def solve(n, sets, classes):
    """sets: list of frozensets (1-indexed skills). classes: per-player class idx.
    Returns (count, teams) with teams as lists of 1-indexed player labels."""
    m = len(sets)
    order = sorted(range(m), key=lambda i: -len(sets[i]))
    owner = {}
    parent = [-1] * m
    children = [[] for _ in range(m)]
    for i in order:
        p = None
        for x in sets[i]:
            p = owner.get(x, -1)
            break
        parent[i] = p if p is not None else -1
        if parent[i] != -1:
            children[parent[i]].append(i)
        for x in sets[i]:
            owner[x] = i
    roots = [i for i in range(m) if parent[i] == -1]
    if set().union(*[sets[i] for i in roots]) != set(range(1, n + 1)):
        return 0, []
    if sum(len(sets[i]) for i in roots) != n:
        return 0, []  # roots overlap: not laminar / cannot happen in valid input

    players_of = [[] for _ in range(m)]
    for pi, c in enumerate(classes):
        players_of[c].append(pi + 1)

    tiles = [sum(len(sets[c]) for c in children[i]) == len(sets[i]) for i in range(m)]

    g = [0] * m
    seen = set()
    stack = [(i, False) for i in roots]
    while stack:
        v, post = stack.pop()
        if not post:
            stack.append((v, True))
            for c in children[v]:
                stack.append((c, False))
        else:
            base = len(players_of[v])
            if children[v] and tiles[v]:
                base += min(g[c] for c in children[v])
            g[v] = base
    ans = min(g[i] for i in roots)
    if ans == 0:
        return 0, []

    def covers(v, need):
        """`need` covers of S_v as lists of players."""
        out = [[p] for p in players_of[v][:need]]
        if len(out) < need and children[v] and tiles[v]:
            rest = need - len(out)
            parts = [covers(c, rest) for c in children[v]]
            for j in range(rest):
                team = []
                for pl in parts:
                    team.extend(pl[j])
                out.append(team)
        return out[:need]

    per_root = [covers(i, ans) for i in roots]
    teams = []
    for j in range(ans):
        t = []
        for pr in per_root:
            t.extend(pr[j])
        teams.append(t)
    return ans, teams


def brute(n, sets, classes):
    p = len(classes)
    full = (1 << n) - 1
    pmask = []
    for c in classes:
        msk = 0
        for x in sets[c]:
            msk |= 1 << (x - 1)
        pmask.append(msk)

    @lru_cache(maxsize=None)
    def f(avail):
        best = 0
        # enumerate subsets of avail that cover everything
        sub = avail
        while sub:
            cov = 0
            s = sub
            while s:
                b = s & -s
                cov |= pmask[b.bit_length() - 1]
                s ^= b
            if cov == full:
                best = max(best, 1 + f(avail ^ sub))
            sub = (sub - 1) & avail
        return best

    return f((1 << p) - 1)


def gen_laminar(n, rng):
    """Random laminar family over {1..n}; returns list of frozensets."""
    fam = []

    def rec(elems, depth):
        s = frozenset(elems)
        if rng.random() < 0.8:
            fam.append(s)
        if len(elems) <= 1 or depth > 3:
            return
        rng.shuffle(elems)
        cut = rng.randint(1, len(elems) - 1)
        parts = [elems[:cut], elems[cut:]]
        for pt in parts:
            if pt and rng.random() < 0.85:
                rec(list(pt), depth + 1)

    rec(list(range(1, n + 1)), 0)
    out = []
    seen = set()
    for s in fam:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def main():
    # statement sample
    sets = [frozenset([1]), frozenset([2]), frozenset([1, 2]), frozenset([3])]
    classes = [1 - 1, 2 - 1, 2 - 1, 3 - 1, 4 - 1, 4 - 1, 2 - 1]
    cnt, teams = solve(3, sets, classes)
    assert cnt == 2, (cnt, teams)
    print("sample 1 OK (2 teams):", teams)

    rng = random.Random(5)
    bad = tried = 0
    for _ in range(400):
        n = rng.randint(1, 4)
        fam = gen_laminar(n, rng)
        if not fam:
            continue
        p = rng.randint(1, 7)
        classes = [rng.randrange(len(fam)) for _ in range(p)]
        tried += 1
        a, teams = solve(n, fam, classes)
        b = brute(n, fam, classes)
        ok = a == b
        used = set()
        for t in teams:
            cov = set()
            for pl in t:
                assert pl not in used, "player reused"
                used.add(pl)
                cov |= fam[classes[pl - 1]]
            if cov != set(range(1, n + 1)):
                ok = False
        if not ok:
            bad += 1
            print("MISMATCH n=%d fam=%s classes=%s mine=%s brute=%s teams=%s"
                  % (n, [sorted(s) for s in fam], classes, a, b, teams))
            if bad > 5:
                return
    print("%d random cases, %s" % (tried, "OK" if bad == 0 else "%d FAILURES" % bad))


if __name__ == "__main__":
    main()
