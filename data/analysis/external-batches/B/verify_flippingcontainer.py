"""kattis-flippingcontainer / "Flipping Container" (ICPC WF 2024) -- verification.

Model.  Orientation = (E,N,U) permutation of (a,b,c); S = a+b+c.  Track the
footprint centre in DOUBLED units.  An x-flip moves cx by +-(E+U) = +-(S-N)
and swaps E<->U; a y-flip moves cy by +-(S-E) and swaps N<->U.  Target:
orientation back to (a,b,c) and (cx,cy) = (2x,2y).

Reduction (derived, checked by BFS below).  The 6 orientations with the two
transpositions s=(E U), t=(N U) form a HEXAGON whose edges alternate x/y:
   o0 -[x,N=b]- -[y,E=c]- -[x,N=a]- -[y,E=b]- -[x,N=c]- -[y,E=a]- o0
A flip sequence = closed walk from o0.  Let t_e = #traversals of edge e and
sigma_e = (#east/north flips on e) - (#west/south flips on e); cost = sum t_e,
displacement = sum sigma_e * w_e (w_e = S - N_e resp. S - E_e), and
|sigma_e| <= t_e, sigma_e = t_e (mod 2).  A closed walk on a cycle graph has
cw - ccw = f on EVERY edge (same f), so t_e = f (mod 2) and t_e >= |f|; the
traversed edges must be connected and contain o0.  Only f in {0,1} matter
(f=2 is dominated by f=0 with the full hexagon, f=3 by f=1):
   f=1 : all six sigma_e ODD, cost = sum |sigma_e|.
   f=0 : all sigma_e EVEN, support inside an arc of the hexagon that contains
         o0, cost = sum_{e in arc} max(|sigma_e|, 2).
Both cases split into an independent x and y "coin" problem with <=3 weights
(each of S-a, S-b, S-c appears once per axis).  Each 1-D problem is solved
exactly: the smallest weight's coefficient is bounded by 2*w_max (exchange),
loop it; the remaining two weights are solved by a linear congruence, whose
solutions form an arithmetic progression on which the (convex) cost is
minimised at a breakpoint.  O(6 * 4000 * 2 * 28) elementary ops, x,y ~ 1e18 ok.
"""
import math, random, sys
from collections import deque


# ---------------------------------------------------------------- intended
def _cost(s, floor2):
    return max(abs(s), 2) if floor2 else abs(s)


def solve2(w2, wb, T, r, floor2):
    """min c(s2)+c(sb) with s2*w2 + sb*wb = T, s2,sb = r (mod 2); None if impossible."""
    T2 = T - r * (w2 + wb)
    if T2 % 2:
        return None
    M = T2 // 2                      # u*w2 + v*wb = M, s2=2u+r, sb=2v+r
    g = math.gcd(w2, wb)
    if M % g:
        return None
    w2p, wbp, Mp = w2 // g, wb // g, M // g
    u0 = 0 if wbp == 1 else (Mp * pow(w2p, -1, wbp)) % wbp
    # progression u = u0 + j*wbp ; v = (Mp - u*w2p)/wbp

    def cost_j(j):
        u = u0 + j * wbp
        v = (Mp - u * w2p) // wbp
        return _cost(2 * u + r, floor2) + _cost(2 * v + r, floor2)

    cands = set()
    for tgt in (-2, 0, 2):
        # 2u+r = tgt  -> u = (tgt-r)/2
        ju = ((tgt - r) / 2 - u0) / wbp
        # 2v+r = tgt  -> v=(tgt-r)/2 -> u = (Mp - v*wbp)/w2p
        jv = ((Mp - ((tgt - r) / 2) * wbp) / w2p - u0) / wbp
        for jj in (ju, jv):
            base = math.floor(jj)
            for d in (-2, -1, 0, 1, 2):
                cands.add(base + d)
    return min(cost_j(j) for j in cands)


def solve1d(W, T, r, floor2):
    """min sum c(sigma_e) over e in W with sum sigma_e*w_e = T, sigma_e = r mod 2."""
    if not W:
        return 0 if T == 0 else None
    W = sorted(W, reverse=True)
    if len(W) == 1:
        w = W[0]
        if T % w:
            return None
        s = T // w
        return _cost(s, floor2) if s % 2 == r else None
    if len(W) == 2:
        return solve2(W[1], W[0], T, r, floor2)
    wb, w2, w1 = W
    best = None
    lim = 2 * wb
    start = -lim if (-lim) % 2 == r else -lim + 1
    for s1 in range(start, lim + 1, 2):
        sub = solve2(w2, wb, T - s1 * w1, r, floor2)
        if sub is None:
            continue
        c = _cost(s1, floor2) + sub
        if best is None or c < best:
            best = c
    return best


def fast(a, b, c, x, y):
    S = a + b + c
    wa, wb, wc = S - a, S - b, S - c
    Tx, Ty = 2 * x, 2 * y
    # hexagon edges from o0 going "s-first": (axis, weight)
    edges = [('x', wb), ('y', wc), ('x', wa), ('y', wb), ('x', wc), ('y', wa)]
    best = None

    def upd(v):
        nonlocal best
        if v is not None and (best is None or v < best):
            best = v

    # f = 1 : all sigma odd
    fx = solve1d([wa, wb, wc], Tx, 1, False)
    fy = solve1d([wa, wb, wc], Ty, 1, False)
    if fx is not None and fy is not None:
        upd(fx + fy)
    # f = 0 : even sigma, arc containing o0 = first i edges + last k edges
    memo = {}
    for i in range(0, 7):
        for k in range(0, 7 - i):
            idx = set(range(i)) | set(range(6 - k, 6))
            Xw = tuple(sorted(edges[e][1] for e in idx if edges[e][0] == 'x'))
            Yw = tuple(sorted(edges[e][1] for e in idx if edges[e][0] == 'y'))
            if ('x', Xw) not in memo:
                memo[('x', Xw)] = solve1d(list(Xw), Tx, 0, True)
            if ('y', Yw) not in memo:
                memo[('y', Yw)] = solve1d(list(Yw), Ty, 0, True)
            cx_, cy_ = memo[('x', Xw)], memo[('y', Yw)]
            if cx_ is not None and cy_ is not None:
                upd(cx_ + cy_)
    return best  # None == impossible


# ------------------------------------------------------------------- brute
def brute_table(a, b, c, B):
    """BFS over (orientation, cx, cy) with |cx|,|cy| <= B (doubled units)."""
    S = a + b + c
    start = ((a, b, c), 0, 0)
    dist = {start: 0}
    dq = deque([start])
    while dq:
        st = dq.popleft()
        (E, N, U), cx, cy = st
        d = dist[st] + 1
        nxt = []
        for sg in (1, -1):
            nxt.append(((U, N, E), cx + sg * (E + U), cy))
            nxt.append(((E, U, N), cx, cy + sg * (N + U)))
        for ns in nxt:
            if abs(ns[1]) > B or abs(ns[2]) > B:
                continue
            if ns not in dist:
                dist[ns] = d
                dq.append(ns)
    return dist


def brute(dist, a, b, c, x, y):
    return dist.get(((a, b, c), 2 * x, 2 * y))


# ------------------------------------------------------------------- tests
def samples():
    cases = [((3, 4, 5, 8, 0), 2), ((3, 4, 5, -8, 9), 4),
             ((3, 4, 5, 123, 45), 40), ((20, 10, 30, 13, 37), None)]
    for args, want in cases:
        got = fast(*args)
        print("sample", args, "->", got, "expected", want)
        assert got == want


def cross_check(seed=1, triples=12, R=14, B=170):
    rng = random.Random(seed)
    mism = 0
    for _ in range(triples):
        while True:
            a, b, c = rng.randint(1, 7), rng.randint(1, 7), rng.randint(1, 7)
            if len({a, b, c}) == 3:
                break
        dist = brute_table(a, b, c, B)
        for x in range(-R, R + 1):
            for y in range(-R, R + 1):
                f_, b_ = fast(a, b, c, x, y), brute(dist, a, b, c, x, y)
                if f_ != b_:
                    mism += 1
                    if mism <= 10:
                        print("MISMATCH", (a, b, c, x, y), "fast", f_, "brute", b_)
        print("checked dims", (a, b, c), "targets", (2 * R + 1) ** 2, "mismatches so far", mism)
    return mism


if __name__ == "__main__":
    samples()
    m = cross_check()
    print("total mismatches:", m)
    import time
    t = time.time()
    print("big:", fast(999, 1000, 997, 10**18, -10**18), "in", round(time.time() - t, 2), "s")
    t = time.time()
    print("big:", fast(1, 2, 1000, -10**18, 10**18 - 1), "in", round(time.time() - t, 2), "s")
