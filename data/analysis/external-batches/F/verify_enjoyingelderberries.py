"""Enjoying Elderberries -- verification.

Solution under test (solve):
  * a bird's controlled area is a subtree, so all the areas containing a given
    berry are nested; the owner of a berry is the bird of its label whose area
    root is deepest.  With at most seven birds per label that owner is found by
    scanning the label's bird list, using an Euler tour for the ancestor test.
  * turning the tiny birds giant only ENLARGES areas (subtree(parent) becomes
    subtree(closest big ancestor)), so every bird still contains its own
    berries; what can break is that a same-label bird now sits deeper.
  * a berry must keep its owner, so a berry's label must equal its owner's:
    each bird and the berries it owns form one block that is relabelled all at
    once or not at all, and since all of them already share the bird's label
    the cost of relabelling a block is its whole size.  A relabelled block can
    always take a brand new label, which clashes with nothing, so the only
    constraint is on the blocks that KEEP label L: pairwise, two kept birds of
    label L must not have equal new areas (rule: distinct areas) and the deeper
    one must not swallow a berry of the shallower one (rule: owners unchanged).
  * that makes every label independent, and 'no eight birds share a label'
    bounds each label class at seven birds -- so the best kept set is the
    maximum-weight conflict-free subset, found by trying all 2^7 subsets.
    Answer = total weight - sum of the best kept weights.  O(n log n).

Checks below: the three samples; 700+ random trees against an exhaustive search
over all labellings (optimality), every produced labelling replayed through an
independent simulator of the rules (validity); and a 150k-vertex timing run.
"""
import itertools
import random
import sys
import time
from bisect import bisect_left


# --------------------------------------------------------------- solution
def parse(text):
    it = text.split()
    pos = 0
    n = int(it[pos]); pos += 1
    par = [0] * (n + 1)
    kind = [''] * (n + 1)          # B,S branch ; G,T,E leaf
    lab = [''] * (n + 1)
    for i in range(1, n + 1):
        par[i] = int(it[pos]); pos += 1
        kind[i] = it[pos]; pos += 1
        if kind[i] in 'GTE':
            lab[i] = it[pos]; pos += 1
    return n, par, kind, lab


def solve(text):
    n, par, kind, lab = parse(text)
    ch = [[] for _ in range(n + 1)]
    for i in range(2, n + 1):
        ch[par[i]].append(i)
    big = [0] * (n + 1)
    depth = [0] * (n + 1)
    for i in range(2, n + 1):                 # parents have the smaller index
        p = par[i]
        depth[i] = depth[p] + 1
        big[i] = p if kind[p] == 'B' else big[p]
    tin = [0] * (n + 1)
    tout = [0] * (n + 1)
    timer = 0
    st = [(1, 0)]
    while st:
        v, state = st.pop()
        if state == 0:
            tin[v] = timer
            timer += 1
            st.append((v, 1))
            for c in reversed(ch[v]):
                st.append((c, 0))
        else:
            tout[v] = timer - 1

    def anc(a, x):
        return tin[a] <= tin[x] <= tout[a]

    birds = [v for v in range(1, n + 1) if kind[v] in 'GT']
    berries = [v for v in range(1, n + 1) if kind[v] == 'E']
    area_old, area_new = {}, {}
    for v in birds:
        area_old[v] = par[v] if kind[v] == 'T' else big[v]
        area_new[v] = big[v]
    by_label = {}
    for v in birds:
        by_label.setdefault(lab[v], []).append(v)
    owner = {}
    owned = {v: [] for v in birds}
    for x in berries:
        best, bd = -1, -1
        for u in by_label.get(lab[x], ()):
            r = area_old[u]
            if anc(r, x) and depth[r] > bd:
                bd, best = depth[r], u
        assert best != -1, "berry %d has no owner" % x
        owner[x] = best
        owned[best].append(tin[x])
    for v in birds:
        owned[v].sort()

    def owns_in(w, r):
        lst = owned[w]
        i = bisect_left(lst, tin[r])
        return i < len(lst) and lst[i] <= tout[r]

    weight = {v: 1 + len(owned[v]) for v in birds}
    changed = []
    for L, S in by_label.items():
        m = len(S)
        assert m <= 7, "label %r is carried by %d birds" % (L, m)
        bad = [0] * m
        for i in range(m):
            for j in range(i + 1, m):
                u, w = S[i], S[j]
                ru, rw = area_new[u], area_new[w]
                clash = (ru == rw
                         or (anc(rw, ru) and owns_in(w, ru))
                         or (anc(ru, rw) and owns_in(u, rw)))
                if clash:
                    bad[i] |= 1 << j
                    bad[j] |= 1 << i
        bestmask, bestw = 0, -1
        for mask in range(1 << m):
            tw, ok = 0, True
            for i in range(m):
                if mask >> i & 1:
                    if bad[i] & mask:
                        ok = False
                        break
                    tw += weight[S[i]]
            if ok and tw > bestw:
                bestw, bestmask = tw, mask
        for i in range(m):
            if not (bestmask >> i & 1):
                changed.append(S[i])

    used = set(lab[v] for v in range(1, n + 1) if lab[v])
    alpha = [chr(c) for c in range(97, 123)]

    def fresh():
        for ln in range(1, 6):
            for t in itertools.product(alpha, repeat=ln):
                s = ''.join(t)
                if s not in used:
                    yield s
    g = fresh()
    inv = {}
    for x in berries:
        inv.setdefault(owner[x], []).append(x)
    out = []
    for v in changed:
        s = next(g)
        out.append((v, s))
        for x in inv.get(v, ()):
            out.append((x, s))
    return "\n".join([str(len(out))] + ["%d %s" % vs for vs in out])


# ------------------------------------------- independent rules simulator
def build(n, par, kind):
    big = [0] * (n + 1)
    depth = [0] * (n + 1)
    for i in range(2, n + 1):
        p = par[i]
        depth[i] = depth[p] + 1
        big[i] = p if kind[p] == 'B' else big[p]
    ch = [[] for _ in range(n + 1)]
    for i in range(2, n + 1):
        ch[par[i]].append(i)
    sub = [set() for _ in range(n + 1)]
    for v in range(n, 0, -1):
        sub[v].add(v)
        for c in ch[v]:
            sub[v] |= sub[c]
    return big, depth, sub


def owners(n, par, kind, lab, big, depth, sub, all_giant):
    """berry -> bird under the stated rules, or None if a rule is broken"""
    birds = [v for v in range(1, n + 1) if kind[v] in 'GT']
    berries = [v for v in range(1, n + 1) if kind[v] == 'E']
    area = {v: (big[v] if (all_giant or kind[v] == 'G') else par[v])
            for v in birds}
    cnt = {}
    for v in birds:
        cnt[lab[v]] = cnt.get(lab[v], 0) + 1
        if cnt[lab[v]] >= 8:
            return None
    seen = set()
    for v in birds:
        key = (lab[v], area[v])
        if key in seen:
            return None
        seen.add(key)
    res = {}
    for x in berries:
        best, bd = -1, -1
        for u in birds:
            if lab[u] == lab[x] and x in sub[area[u]] and depth[area[u]] > bd:
                bd, best = depth[area[u]], u
        if best == -1:
            return None
        res[x] = best
    return res


def validate(text, answer):
    """apply the answer, replay the rules, return the number of changed labels"""
    n, par, kind, lab = parse(text)
    big, depth, sub = build(n, par, kind)
    base = owners(n, par, kind, lab, big, depth, sub, False)
    assert base is not None
    toks = answer.split()
    k = int(toks[0])
    nl = list(lab)
    seen = set()
    for i in range(k):
        v = int(toks[1 + 2 * i])
        s = toks[2 + 2 * i]
        assert 1 <= v <= n and kind[v] in 'GTE', "vertex %d is not a leaf" % v
        assert 1 <= len(s) <= 5 and s.isalpha() and s.islower()
        assert v not in seen
        seen.add(v)
        nl[v] = s
    new = owners(n, par, kind, nl, big, depth, sub, True)
    assert new is not None, "the new labelling breaks one of the rules"
    assert new == base, "a berry changed owner"
    return sum(1 for v in range(1, n + 1) if nl[v] != lab[v])


def brute(text, fresh=3):
    """smallest number of changed labels, by exhaustive search"""
    n, par, kind, lab = parse(text)
    big, depth, sub = build(n, par, kind)
    leaves = [v for v in range(1, n + 1) if kind[v] in 'GTE']
    base = owners(n, par, kind, lab, big, depth, sub, False)
    assert base is not None, "the instance breaks the stated guarantees"
    pool = sorted(set(lab[v] for v in leaves))
    pool += [c for c in "zyxwvu" if c not in pool][:min(len(leaves), fresh)]
    best = None
    for assign in itertools.product(pool, repeat=len(leaves)):
        nl = list(lab)
        for v, s in zip(leaves, assign):
            nl[v] = s
        o = owners(n, par, kind, nl, big, depth, sub, True)
        if o is None or o != base:
            continue
        c = sum(1 for v in leaves if nl[v] != lab[v])
        if best is None or c < best:
            best = c
    return best


# --------------------------------------------------------------- driver
def gen(rng, maxn, maxleaf, alpha):
    n = rng.randint(4, maxn)
    par = [0, 0]
    for i in range(2, n + 1):
        par.append(rng.randint(max(1, i - 3), i - 1))
    ch = [[] for _ in range(n + 1)]
    for i in range(2, n + 1):
        ch[par[i]].append(i)
    leaves = [v for v in range(1, n + 1) if not ch[v]]
    if not leaves or len(leaves) > maxleaf:
        return None
    kind = [''] * (n + 1)
    lab = [''] * (n + 1)
    for v in range(1, n + 1):
        if ch[v]:
            kind[v] = 'B' if v == 1 else rng.choice('BSSS')
        else:
            kind[v] = rng.choice('GTTTEEE')
            lab[v] = rng.choice(alpha)
    if not any(kind[v] in 'GT' for v in leaves):
        return None
    if not any(kind[v] == 'E' for v in leaves):
        return None
    big, depth, sub = build(n, par, kind)
    if owners(n, par, kind, lab, big, depth, sub, False) is None:
        return None            # the random instance breaks a stated guarantee
    lines = [str(n)]
    for i in range(1, n + 1):
        lines.append("%d %s" % (par[i], kind[i]) if kind[i] in 'BS'
                     else "%d %s %s" % (par[i], kind[i], lab[i]))
    return "\n".join(lines)


SAMPLES = [
    ("""13
0 B
1 B
2 E a
2 E b
2 S
5 G a
5 T a
5 E a
5 E b
1 S
10 E a
10 G b
1 T a""", 2),
    ("""6
0 B
1 B
1 T a
2 E a
2 S
5 T a""", 1),
    ("""6
0 B
1 G y
1 E y
1 E z
1 T z
1 E z""", 0),
]


def main():
    t0 = time.time()
    for i, (txt, exp) in enumerate(SAMPLES, 1):
        out = solve(txt)
        k = int(out.split("\n")[0])
        assert k == exp, ("sample %d: got %d, expected %d" % (i, k, exp))
        assert validate(txt, out) == k
        print("sample %d: k = %d, replayed labelling keeps every owner  %s"
              % (i, k, out.replace("\n", " | ")))

    total = nz = 0
    for seed, cfg in ((1, (11, 5, "abc")), (7, (11, 5, "abc")),
                      (99, (11, 5, "abc")), (5, (13, 6, "ab"))):
        rng = random.Random(seed)
        done = 0
        while done < 180:
            t = gen(rng, *cfg)
            if t is None:
                continue
            done += 1
            total += 1
            out = solve(t)
            k = int(out.split("\n")[0])
            assert validate(t, out) == k, t
            b = brute(t)
            assert b == k, ("NOT OPTIMAL\n%s\nours %d brute %d\n%s"
                            % (t, k, b, out))
            nz += 1 if k else 0
    print("%d random trees: every answer optimal (exhaustive search over all "
          "labellings) and valid; %d of them needed a change" % (total, nz))

    # scale
    rng = random.Random(3)
    n = 150000
    par = [0, 0, 1]
    for i in range(3, n + 1):
        p = rng.randint(max(1, i - 4), i - 1)
        par.append(1 if p == 2 else p)
    ch = [[] for _ in range(n + 1)]
    for i in range(2, n + 1):
        ch[par[i]].append(i)
    pool = [''.join(t) for t in itertools.product(
        [chr(c) for c in range(97, 123)], repeat=4)]
    rng.shuffle(pool)
    pool = [p for p in pool if p != 'aaaa']
    lines = ['0 B', '1 G aaaa']
    for i in range(3, n + 1):
        if ch[i]:
            lines.append('%d %s' % (par[i], rng.choice('BS')))
        elif rng.random() < 0.5:
            lines.append('%d E aaaa' % par[i])
        else:
            lines.append('%d %s %s' % (par[i], rng.choice('GT'), pool.pop()))
    text = "\n".join([str(n)] + lines)
    t1 = time.time()
    out = solve(text)
    print("n = 150000: solved in %.2fs (python), k = %s"
          % (time.time() - t1, out.split("\n")[0]))
    print("total %.1fs" % (time.time() - t0))
    print("PASS")


main()
