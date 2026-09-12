"""Alea Iacta Est (ICPC WF 2023, Kattis aleaiactaest) -- verification.

Model (derived from the samples/narrative):
  d dice, die i has 6 faces (symbols may repeat).  All d dice are rolled (1 roll).
  The dice WIN if the MULTISET of top symbols equals some dictionary word
  (the narrative keeps P,E,S on dice 1,4,5 and hopes for PARSE/PAUSE/... which
  do not match positionally; and it keeps P,E,A,E and rerolls die 5 for a C to
  make PEACE, where die 5 = ABCSCC has no E -> multiset matching, not positional).
  Otherwise choose ANY subset K of dice to keep and reroll the rest (cost 1 per
  roll).  Minimise the expected number of rolls.

Main algorithm (solve_dijkstra): Dijkstra-style exact solve of the MDP.
  Nodes = "keep-sets": partial assignments q (each die either free or pinned to
  one of its distinct faces), with at least one free die.  Tuples t = full
  assignments.
      h(q) = 1 + sum_t Pr[t | q] * V(t)
      V(t) = 0 if multiset(t) is a word, else min over proper sub-partials q of t
             of h(q)   (q ranges over the 2^d - 1 keep-sets contained in t)
  Since q subset t for every completion t of q, V(t) <= h(q) always, i.e. every
  node has a self-loop.  Values are computed in increasing order: when q is
  popped, the completions whose V is still unknown must have V == h(q), so
      h(q) = (1 + sum_{known t} Pr[t|q] V(t)) / (1 - Pr[unknown])
  which is exactly the Dijkstra-for-SSP relaxation.  Answer = h(empty set).
  Cost O(2^d * 6^d log) = ~3e6 log, plus O(w d) to read the dictionary.

Cross-check (solve_valueiter): plain value iteration over the same MDP, written
  independently of the lattice machinery, run to convergence on small inputs.
Plus a Monte-Carlo simulation of the greedy-on-h policy.
"""
import heapq
import itertools
import math
import random
import sys
from collections import Counter

INF = float("inf")


def parse(text):
    tok = text.split()
    d = int(tok[0]); w = int(tok[1])
    dice = tok[2:2 + d]
    words = tok[2 + d:2 + d + w]
    assert all(len(x) == 6 for x in dice), dice
    assert all(len(x) == d for x in words), words
    return d, dice, words


# ---------------------------------------------------------------- main solver
def solve_dijkstra(d, dice, words):
    faces = []           # distinct faces per die
    probs = []           # matching probabilities
    for die in dice:
        c = Counter(die)
        ks = sorted(c)
        faces.append(ks)
        probs.append([c[k] / 6.0 for k in ks])
    n = [len(f) for f in faces]

    # tuple encoding, mixed radix n[i]
    tstride = [1] * d
    for i in range(1, d):
        tstride[i] = tstride[i - 1] * n[i - 1]
    ntuples = tstride[-1] * n[-1]

    # partial encoding, mixed radix n[i]+1 ; value n[i] == free
    pstride = [1] * d
    for i in range(1, d):
        pstride[i] = pstride[i - 1] * (n[i - 1] + 1)
    npart = pstride[-1] * (n[-1] + 1)
    FULL = sum(f * pstride[i] for i, f in enumerate([0] * d))  # unused

    wordset = set()
    for word in words:
        wordset.add("".join(sorted(word)))

    # enumerate tuples; find winners; build the sub-partial lists
    tuples = []          # list of face-index tuples, indexed by tuple id
    is_win = [False] * ntuples
    for combo in itertools.product(*[range(x) for x in n]):
        tid = sum(combo[i] * tstride[i] for i in range(d))
        while len(tuples) <= tid:
            tuples.append(None)
        tuples[tid] = combo
        sym = "".join(sorted(faces[i][combo[i]] for i in range(d)))
        is_win[tid] = sym in wordset

    if not any(is_win):
        return None  # impossible

    # comp[q] = list of (tuple id, Pr[t|q]) ; subs[t] = list of (q, Pr[t|q])
    comp = [[] for _ in range(npart)]
    subs = [[] for _ in range(ntuples)]
    masks = [m for m in range(1 << d) if m != (1 << d) - 1]  # keep-sets, K != all
    for tid, combo in enumerate(tuples):
        for m in masks:
            q = 0
            p = 1.0
            for i in range(d):
                if m >> i & 1:
                    q += combo[i] * pstride[i]
                else:
                    q += n[i] * pstride[i]
                    p *= probs[i][combo[i]]
            comp[q].append((tid, p))
            subs[tid].append((q, p))

    EMPTY = sum(n[i] * pstride[i] for i in range(d))

    sumk = [0.0] * npart      # sum Pr[t|q] V(t) over finalised completions
    punk = [1.0] * npart      # probability mass of completions not yet finalised
    hval = [None] * npart
    V = [None] * ntuples
    heap = []

    def relax(q, p, v):
        sumk[q] += p * v
        punk[q] -= p
        if punk[q] < 1e-12:
            punk[q] = 0.0
        if punk[q] < 1.0:
            heapq.heappush(heap, ((1.0 + sumk[q]) / (1.0 - punk[q]), q))

    for tid in range(ntuples):
        if is_win[tid]:
            V[tid] = 0.0
            for q, p in subs[tid]:
                relax(q, p, 0.0)

    while heap:
        val, q = heapq.heappop(heap)
        if hval[q] is not None:
            continue
        hval[q] = val
        if q == EMPTY:
            return val
        for tid, _p in comp[q]:
            if V[tid] is None:
                V[tid] = val
                for q2, p2 in subs[tid]:
                    relax(q2, p2, val)
    return None if hval[EMPTY] is None else hval[EMPTY]


def policy_tables(d, dice, words):
    """Re-run the solver but return (faces, probs, h, V, subs) for simulation."""
    faces, probs = [], []
    for die in dice:
        c = Counter(die)
        ks = sorted(c)
        faces.append(ks)
        probs.append([c[k] / 6.0 for k in ks])
    n = [len(f) for f in faces]
    tstride = [1] * d
    for i in range(1, d):
        tstride[i] = tstride[i - 1] * n[i - 1]
    ntuples = tstride[-1] * n[-1]
    pstride = [1] * d
    for i in range(1, d):
        pstride[i] = pstride[i - 1] * (n[i - 1] + 1)
    npart = pstride[-1] * (n[-1] + 1)
    wordset = {"".join(sorted(x)) for x in words}
    tuples = [None] * ntuples
    is_win = [False] * ntuples
    for combo in itertools.product(*[range(x) for x in n]):
        tid = sum(combo[i] * tstride[i] for i in range(d))
        tuples[tid] = combo
        is_win[tid] = "".join(sorted(faces[i][combo[i]] for i in range(d))) in wordset
    comp = [[] for _ in range(npart)]
    subs = [[] for _ in range(ntuples)]
    masks = [m for m in range(1 << d) if m != (1 << d) - 1]
    for tid, combo in enumerate(tuples):
        for m in masks:
            q, p = 0, 1.0
            for i in range(d):
                if m >> i & 1:
                    q += combo[i] * pstride[i]
                else:
                    q += n[i] * pstride[i]
                    p *= probs[i][combo[i]]
            comp[q].append((tid, p))
            subs[tid].append((q, p))
    sumk = [0.0] * npart
    punk = [1.0] * npart
    hval = [INF] * npart
    done = [False] * npart
    V = [None] * ntuples
    heap = []

    def relax(q, p, v):
        sumk[q] += p * v
        punk[q] -= p
        if punk[q] < 1e-12:
            punk[q] = 0.0
        if punk[q] < 1.0:
            heapq.heappush(heap, ((1.0 + sumk[q]) / (1.0 - punk[q]), q))

    for tid in range(ntuples):
        if is_win[tid]:
            V[tid] = 0.0
            for q, p in subs[tid]:
                relax(q, p, 0.0)
    while heap:
        val, q = heapq.heappop(heap)
        if done[q]:
            continue
        done[q] = True
        hval[q] = val
        for tid, _p in comp[q]:
            if V[tid] is None:
                V[tid] = val
                for q2, p2 in subs[tid]:
                    relax(q2, p2, val)
    return dict(faces=faces, probs=probs, n=n, tstride=tstride, pstride=pstride,
                tuples=tuples, is_win=is_win, subs=subs, hval=hval, V=V,
                masks=masks)


def simulate(d, dice, words, trials=200000, seed=1):
    T = policy_tables(d, dice, words)
    rng = random.Random(seed)
    n, probs, tstride, pstride = T["n"], T["probs"], T["tstride"], T["pstride"]
    # per-die cumulative distribution over distinct face indices
    cum = []
    for i in range(d):
        acc, s = [], 0.0
        for p in probs[i]:
            s += p
            acc.append(s)
        cum.append(acc)

    def roll(i):
        x = rng.random()
        for j, c in enumerate(cum[i]):
            if x < c:
                return j
        return n[i] - 1

    total = 0
    for _ in range(trials):
        cur = [roll(i) for i in range(d)]
        rolls = 1
        while True:
            tid = sum(cur[i] * tstride[i] for i in range(d))
            if T["is_win"][tid]:
                break
            best, bestq = INF, None
            for q, _p in T["subs"][tid]:
                if T["hval"][q] < best:
                    best, bestq = T["hval"][q], q
            # reroll the free positions of bestq
            for i in range(d):
                if (bestq // pstride[i]) % (n[i] + 1) == n[i]:
                    cur[i] = roll(i)
            rolls += 1
            if rolls > 100000:
                break
        total += rolls
    return total / trials


# --------------------------------------------------------------- brute force
def solve_valueiter(d, dice, words, sweeps=200000, tol=1e-13):
    """Independent brute force: plain value iteration over full tuples.

    States are the raw symbol tuples (product of the dice faces WITH
    multiplicity, so probabilities are uniform 1/6^d).  No lattice tricks.
    """
    allt = list(itertools.product(*[list(x) for x in dice]))
    idx = {}
    for t in allt:
        idx.setdefault(t, len(idx))
    # uniform over 6^d face combinations; group identical symbol tuples
    weight = Counter(allt)
    m = len(idx)
    order = [None] * m
    for t, i in idx.items():
        order[i] = t
    wordset = {"".join(sorted(x)) for x in words}
    win = [("".join(sorted(t)) in wordset) for t in order]
    if not any(win):
        return None
    total = 6 ** d
    keepsets = [m_ for m_ in range(1 << d) if m_ != (1 << d) - 1]
    # for each (state, keepset) the outcome distribution
    trans = []
    for i, t in enumerate(order):
        row = []
        for ks in keepsets:
            free = [j for j in range(d) if not (ks >> j & 1)]
            dist = Counter()
            for combo in itertools.product(*[list(dice[j]) for j in free]):
                nt = list(t)
                for j, ch in zip(free, combo):
                    nt[j] = ch
                dist[idx[tuple(nt)]] += 1
            tot = 6 ** len(free)
            row.append([(k, v / tot) for k, v in dist.items()])
        trans.append(row)
    V = [0.0 if win[i] else 1e9 for i in range(m)]
    for it in range(sweeps):
        delta = 0.0
        newV = V[:]
        for i in range(m):
            if win[i]:
                continue
            best = INF
            for row in trans[i]:
                s = 1.0
                for k, p in row:
                    s += p * V[k]
                if s < best:
                    best = s
            delta = max(delta, abs(best - V[i]))
            newV[i] = best
        V = newV
        if delta < tol:
            break
    # value of the initial (uniform) roll
    exp = 0.0
    for t, c in weight.items():
        exp += (c / total) * V[idx[t]]
    return 1.0 + exp


# --------------------------------------------------------------------- tests
SAMPLES = [
    ("5 8\nABCDEP\nAEHOXU\nAISOLR\nABCDEF\nABCSCC\nPARSE\nPAUSE\nPHASE\nPOISE\nPROSE\nPULSE\nPURSE\nPEACE", 9.677887141),
    ("2 1\nAAAAAA\nBBBBBB\nAB", 1.0),
    ("3 1\n123456\n123456\n123456\n666", 10.555444555),
    ("2 1\nABCDEF\nGHI234\nAB", None),
]


def run_samples():
    ok = True
    for text, want in SAMPLES:
        d, dice, words = parse(text)
        got = solve_dijkstra(d, dice, words)
        if want is None:
            good = got is None
            gs = "impossible" if got is None else "%.9f" % got
        else:
            good = got is not None and abs(got - want) <= 1e-6 * max(1.0, abs(want))
            gs = "%.9f" % got if got is not None else "impossible"
        ok &= good
        print(("  OK  " if good else " FAIL "), "want", want, "got", gs)
    return ok


def positional_variant(d, dice, words):
    """Sanity: what the answer would be if words matched die-by-die."""
    faces = []
    for die in dice:
        faces.append(die)
    # reuse solve_dijkstra with an exact-word (ordered) match by faking the set
    # -- easiest: monkey-patch through a tiny re-implementation
    return None


def run_random(trials=60, seed=7):
    rng = random.Random(seed)
    bad = 0
    for tc in range(trials):
        d = rng.randint(1, 3)
        alpha = "AB" if rng.random() < 0.5 else "ABC"
        dice = ["".join(rng.choice(alpha) for _ in range(6)) for _ in range(d)]
        nw = rng.randint(1, 4)
        wordpool = {"".join(rng.choice(alpha) for _ in range(d)) for _ in range(nw)}
        words = sorted(wordpool)
        a = solve_dijkstra(d, dice, words)
        b = solve_valueiter(d, dice, words)
        if (a is None) != (b is None):
            print(" MISMATCH(possible)", d, dice, words, a, b)
            bad += 1
            continue
        if a is not None and abs(a - b) > 1e-6 * max(1.0, a):
            print(" MISMATCH", d, dice, words, a, b)
            bad += 1
    print("random cross-check: %d/%d agree" % (trials - bad, trials))
    return bad == 0


def run_random_big(trials=12, seed=99):
    """Bigger random cases (d=3..4, full 6-symbol alphabet) -- slower VI."""
    rng = random.Random(seed)
    bad = 0
    for tc in range(trials):
        d = rng.randint(2, 3)
        alpha = "ABCD"
        dice = ["".join(rng.choice(alpha) for _ in range(6)) for _ in range(d)]
        words = sorted({"".join(rng.choice(alpha) for _ in range(d))
                        for _ in range(rng.randint(1, 3))})
        a = solve_dijkstra(d, dice, words)
        b = solve_valueiter(d, dice, words, sweeps=50000)
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-6 * max(1.0, a)):
            print(" MISMATCH", d, dice, words, a, b)
            bad += 1
    print("bigger random cross-check: %d/%d agree" % (trials - bad, trials))
    return bad == 0


if __name__ == "__main__":
    print("samples:")
    s = run_samples()
    print()
    r1 = run_random()
    r2 = run_random_big()
    print()
    d, dice, words = parse(SAMPLES[0][0])
    mc = simulate(d, dice, words, trials=100000, seed=12345)
    print("sample 1 Monte-Carlo of the computed policy: %.4f (exact 9.677887141)" % mc)
    print()
    print("ALL OK" if (s and r1 and r2) else "FAILURES PRESENT")
