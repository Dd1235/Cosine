"""
kattis-jetlag  (ICPC World Finals 2023, "Jet Lag") -- solution + verification.

MODEL
-----
Activities [b_i, e_i] with b_i < e_i and e_i <= b_{i+1}; you must be awake for
every activity, so a sleep interval must lie inside one "gap"
    [0, b_1], [e_1, b_2], ..., [e_{n-1}, b_n].
A sleep [s, t] of length k = t - s is followed by k minutes "rested" (you cannot
fall asleep) and then k minutes "functioning" (you may fall asleep).  Hence the
NEXT sleep must start in
    [t + k, t + 2k] = [2t - s, 3t - 2s],
and if there is no next sleep you must stay functional through the last activity:
    3t - 2s >= e_n.
The first sleep is forced to start at minute 0.

REDUCTION (this is the whole problem)
-------------------------------------
(1) A sleep that starts at s inside the gap [L, R] may end at ANY t in (s, R].
(2) Union over those t of the successor windows [2t - s, 3t - 2s] is exactly the
    single interval [s + 2, 3R - 2s]  (consecutive windows overlap because
    2(t+1) - s <= (3t - 2s) + 1 whenever t >= s + 1).
    => the set of legal next sleep STARTS depends only on the start s (and its
       gap's right end R), not on where the sleep ended.
(3) That successor interval only grows as s decreases, and the terminal test
    "3R - 2s >= e_n" is also easiest for the smallest s.  So within each gap the
    EARLIEST reachable start dominates every later one -- no exchange needed,
    one start per gap suffices.
(4) Every activity is at least 1 minute long, so for a gap [L_m, R_m] and any
    start s <= R_{m'} - 1 in an earlier gap, L_m >= R_{m'} + 1 >= s + 2: the
    "+2" of step (2) never binds across gaps.  Therefore the earliest reachable
    start of a reachable gap is exactly its left end L_m.

ALGORITHM  (O(n) time, one left-to-right sweep, no sorting -- input is sorted)
    reach(gap) = 3R - 2L        # furthest minute you can stay functional to
    gap m is reachable  <=>  max reach over reachable earlier gaps >= L_m
    answer exists       <=>  some reachable gap has reach >= e_n
    (gap 0 must be [0, b_1], since the first sleep starts at minute 0)
Reconstruction: keep, for each reachable gap, the earlier gap that held the
running maximum reach; walk those predecessors back from the finishing gap.
Each chosen gap sleeps [L, t]; t is the smallest end that reaches the next
chain element's L (or e_n for the last one), which is
    t = L + ceil((next - L) / 3)   and this always satisfies 2t - L <= next,
so the sleep is never too long either.  The chain visits each gap at most once,
so p <= n <= 200000 <= 10^6.

VERIFICATION IN THIS FILE
    * solve()          - the O(n) sweep above
    * greedy_backward()- a SECOND, independently written right-to-left greedy
    * brute()          - exhaustive forward BFS over states (t, k), assuming
                         nothing from the reduction above
    * validate()       - independent replay of a schedule against the raw rules
    * three official samples; EXHAUSTIVE comparison over every activity pattern
      on a timeline of up to 16 minutes; random stress at several scales
      (including scaled-up copies, since the constraints are not scale free);
      and an n = 200000, e_n ~ 9*10^9 run for performance and the p <= 10^6 bound.
"""
import bisect
import random
import sys
import time


# ---------------------------------------------------------------- utilities
def gaps_of(acts):
    """Maximal intervals of free time before the last activity starts."""
    g = []
    if acts[0][0] > 0:
        g.append((0, acts[0][0]))
    for i in range(len(acts) - 1):
        L, R = acts[i][1], acts[i + 1][0]
        if L < R:
            g.append((L, R))
    return g


def ceil_div(a, b):
    return -((-a) // b)


def validate(acts, sleeps):
    """Replay a schedule against the raw statement rules.  Independent of solve()."""
    E = acts[-1][1]
    bn = acts[-1][0]
    gs = gaps_of(acts)
    Ls = [L for L, _ in gs]
    if not sleeps:
        return False
    if sleeps[0][0] != 0:                       # must fall asleep at minute 0
        return False
    if sleeps[-1][1] > bn:                      # no sleep after the last activity starts
        return False
    if len(sleeps) > 10 ** 6:
        return False
    prev = None
    for (s, t) in sleeps:
        if not (isinstance(s, int) and isinstance(t, int)) or not (0 <= s < t):
            return False
        i = bisect.bisect_right(Ls, s) - 1      # the sleep must sit inside one gap
        if i < 0 or not (gs[i][0] <= s and t <= gs[i][1]):
            return False
        if prev is not None:
            ps, pt = prev
            if not (2 * pt - ps <= s <= 3 * pt - 2 * ps):
                return False                    # too early (still rested) or too late
        prev = (s, t)
    s, t = sleeps[-1]
    return 3 * t - 2 * s >= E                   # functional through the last activity


# ---------------------------------------------------------------- the solution
def solve(acts):
    """O(n) left-to-right sweep.  Returns a schedule, or None for 'impossible'."""
    E = acts[-1][1]
    gs = gaps_of(acts)
    if not gs or gs[0][0] != 0:                 # b_1 == 0: cannot sleep at minute 0
        return None
    best, besti = -1, -1                        # running max reach and its gap
    pred = [-1] * len(gs)
    final = -1
    for i, (L, R) in enumerate(gs):
        if i > 0:
            if best < L:
                break                           # unreachable, and later gaps start later
            pred[i] = besti
        r = 3 * R - 2 * L
        if r >= E:
            final = i
            break
        if r > best:
            best, besti = r, i
    if final < 0:
        return None
    chain = [final]
    while chain[-1] != 0:
        chain.append(pred[chain[-1]])
    chain.reverse()
    out = []
    for idx, gi in enumerate(chain):
        L, R = gs[gi]
        nxt = gs[chain[idx + 1]][0] if idx + 1 < len(chain) else E
        t = max(L + 1, ceil_div(nxt + 2 * L, 3))   # smallest end with 3t-2L >= nxt
        out.append((L, t))
    return out


# ------------------------------------------- second, independent greedy (right to left)
def greedy_backward(acts):
    """Scan gaps right to left carrying the minute S that still has to be covered.
    A gap [L,R] can serve S iff R <= S, L + 2 <= S <= 3R - 2L; it then sleeps
    [L, L + ceil((S-L)/3)] and the new target becomes L.  Success iff the scan
    ends on the gap [0, b_1]."""
    E = acts[-1][1]
    gs = gaps_of(acts)
    out = []
    S = E
    for (L, R) in reversed(gs):
        if not out:
            if 3 * R - 2 * L >= E:
                out.append((L, max(L + 1, ceil_div(E + 2 * L, 3))))
                S = L
        elif R <= S and L + 2 <= S <= 3 * R - 2 * L:
            out.append((L, L + ceil_div(S - L, 3)))
            S = L
        if S == 0 and out:
            break
    if not out or S != 0:
        return None
    return list(reversed(out))


# ---------------------------------------------------------------- brute force
def brute(acts):
    """Exhaustive forward BFS over states (t, k) = (wake-up minute, sleep length).
    Uses only the raw rules -- none of the reduction the solution relies on.
    end_of[s] is the right end of the gap containing minute s (None if busy), which
    is just an index into the gap list, not an appeal to the solution's argument."""
    from collections import deque
    E = acts[-1][1]
    gs = gaps_of(acts)
    if not gs or gs[0][0] != 0:
        return None
    bn = acts[-1][0]
    end_of = [None] * (bn + 1)
    for (L, R) in gs:
        for s in range(L, R):
            end_of[s] = R
    par = {}
    dq = deque()
    for k in range(1, gs[0][1] + 1):            # first sleep: [0, k]
        st = (k, k)
        if st not in par:
            par[st] = None
            dq.append(st)
    while dq:
        t, k = dq.popleft()
        if t + 2 * k >= E:
            out, cur = [], (t, k)
            while cur is not None:
                tt, kk = cur
                out.append((tt - kk, tt))
                cur = par[cur]
            return out[::-1]
        for s in range(t + k, min(t + 2 * k, bn - 1) + 1):
            R = end_of[s]
            if R is None:
                continue
            for k2 in range(1, R - s + 1):
                st = (s + k2, k2)
                if st not in par:
                    par[st] = (t, k)
                    dq.append(st)
    return None


# ---------------------------------------------------------------- tests
SAMPLES = [
    ([(30, 45), (60, 90), (120, 180)], True),
    ([(0, 60)], False),
    ([(31, 32), (35, 41), (48, 55), (69, 91),
      (1000, 2022), (2022, 2023), (2994, 4096)], True),
]


def test_samples():
    for acts, feasible in SAMPLES:
        fns = [("solve", solve), ("greedy_backward", greedy_backward)]
        if acts[-1][1] <= 200:                  # brute is exponential in the timeline
            fns.append(("brute", brute))
        for name, fn in fns:
            r = fn(acts)
            assert (r is not None) == feasible, (name, acts, r)
            if r is not None:
                assert validate(acts, r), (name, acts, r)
        print("  sample ok:", acts[0], "...", "->", solve(acts))


def _acts_from_bits(bits):
    acts, i, T = [], 0, len(bits)
    while i < T:
        if bits[i] == '1':
            j = i
            while j < T and bits[j] == '1':
                j += 1
            acts.append((i, j))
            i = j
        else:
            i += 1
    return acts


def test_exhaustive(T=16):
    """Every possible busy/free pattern on a timeline of T minutes."""
    tested = feas = 0
    for mask in range(1 << T):
        bits = ''.join('1' if (mask >> i) & 1 else '0' for i in range(T))
        if bits[-1] != '1':                     # normalise: last activity ends at T
            continue
        acts = _acts_from_bits(bits)
        if not acts:
            continue
        tested += 1
        b, m, g = brute(acts), solve(acts), greedy_backward(acts)
        assert (b is None) == (m is None), ("solve vs brute", acts, b, m)
        assert (b is None) == (g is None), ("backward vs brute", acts, b, g)
        if b is not None:
            feas += 1
            assert validate(acts, b), ("brute schedule invalid", acts, b)
            assert validate(acts, m), ("solve schedule invalid", acts, m)
            assert validate(acts, g), ("backward schedule invalid", acts, g)
    print(f"  exhaustive T={T}: {tested} instances, {feas} feasible, all agree")


def _gen(rng, maxn, maxlen, scale=1):
    n = rng.randint(1, maxn)
    acts, cur = [], rng.randint(0, 3) * scale
    for _ in range(n):
        b = cur + rng.randint(0, maxlen) * scale
        e = b + rng.randint(1, maxlen) * scale
        acts.append((b, e))
        cur = e
    return acts


def test_random():
    # the rules are not scale invariant (3t-2s vs integer minutes), so scale varies
    cases = [("dense small", 2500, 6, 4, 1, 11),
             ("medium", 1200, 5, 12, 1, 12),
             ("scaled x3", 800, 4, 6, 3, 13),
             ("scaled x7", 500, 3, 5, 7, 14),
             ("long gaps", 600, 3, 20, 1, 15)]
    for tag, iters, maxn, maxlen, scale, seed in cases:
        rng = random.Random(seed)
        feas = 0
        for _ in range(iters):
            acts = _gen(rng, maxn, maxlen, scale)
            b, m, g = brute(acts), solve(acts), greedy_backward(acts)
            assert (b is None) == (m is None), ("solve vs brute", acts, b, m)
            assert (b is None) == (g is None), ("backward vs brute", acts, b, g)
            if b is not None:
                feas += 1
                assert validate(acts, m), ("solve schedule invalid", acts, m)
                assert validate(acts, g), ("backward schedule invalid", acts, g)
        print(f"  random {tag}: {iters} instances, {feas} feasible, all agree")


def test_limits():
    rng = random.Random(7)
    for tag, build in (("n=200000", "dense"), ("e_n~9e9", "huge")):
        acts, cur = [], rng.randint(1, 50)
        if build == "dense":
            for _ in range(200000):
                g = rng.randint(20, 60)
                b = cur + g
                e = b + rng.randint(1, 2 * g)
                acts.append((b, e))
                cur = e
        else:
            cur = rng.randint(1, 10 ** 4)
            while cur < 9 * 10 ** 9 and len(acts) < 200000:
                g = rng.randint(10 ** 4, 10 ** 5)
                b = cur + g
                e = b + rng.randint(1, 2 * g)
                acts.append((b, e))
                cur = e
        t0 = time.time()
        m = solve(acts)
        dt = time.time() - t0
        g2 = greedy_backward(acts)
        assert (m is None) == (g2 is None)
        p = 0
        if m is not None:
            assert validate(acts, m)
            assert validate(acts, g2)
            p = len(m)
            assert p <= 10 ** 6
        print(f"  limits {tag}: n={len(acts)} e_n={acts[-1][1]} feasible={m is not None} "
              f"p={p} solve={dt:.2f}s")


def test_traps():
    """The two plausible-but-wrong greedies, refuted on the smallest witnesses."""
    # (a) "sleep to the end of every gap": on this instance sleeping [0,2] leaves you
    #     unable to fall asleep before minute 4, so the second gap only yields a
    #     1-minute sleep reaching 7 < 8; [0,1] then [3,5] reaches 9.
    acts = [(2, 3), (5, 8)]
    assert brute(acts) is not None and solve(acts) is not None
    assert validate(acts, solve(acts))
    assert validate(acts, [(0, 1), (3, 5)])
    assert not validate(acts, [(0, 2), (4, 5)])
    # (b) the chain does not have to use every usable gap
    acts = [(30, 45), (60, 90), (120, 180)]
    assert len(solve(acts)) == 2 and len(gaps_of(acts)) == 3
    print("  traps ok: max-length-sleep greedy refuted, gap-skipping confirmed")


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    print("samples:")
    test_samples()
    print("traps:")
    test_traps()
    print("exhaustive:")
    test_exhaustive(16)
    print("random:")
    test_random()
    print("limits:")
    test_limits()
    print("ALL OK")
