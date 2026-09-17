"""Kattis control (2015 ICPC Singapore, D).

Task: recipes are considered in order 1..N.  Recipe i is brewed iff its ingredient
set can be assembled from (a) still-unused ingredients and (b) whole existing
cauldrons -- a cauldron may only be poured in if ALL of its contents are listed in
the recipe.  Brewing is forced whenever it is possible.  Count the brews.
N <= 200000, sum of ingredient-list lengths <= 500000.

Key invariant: every ingredient that has been used sits in exactly one live
cauldron whose contents are precisely that ingredient's group, and unused
ingredients are singleton groups.  So recipe S is brewable iff every group that
meets S is contained in S, i.e. iff the sizes of the distinct groups met by S add
up to |S|.  Brewing then unions all of S into one group.

Solution under test: union-find with sizes, O(sum(M) * alpha) time, O(max id) space.
Brute force: keeps the explicit list of cauldrons (sets) and unused ingredients and
replays the statement's rules literally.
"""
import random

# ---------- union-find solution ----------
def solve(recipes, maxing=None):
    ids = {x for r in recipes for x in r}
    parent = {x: x for x in ids}
    size = {x: 1 for x in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    count = 0
    for r in recipes:
        roots = {find(x) for x in r}
        if sum(size[q] for q in roots) != len(r):
            continue
        count += 1
        roots = list(roots)
        big = max(roots, key=lambda q: size[q])
        for q in roots:
            if q != big:
                parent[q] = big
                size[big] += size[q]
    return count

# ---------- literal simulation ----------
def brute(recipes):
    cauldrons = []          # list of live cauldrons, each a frozenset
    used = set()
    count = 0
    for r in recipes:
        S = set(r)
        touched = [c for c in cauldrons if c & S]
        if any(not (c <= S) for c in touched):
            continue
        # every ingredient of S not inside a touched cauldron must be unused
        covered = set().union(*touched) if touched else set()
        if any(x in used and x not in covered for x in S):
            continue
        count += 1
        cauldrons = [c for c in cauldrons if not (c & S)]
        cauldrons.append(frozenset(S))
        used |= S
    return count

def samples():
    s1 = [[1, 2], [3, 4], [1, 5], [1, 2, 3, 4, 5], [1, 2]]
    s2 = [[1, 2], [1], [2]]
    assert solve(s1) == 3, solve(s1)
    assert solve(s2) == 1, solve(s2)
    assert brute(s1) == 3 and brute(s2) == 1
    print("samples OK")

def fuzz(trials=4000):
    rnd = random.Random(2024)
    for _ in range(trials):
        n = rnd.randint(2, 8)
        ning = rnd.randint(2, 6)
        recipes = []
        for _ in range(n):
            m = rnd.randint(1, ning)
            recipes.append(rnd.sample(range(1, ning + 1), m))
        a, b = solve(recipes), brute(recipes)
        if a != b:
            print("MISMATCH", recipes, a, b)
            return False
    print("fuzz OK (%d random cases) -- union-find matches the literal simulation" % trials)
    return True

if __name__ == "__main__":
    samples()
    assert fuzz()
