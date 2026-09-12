"""
kattis-jetlag  (ICPC World Finals 2023, "Jet Lag") -- verification.

Model
-----
Activities [b_i, e_i], b_i < e_i, e_i <= b_{i+1}.  You must be awake during every
activity.  A sleep of length k starting at s and ending at t = s+k is followed by
k minutes "rested" (cannot fall asleep) and then k minutes "functioning" (may fall
asleep).  So after a sleep [s,t] the NEXT sleep must start at some
    s' in [t+k, t+2k] = [2t-s, 3t-2s]      (both endpoints inclusive)
and if there is no next sleep, you must survive to the end:  3t-2s >= e_n.
The first sleep starts at exactly 0; no sleep may overlap an activity, so every
sleep lies inside one "gap" [e_j, b_{j+1}] (or [0, b_1]); last sleep ends <= b_n.

Derived greedy (O(n), scan gaps right to left):
  * target S (initially e_n, with the last sleep exempt from the upper "rested" bound)
  * a gap [L,R] can serve target S iff  L+2 <= S <= 3R-2L   (and R <= S)
  * when it can, it can do so with s = L (the gap's left end), t = L+ceil((S-L)/3);
    the new target becomes L.  Taking s = L (smallest possible new target) and the
    RIGHTMOST usable gap both dominate.
  * success iff the scan eventually uses gap [0, b_1] (giving s_1 = 0).
"""
import random
import sys
from functools import lru_cache


# ---------------------------------------------------------------- utilities
def gaps_of(acts):
    g = []
    if acts[0][0] > 0:
        g.append((0, acts[0][0]))
    for i in range(len(acts) - 1):
        L, R = acts[i][1], acts[i + 1][0]
        if L < R:
            g.append((L, R))
    return g


def validate(acts, sleeps):
    """Independent checker of a proposed schedule."""
    E = acts[-1][1]
    bn = acts[-1][0]
    if not sleeps:
        return False
    if sleeps[0][0] != 0:
        return False
    if sleeps[-1][1] > bn:
        return False
    gs = gaps_of(acts)
    prev = None
    for (s, t) in sleeps:
        if not (s < t):
            return False
        if prev is not None:
            ps, pt = prev
            if not (pt < s):
                return False
            if not (2 * pt - ps <= s <= 3 * pt - 2 * ps):
                return False
        if not any(L <= s and t <= R for (L, R) in gs):
            return False
        prev = (s, t)
    s, t = sleeps[-1]
    return 3 * t - 2 * s >= E


# ---------------------------------------------------------------- brute force
def brute(acts):
    """Exhaustive search over all schedules.  Returns a schedule or None."""
    E = acts[-1][1]
    gs = gaps_of(acts)
    if not gs:
        return None

    starts = {}          # s -> list of t
    for (L, R) in gs:
        for s in range(L, R):
            starts[s] = [t for t in range(s + 1, R + 1)]

    sys.setrecursionlimit(10000)
    seen = set()

    def rec(s, t):
        if 3 * t - 2 * s >= E:
            return [(s, t)]
        if (s, t) in seen:
            return None
        seen.add((s, t))
        lo, hi = 2 * t - s, 3 * t - 2 * s
        for s2 in range(lo, hi + 1):
            if s2 in starts:
                for t2 in starts[s2]:
                    r = rec(s2, t2)
                    if r is not None:
                        return [(s, t)] + r
        return None

    if 0 not in starts:
        return None
    for t in starts[0]:
        r = rec(0, t)
        if r is not None:
            return r
    return None


# ---------------------------------------------------------------- greedy
def ceil_div(a, b):
    return -((-a) // b)


def greedy(acts):
    E = acts[-1][1]
    gs = gaps_of(acts)
    out = []
    S = E
    for (L, R) in reversed(gs):
        if not out:                              # the final sleep
            if 3 * R - 2 * L >= E:
                t = max(L + 1, ceil_div(E + 2 * L, 3))
                assert t <= R
                out.append((L, t))
                S = L
        else:                                    # an intermediate sleep
            if R <= S and L + 2 <= S <= 3 * R - 2 * L:
                t = L + ceil_div(S - L, 3)
                assert L < t <= min(R, S - 1), (L, R, S, t)
                out.append((L, t))
                S = L
        if S == 0 and out:
            break
    if not out or S != 0:
        return None
    return list(reversed(out))


# ---------------------------------------------------------------- tests
def samples():
    S = [
        ([(30, 45), (60, 90), (120, 180)], True),
        ([(0, 60)], False),
        ([(31, 32), (35, 41), (48, 55), (69, 91),
          (1000, 2022), (2022, 2023), (2994, 4096)], True),
    ]
    for acts, feasible in S:
        g = greedy(acts)
        assert (g is not None) == feasible, (acts, g)
        if g:
            assert validate(acts, g), (acts, g)
        print("sample ok:", acts[:2], "->", g)


def rand_acts(rng, maxt, maxn):
    n = rng.randint(1, maxn)
    pts = sorted(rng.sample(range(0, maxt), min(2 * n, maxt)))
    acts = []
    for i in range(0, len(pts) - 1, 2):
        acts.append((pts[i], pts[i + 1]))
    if not acts:
        return None
    return acts


def stress(iters=4000, maxt=26, maxn=4, seed=1):
    rng = random.Random(seed)
    tested = feas = 0
    for _ in range(iters):
        acts = rand_acts(rng, maxt, maxn)
        if acts is None:
            continue
        b = brute(acts)
        g = greedy(acts)
        tested += 1
        if (b is not None) != (g is not None):
            print("MISMATCH on", acts, "brute:", b, "greedy:", g)
            return False
        if g is not None:
            feas += 1
            if not validate(acts, g):
                print("INVALID greedy schedule", acts, g)
                return False
        if b is not None and not validate(acts, b):
            print("brute produced invalid schedule?!", acts, b)
            return False
    print(f"stress ok: {tested} cases, {feas} feasible")
    return True


def stress_dense(iters=3000, maxt=18, seed=7):
    """Many short activities packed together -> lots of tiny gaps, edge cases."""
    rng = random.Random(seed)
    tested = feas = 0
    for _ in range(iters):
        acts = []
        cur = rng.randint(0, 2)
        while cur < maxt:
            b = cur + rng.randint(0, 3)
            e = b + rng.randint(1, 3)
            if e > maxt:
                break
            acts.append((b, e))
            cur = e
        if not acts:
            continue
        b = brute(acts)
        g = greedy(acts)
        tested += 1
        if (b is not None) != (g is not None):
            print("MISMATCH on", acts, "brute:", b, "greedy:", g)
            return False
        if g is not None:
            feas += 1
            if not validate(acts, g):
                print("INVALID greedy schedule", acts, g)
                return False
    print(f"dense stress ok: {tested} cases, {feas} feasible")
    return True


if __name__ == "__main__":
    samples()
    ok = stress() and stress_dense()
    print("ALL OK" if ok else "FAILED")
