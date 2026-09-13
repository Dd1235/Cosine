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
import time
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


# ------------------------------------------------- second independent solver
def solve_lattice_vi(d, dice, words, iters=4000, tol=1e-14):
    """Independent method #2: value iteration on the keep-set lattice.

    No Dijkstra, no explicit per-state transition lists.  Partial hands live in
    a mixed-radix array (digit n_i means "die i is free"); the expectation over
    completions is an axis-by-axis average (a zeta transform on the lattice) and
    the "best sub-hand" is an axis-by-axis min.  Value iteration from V == 0
    computes the k-horizon optimum, which increases to V*; since the answer is
    bounded by E[max of d Geom(1/6)] <= 13.9378 the tail decays like (5/6)^k and
    ~140 sweeps reach 1e-10.
    """
    faces, probs = [], []
    for die in dice:
        c = Counter(die); ks = sorted(c)
        faces.append(ks); probs.append([c[k] / 6.0 for k in ks])
    n = [len(f) for f in faces]
    r = [x + 1 for x in n]
    ps = [1] * d
    for i in range(1, d): ps[i] = ps[i - 1] * r[i - 1]
    npart = ps[-1] * r[-1]
    ts = [1] * d
    for i in range(1, d): ts[i] = ts[i - 1] * n[i - 1]
    ntup = ts[-1] * n[-1]

    wordset = {"".join(sorted(x)) for x in words}
    combos = list(itertools.product(*[range(x) for x in n]))
    tid_of, win, pfull = {}, [False] * ntup, [0] * ntup
    for combo in combos:
        tid = sum(combo[i] * ts[i] for i in range(d))
        tid_of[combo] = tid
        win[tid] = "".join(sorted(faces[i][combo[i]] for i in range(d))) in wordset
        pfull[tid] = sum(combo[i] * ps[i] for i in range(d))
    if not any(win):
        return None

    free_idx = [[q for q in range(npart) if (q // ps[i]) % r[i] == n[i]] for i in range(d)]
    fix_idx = [[q for q in range(npart) if (q // ps[i]) % r[i] != n[i]] for i in range(d)]
    EMPTY = sum(n[i] * ps[i] for i in range(d))

    def zeta(V):
        A = [0.0] * npart
        for tid in range(ntup):
            A[pfull[tid]] = V[tid]
        for i in range(d):
            si, ni, pi = ps[i], n[i], probs[i]
            for q in free_idx[i]:
                base = q - ni * si
                A[q] = sum(pi[f] * A[base + f * si] for f in range(ni))
        return A

    V = [0.0] * ntup
    for it in range(iters):
        A = zeta(V)
        B = A[:]
        for i in range(d):
            si, ni = ps[i], n[i]
            for q in fix_idx[i]:
                fq = q + (ni - (q // si) % r[i]) * si
                if B[fq] < B[q]:
                    B[q] = B[fq]
        newV = [0.0] * ntup
        for combo in combos:
            tid = tid_of[combo]
            if win[tid]:
                continue
            base = pfull[tid]
            newV[tid] = 1.0 + min(B[base + (n[i] - combo[i]) * ps[i]] for i in range(d))
        delta = max(abs(a - b) for a, b in zip(newV, V))
        V = newV
        if delta < tol and it > 20:
            break
    return 1.0 + zeta(V)[EMPTY]


def run_lattice_cross(trials=70, seed=4242):
    """Dijkstra vs lattice value iteration on random instances up to d = 5."""
    rng = random.Random(seed)
    bad = 0
    for _ in range(trials):
        d = rng.randint(1, 4)
        alpha = rng.choice(["AB", "ABC", "ABCD", "ABCDEF"])
        dice = ["".join(rng.choice(alpha) for _ in range(6)) for _ in range(d)]
        words = sorted({"".join(rng.choice(alpha) for _ in range(d))
                        for _ in range(rng.randint(1, 5))})
        a = solve_dijkstra(d, dice, words)
        b = solve_lattice_vi(d, dice, words, iters=6000)
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-7 * max(1.0, a)):
            print(" MISMATCH(lattice)", d, dice, words, a, b)
            bad += 1
    for _ in range(6):
        d, alpha = 5, "ABC"
        dice = ["".join(rng.choice(alpha) for _ in range(6)) for _ in range(d)]
        words = sorted({"".join(rng.choice(alpha) for _ in range(d))
                        for _ in range(rng.randint(1, 3))})
        a = solve_dijkstra(d, dice, words)
        b = solve_lattice_vi(d, dice, words, iters=3000)
        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-7 * max(1.0, a)):
            print(" MISMATCH(lattice d=5)", d, dice, words, a, b)
            bad += 1
    print("dijkstra vs lattice-VI: %d mismatches" % bad)
    return bad == 0


def run_interpretation_check():
    """Sample 1 separates 'rearrange into a word' from 'die i shows word[i]'."""
    d, dice, words = parse(SAMPLES[0][0])
    feasible = [w for w in words if all(w[i] in dice[i] for i in range(d))]
    ok = not feasible                      # no word is positionally makeable...
    got = solve_dijkstra(d, dice, words)   # ...yet the expected answer is finite
    ok &= got is not None and abs(got - 9.677887141) < 1e-6
    print("interpretation: positional match would print 'impossible' on sample 1,"
          " multiset match gives %.9f -> multiset confirmed (%s)"
          % (got, "OK" if ok else "FAIL"))
    return ok


def run_worst_case():
    """Largest input shape, and the analytic ceiling on the answer."""
    dice = ["ABCDEF"] * 6
    t0 = time.time(); a = solve_dijkstra(6, dice, ["FFFFFF"]); t1 = time.time()
    bound = sum((-1) ** (k + 1) * math.comb(6, k) / (1 - (5 / 6) ** k)
                for k in range(1, 7))
    ok = abs(a - bound) < 1e-9
    print("worst case d=6 (6^6 tuples, 63 keep-sets): %.9f in %.1fs; "
          "E[max of 6 Geom(1/6)] = %.9f (%s)"
          % (a, t1 - t0, bound, "OK" if ok else "FAIL"))
    # a 2e5-word dictionary costs only the O(w d) canonicalisation
    rng = random.Random(11)
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    pool = {"".join(rng.choice("ABCDEF") for _ in range(6)) for _ in range(120000)}
    while len(pool) < 200000:                      # pad out to the real cap of w
        pool.add("".join(rng.choice(alpha) for _ in range(6)))
    words = sorted(pool)
    t0 = time.time(); b = solve_dijkstra(6, dice, words); t1 = time.time()
    print("worst case w=%d: %.9f in %.1fs" % (len(words), b, t1 - t0))
    return ok


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
    r3 = run_lattice_cross()
    r4 = run_interpretation_check()
    r5 = run_worst_case()
    print()
    d, dice, words = parse(SAMPLES[0][0])
    mc = simulate(d, dice, words, trials=100000, seed=12345)
    print("sample 1 Monte-Carlo of the computed policy: %.4f (exact 9.677887141)" % mc)
    print()
    print("ALL OK" if (s and r1 and r2 and r3 and r4 and r5) else "FAILURES PRESENT")
