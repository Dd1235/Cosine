"""Game of Divisibility: n <= 1024 numbers, k in [2,32].  Players alternately remove
one number; Viet moves first; each player's score is the sum of what he took.  The
winner is the player whose score is divisible by k when the OTHER one's is not;
otherwise it is a draw.  Report FIRST / SECOND / DRAW under optimal play.

Only residues matter.  Let c_r be the count of a_i = r (mod k),
  base0 = sum_r floor(c_r/2) * r   (mod k)      -- one element out of each equal pair
  z     = #{ r : c_r odd }                      -- note n = z (mod 2)
  S     = 2*base0 + sum_{r: c_r odd} r          (mod k)
Rule (derived from a mirroring analysis and verified exhaustively below):
  z == 0            -> DRAW                (Nam mirrors equal pairs; V = base0 and
                                            S - V = base0, so both or neither divide)
  z == 1, class r   -> V = base0 + r is FORCED; report val(V)
  z == 2, {r1,r2}   -> FIRST iff S != 0 and (base0+r1 == 0 or base0+r2 == 0),
                       otherwise DRAW      (SECOND is impossible when n is even)
  z >= 3            -> DRAW
O(n + k) per dataset, O(k) space.

Underlying structural theorem (also checked here): the value equals
  n even : min over perfect matchings P of the multiset of max_{v in Sigma(P)} val(v)
  n odd  : max over (first pick x, matching P of the rest) of min_{v in x+Sigma(P)} val(v)
where Sigma(P) = { sums taking one element from each pair }, i.e. mirroring is
optimal for both players.

Checks below: (1) the three samples, (2) the O(k) rule against a full game-tree
search for every residue multiset with k = 2..6 and n up to 8-10, (3) the rule
against the matching theorem, (4) the "outcome depends only on (parities, base0)"
reduction.
"""
import itertools, random
from functools import lru_cache

FIRST, DRAW, SECOND = 3, 2, 1
NAME = {FIRST: 'FIRST', DRAW: 'DRAW', SECOND: 'SECOND'}

def val(v, S, k):
    vd = (v % k == 0); nd = ((S - v) % k == 0)
    if vd and not nd: return FIRST
    if nd and not vd: return SECOND
    return DRAW

def fast(a, k):
    c = [0]*k
    for x in a: c[x % k] += 1
    base0 = sum((c[r]//2)*r for r in range(k)) % k
    odd = [r for r in range(k) if c[r] % 2]
    z = len(odd)
    S = (2*base0 + sum(odd)) % k
    if z == 0: return DRAW
    if z == 1:
        return val((base0 + odd[0]) % k, S, k)
    if z == 2:
        if S % k and ((base0 + odd[0]) % k == 0 or (base0 + odd[1]) % k == 0):
            return FIRST
        return DRAW
    return DRAW

def game(cnt, k):
    S = sum(r*c for r, c in enumerate(cnt)) % k
    @lru_cache(maxsize=None)
    def rec(cnt, V, turn):
        if sum(cnt) == 0: return val(V, S, k)
        vals = []
        for r in range(k):
            if cnt[r]:
                nc = list(cnt); nc[r] -= 1
                vals.append(rec(tuple(nc), (V+r) % k if turn == 0 else V, 1-turn))
        return max(vals) if turn == 0 else min(vals)
    o = rec(tuple(cnt), 0, 0); rec.cache_clear(); return o

# ---- the matching theorem, used as a second independent reference ----
def matchings(lst):
    if not lst: yield []; return
    a = lst[0]
    for i in range(1, len(lst)):
        rest = lst[1:i] + lst[i+1:]
        for m in matchings(rest): yield [(a, lst[i])] + m

def sigma(pairs, k):
    s = {0}
    for x, y in pairs:
        s = {(u+x) % k for u in s} | {(u+y) % k for u in s}
    return s

def theorem(res, k):
    n = len(res); S = sum(res) % k
    if n % 2 == 0:
        best = None
        for P in matchings(list(range(n))):
            pp = [(res[i], res[j]) for i, j in P]
            v = max(val(x, S, k) for x in sigma(pp, k))
            best = v if best is None else min(best, v)
        return best
    best = None
    for i in range(n):
        rest = [j for j in range(n) if j != i]
        for P in matchings(rest):
            pp = [(res[a], res[b]) for a, b in P]
            v = min(val((res[i]+x) % k, S, k) for x in sigma(pp, k))
            best = v if best is None else max(best, v)
    return best

def main():
    assert NAME[fast([4,4,2], 4)] == 'SECOND'
    assert NAME[fast([4,4,8], 4)] == 'DRAW'
    assert NAME[fast([2,2,2], 4)] == 'FIRST'
    print("samples OK")

    bad = 0; tested = 0
    for k in [2,3,4,5,6]:
        MAXN = 10 if k <= 3 else (9 if k == 4 else 8)
        for n in range(1, MAXN+1):
            for res in itertools.combinations_with_replacement(range(k), n):
                cnt = [0]*k
                for r in res: cnt[r] += 1
                g = game(cnt, k); f = fast(list(res), k); tested += 1
                if g != f:
                    bad += 1
                    if bad < 8:
                        print("MISMATCH k=%d res=%s game=%s rule=%s" % (k, res, NAME[g], NAME[f]))
    print("O(k) rule vs full game tree: %d multisets, mismatches = %d" % (tested, bad))
    assert bad == 0

    bad = 0; tested = 0
    for k in [2,3,4,5]:
        for n in range(1, 8):
            for res in itertools.combinations_with_replacement(range(k), n):
                if theorem(list(res), k) != fast(list(res), k): bad += 1
                tested += 1
    print("O(k) rule vs the mirroring/matching theorem: %d multisets, mismatches = %d" % (tested, bad))
    assert bad == 0

    # big random instances: rule must agree with the game tree wherever the tree is
    # affordable, and with the (parities, base0) reduction everywhere
    random.seed(13); bad = 0
    for _ in range(4000):
        k = random.randint(2, 32)
        n = random.randint(1, 1024)
        a = [random.randint(0, 2**31) for _ in range(min(n, 60))]
        a += [random.choice(a) for _ in range(n - len(a))]
        c = [0]*k
        for x in a: c[x % k] += 1
        base0 = sum((c[r]//2)*r for r in range(k)) % k
        p = tuple(x % 2 for x in c)
        # canonical representative with the same (p, base0)
        c2 = list(p); c2[1] += 2*base0
        if sum(c2) <= 9 and k <= 6:
            if game(c2, k) != fast(a, k): bad += 1
        # reduction invariance
        a2 = [r for r in range(k) for _ in range(c2[r])]
        if fast(a2, k) != fast(a, k): bad += 1
    print("large random instances (reduction + game where affordable): mismatches =", bad)
    assert bad == 0
    print("gameofdivisibility: OK")

main()
