"""
Kattis "maxwellsdemon" (ICPC WF 2024) -- derivation check.

MODEL
-----
Chambers: left [-w,0]x[0,h], right [0,w]x[0,h].  A particle's y-motion is a
triangle wave of period 2h, totally independent of everything else.  Its
x-motion inside a chamber is a triangle wave of period 2w, and -- crucially --
whether the demon lets it through or not, the particle arrives back at the
centre wall x=0 exactly every 2w/|vx|.  So the set

    S_i = { t >= 0 : particle i is at (0,d) }

does NOT depend on any of the demon's decisions.  (Unfolded view: let X_i(t)
be the free trajectory in [-w,w] reflecting only at +-w; the real abscissa is
sigma*X_i(t) with sigma flipping on every *reflection* off the centre wall.
Zeros of X_i are the wall arrivals.)

Consequently a particle changes chamber exactly once per demon passage, so it
only needs the right PARITY of passages:
    eps_i = 1 if particle i starts in the wrong chamber else 0.
The demon picks a set D of times; at t in D every particle with t in S_i
passes (all-or-none).  So over GF(2):
    sum_{t in D} chi(t) = eps ,   chi(t)_i = [t in S_i],
and the answer is min max(D).

S_i: wall arrivals t=(2wk-px)/vx; y-hit needs py+vy*t = +-d (mod 2h).  That is
a linear congruence in k, so S_i is <=2 arithmetic progressions of common
period  Pi_i = 4wh/g_i,  g_i = gcd(2w|vy|, 2h|vx|).
All Pi_i share the numerator 4wh, hence lcm_i(Pi_i) = 4wh/gcd_i(g_i) =: P.
P <= 4wh <= 160000, and the whole event pattern is P-periodic, so span of the
events in [0,P) is the full span: the answer (if finite) is < P.

ALGORITHM: enumerate the events in [0,P), group equal times, insert the group
vectors into a GF(2) basis in time order, output the first time eps lies in
the span.  Complexity: O(E * n^2/64) with E = sum_i 2*g_i/gcd(g) events.
"""
import sys, random
from fractions import Fraction
from fractions import Fraction as F
from math import gcd


# ---------------------------------------------------------------- geometry --
def fold(z, period, top):
    """triangle-fold z into [0,top] with 2*top == period"""
    z = z % period
    return z if z <= top else period - z


def first_wall_hit(px, vx, w):
    """smallest t>0 with the particle at x=0 (|px|<w, px!=0, vx!=0)"""
    if vx > 0:
        z = 0 if px < 0 else 2 * w          # next multiple of 2w above px
    else:
        z = 0 if px > 0 else -2 * w         # next multiple of 2w below px
    return Fraction(z - px, vx)


# ------------------------------------------------- event set of a particle --
def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x, y = egcd(b, a % b)
    return (g, y, x - (a // b) * y)


def event_ap(px, py, vx, vy, w, h, d):
    """
    return (period, [first times]) : S = union over the returned first times t0
    of { t0 + j*period : j>=0 }.  period is None when S is empty.
    """
    if vx == 0:
        return None, []                      # never reaches the centre wall
    g = gcd(2 * w * abs(vy), 2 * h * abs(vx))
    period = Fraction(4 * w * h, g)
    a = 2 * w * vy
    m = 2 * h * abs(vx)
    outs = set()
    for sgn in (1, -1):
        c = vx * (sgn * d - py) + vy * px
        gg = gcd(abs(a), m) if a else m
        if c % gg:
            continue
        if a == 0:                            # vy == 0 : y is constant = py
            if py != d:
                continue
            k0 = 0                            # every wall hit works
        else:
            aa, mm, cc = a // gg, m // gg, c // gg
            _, inv, _ = egcd(aa % mm, mm)
            k0 = (cc * inv) % mm
        t = Fraction(2 * w * k0 - px, vx)
        outs.add(t % period)
    return period, sorted(outs)


def brute_events(px, py, vx, vy, w, h, d, tmax):
    """independent event list: step wall-hit by wall-hit, fold y directly."""
    if vx == 0:
        return []
    t = first_wall_hit(px, vx, w)
    step = Fraction(2 * w, abs(vx))
    out = []
    while t <= tmax:
        if fold(py + vy * t, 2 * h, h) == d:
            out.append(t)
        t += step
    return out


# ------------------------------------------------------------------ solver --
def collect(parts, w, h, d, horizon=None):
    """-> (P, {time: bitmask})"""
    G = 0
    aps = []
    for (px, py, vx, vy) in parts:
        per, firsts = event_ap(px, py, vx, vy, w, h, d)
        aps.append((per, firsts))
        if firsts:
            G = gcd(G, 4 * w * h // per.numerator * per.denominator) if False else G
    # recompute G honestly: per = 4wh/g  =>  g = 4wh/per
    G = 0
    for per, firsts in aps:
        if firsts:
            g = Fraction(4 * w * h) / per
            assert g.denominator == 1
            G = gcd(G, int(g))
    if G == 0:
        return Fraction(0), {}
    P = Fraction(4 * w * h, G)
    lim = P if horizon is None else horizon
    ev = {}
    for i, (per, firsts) in enumerate(aps):
        for t0 in firsts:
            t = t0
            while t < lim:
                if t > 0:
                    ev[t] = ev.get(t, 0) | (1 << i)
                t += per
    return P, ev


def solve(w, h, d, r, b, parts):
    eps = 0
    for i, (px, py, vx, vy) in enumerate(parts):
        want_left = (i < r)                      # first r are red -> left
        in_left = px < 0
        if want_left != in_left:
            eps |= 1 << i
    if eps == 0:
        return Fraction(0)
    P, ev = collect(parts, w, h, d)
    basis = {}                                   # pivot bit -> vector
    for t in sorted(ev):
        v = ev[t]
        x = v
        while x:
            p = x.bit_length() - 1
            if p in basis:
                x ^= basis[p]
            else:
                basis[p] = x
                break
        # is eps in the span now?
        y = eps
        while y:
            p = y.bit_length() - 1
            if p not in basis:
                break
            y ^= basis[p]
        if y == 0:
            return t
    return None                                  # impossible


# ------------------------------------------------------------------- brute --
def brute(w, h, d, r, b, parts, horizon_mult=1):
    """
    Fully independent: event times by direct wall-by-wall stepping, and the
    combinatorics by reachability BFS over the 2^n parity states instead of
    linear algebra.
    """
    n = len(parts)
    eps = 0
    for i, (px, py, vx, vy) in enumerate(parts):
        if (i < r) != (px < 0):
            eps |= 1 << i
    if eps == 0:
        return Fraction(0)
    G = 0
    for (px, py, vx, vy) in parts:
        if vx == 0:
            continue
        G = gcd(G, gcd(2 * w * abs(vy), 2 * h * abs(vx)))
    if G == 0:
        return None
    P = Fraction(4 * w * h, G) * horizon_mult
    ev = {}
    for i, p in enumerate(parts):
        for t in brute_events(*p, w, h, d, P):
            if t > 0 and t < P:
                ev[t] = ev.get(t, 0) | (1 << i)
    reach = {0}
    for t in sorted(ev):
        v = ev[t]
        reach = reach | {s ^ v for s in reach}
        if eps in reach:
            return t
    return None


# ---------------------------------------------- physical end-to-end replay --
def replay(w, h, d, r, b, parts, triggers):
    """
    Simulate honestly: each particle bounces inside its own chamber; at a
    trigger time every particle standing at (0,d) swaps chamber.  Returns the
    final chamber list ('L'/'R') right after the last trigger.
    """
    n = len(parts)
    side = ['L' if p[0] < 0 else 'R' for p in parts]
    for t in sorted(triggers):
        for i, (px, py, vx, vy) in enumerate(parts):
            if vx == 0:
                continue
            # wall arrivals are decision independent
            t0 = first_wall_hit(px, vx, w)
            step = Fraction(2 * w, abs(vx))
            if t >= t0 and (t - t0) % step == 0 and fold(py + vy * t, 2 * h, h) == d:
                side[i] = 'R' if side[i] == 'L' else 'L'
    return side


def ok(side, r):
    return all(s == 'L' for s in side[:r]) and all(s == 'R' for s in side[r:])


# -------------------------------------------------------------------- main --
def parse(txt):
    it = list(map(int, txt.split()))
    w, h, d, r, b = it[:5]
    parts = []
    for j in range(r + b):
        parts.append(tuple(it[5 + 4 * j: 9 + 4 * j]))
    return w, h, d, r, b, parts


def fmt(x):
    return "impossible" if x is None else "%.6f" % float(x)


SAMPLES = [
    ("7 4 1 1 1  2 1 4 1  -3 1 2 0", "24.0"),
    ("4 4 1 2 2  3 1 2 2  -2 3 -2 -1  3 2 1 -2  -2 2 2 2", "impossible"),
]

if __name__ == "__main__":
    print("== samples ==")
    for txt, want in SAMPLES:
        a = solve(*parse(txt))
        bb = brute(*parse(txt))
        print(f"  got={fmt(a):>12}  brute={fmt(bb):>12}  expected={want}")
        assert fmt(a) == fmt(bb)

    print("== random cross-check (solver vs BFS brute, independent event gen) ==")
    random.seed(7)
    bad = 0
    for it in range(4000):
        w = random.randint(2, 6); h = random.randint(2, 6)
        d = random.randint(0, h)
        n = random.randint(1, 5)
        parts = []
        for _ in range(n):
            while True:
                px = random.randint(-(w - 1), w - 1)
                if px: break
            py = random.randint(1, h - 1)
            while True:
                vx = random.randint(-(w - 1), w - 1)
                vy = random.randint(-(h - 1), h - 1)
                if (vx, vy) != (0, 0): break
            parts.append((px, py, vx, vy))
        r = random.randint(0, n); b = n - r
        a = solve(w, h, d, r, b, parts)
        bb = brute(w, h, d, r, b, parts)
        if fmt(a) != fmt(bb):
            bad += 1
            print("MISMATCH", w, h, d, r, b, parts, fmt(a), fmt(bb))
            if bad > 4: break
        # longer horizon must not find anything better / anything at all
        if a is None:
            b3 = brute(w, h, d, r, b, parts, horizon_mult=3)
            if b3 is not None:
                bad += 1
                print("PERIOD BOUND VIOLATED", w, h, d, r, b, parts, fmt(b3))
                if bad > 4: break
        # physical replay of a witness schedule
        if a is not None and a > 0:
            P, ev = collect(parts, w, h, d)
            times = [t for t in sorted(ev) if t <= a]
            # search a subset achieving the goal with max time == a
            found = False
            for mask in range(1 << len(times)):
                if not (mask >> (len(times) - 1)) & 1:
                    continue
                sel = [times[j] for j in range(len(times)) if (mask >> j) & 1]
                if ok(replay(w, h, d, r, b, parts, sel), r):
                    found = True; break
                if len(times) > 16: break
            if len(times) <= 16 and not found:
                bad += 1
                print("NO PHYSICAL WITNESS", w, h, d, r, b, parts, fmt(a))
                if bad > 4: break
    print("  mismatches:", bad)


# ------------------------------------------------------------------------------
# SECOND, FULLY INDEPENDENT CHECK: an event-driven physics simulator.  Each
# particle really bounces inside its *current* chamber (no unfolding, no
# arithmetic progressions); at every arrival at (0,d) the search branches on
# reflect-all / pass-all, memoised on the exact configuration.  This tests the
# decision-independence claim itself, not just the number theory / algebra.
# ------------------------------------------------------------------------------

def advance(p, dt, w, h):
    """move one particle (x,y,vx,vy,side) by dt inside its chamber, handling all bounces (no demon)."""
    x, y, vx, vy, side = p
    lo, hi = (F(-w), F(0)) if side == 'L' else (F(0), F(w))
    rem = dt
    while rem > 0:
        tx = None
        if vx > 0: tx = (hi - x) / vx
        elif vx < 0: tx = (lo - x) / vx
        ty = None
        if vy > 0: ty = (h - y) / vy
        elif vy < 0: ty = (0 - y) / vy
        cands = [c for c in (tx, ty) if c is not None]
        tn = min(cands)
        if tn > rem or (tn == rem):
            x += vx * rem; y += vy * rem; rem = 0
            # reflect if exactly on a wall at the end (state after bounce)
            if x == lo or x == hi: vx = -vx
            if y == 0 or y == h: vy = -vy
            break
        x += vx * tn; y += vy * tn; rem -= tn
        if x == lo or x == hi: vx = -vx
        if y == 0 or y == h: vy = -vy
    return (x, y, vx, vy, side)

def next_center_hit(p, w, h, d):
    """time until this particle is next at (0,d), simulating bounce by bounce (None if never within a cap)."""
    x, y, vx, vy, side = p
    if vx == 0: return None
    t = F(0)
    for _ in range(4000):
        lo, hi = (F(-w), F(0)) if side == 'L' else (F(0), F(w))
        tx = (hi - x) / vx if vx > 0 else (lo - x) / vx
        ty = None
        if vy > 0: ty = (h - y) / vy
        elif vy < 0: ty = (0 - y) / vy
        tn = tx if ty is None else min(tx, ty)
        if tn == 0:  # sitting on wall right now with velocity already reflected: step past
            pass
        x += vx * tn; y += vy * tn; t += tn
        hitx = (x == lo or x == hi)
        if y == 0 or y == h: vy = -vy
        if hitx:
            if x == 0 and y == d and t > 0:
                return t
            vx = -vx
    return None

def phys_answer(w, h, d, r, b, parts, P):
    n = len(parts)
    init = tuple((F(px), F(py), F(vx), F(vy), 'L' if px < 0 else 'R') for (px, py, vx, vy) in parts)
    def good(cfg):
        return all(c[4] == 'L' for c in cfg[:r]) and all(c[4] == 'R' for c in cfg[r:])
    if good(init): return F(0)
    best = [None]
    seen = set()
    # DFS over (time, config)
    stack = [(F(0), init)]
    while stack:
        t, cfg = stack.pop()
        if (t, cfg) in seen: continue
        seen.add((t, cfg))
        # next arrival time at (0,d) among particles
        nxt = None
        for c in cfg:
            if c[4] not in 'LR': continue
            th = next_center_hit(c, w, h, d)
            if th is not None and (nxt is None or th < nxt): nxt = th
        if nxt is None: continue
        t2 = t + nxt
        if t2 >= P: continue
        if best[0] is not None and t2 >= best[0]: continue
        moved = tuple(advance(c, nxt, w, h) for c in cfg)
        # which particles are at (0,d)?
        at = [i for i, c in enumerate(moved) if c[0] == 0 and c[1] == d]
        assert at
        # option 1: reflect all (already reflected by advance)
        stack.append((t2, moved))
        # option 2: pass all: undo x-reflection, flip side
        passed = list(moved)
        for i in at:
            x, y, vx, vy, side = moved[i]
            passed[i] = (x, y, -vx, vy, 'R' if side == 'L' else 'L')
        passed = tuple(passed)
        if good(passed):
            if best[0] is None or t2 < best[0]: best[0] = t2
        stack.append((t2, passed))
    return best[0]

def physical_check():
    random.seed(11)
    bad = 0; nontriv = 0; tested = 0
    for it in range(1500):
        w = random.randint(2, 4); h = random.randint(2, 4)
        d = random.randint(0, h)
        n = random.randint(1, 3)
        parts = []
        for _ in range(n):
            while True:
                px = random.randint(-(w - 1), w - 1)
                if px: break
            py = random.randint(1, h - 1)
            while True:
                vx = random.randint(-(w - 1), w - 1); vy = random.randint(-(h - 1), h - 1)
                if (vx, vy) != (0, 0): break
            parts.append((px, py, vx, vy))
        r = random.randint(0, n); b = n - r
        G = 0
        for (px, py, vx, vy) in parts:
            if vx: G = gcd(G, gcd(2 * w * abs(vy), 2 * h * abs(vx)))
        if G == 0: continue
        P = F(4 * w * h, G)
        if P > 60: continue
        a = solve(w, h, d, r, b, parts)
        ph = phys_answer(w, h, d, r, b, parts, P)
        tested += 1
        if a is not None and a > 0: nontriv += 1
        if fmt(a) != fmt(ph):
            bad += 1
            print("MISMATCH", w, h, d, r, b, parts, fmt(a), fmt(ph))
            if bad > 5: break
    print("tested", tested, "nontrivial", nontriv, "bad", bad)


if __name__ == "__main__":
    print("== physical simulator cross-check ==")
    physical_check()
