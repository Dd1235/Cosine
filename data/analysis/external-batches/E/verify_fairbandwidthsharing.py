"""Verify the intended solution for Kattis 'fairbandwidthsharing'.

Intended solution (KKT / water-filling on a Lagrange multiplier):
    minimise  sum (x_i - y_i)^2 / y_i   s.t. a_i <= x_i <= b_i, sum x_i = t,
    where y_i = t*d_i/D is the fair share.
Stationarity gives 2(x_i - y_i)/y_i = lambda on every unclamped coordinate, so
    x_i = clamp(m * d_i, a_i, b_i)
for one scalar m >= 0 (y_i is proportional to d_i).  sum_i clamp(m*d_i,a_i,b_i)
is non-decreasing and continuous in m, so bisect on m.

Cross-checks below are deliberately independent of that derivation:
  (1) exhaustive grid search over the feasible polytope for tiny n,
  (2) pairwise coordinate descent (exact 1-D minimisation of the transfer
      between two coordinates), started from an arbitrary feasible point.
"""
import random, itertools

# ---------------------------------------------------------------- intended
def solve(n, t, abd):
    lo, hi = 0.0, 0.0
    for a, b, d in abd:
        hi = max(hi, b / d)
    hi = max(hi, 1.0)
    def total(m):
        s = 0.0
        for a, b, d in abd:
            v = m * d
            if v < a: v = a
            elif v > b: v = b
            s += v
        return s
    for _ in range(200):
        mid = (lo + hi) / 2
        if total(mid) < t: lo = mid
        else: hi = mid
    m = (lo + hi) / 2
    return [min(max(m * d, a), b) for a, b, d in abd]

def obj(x, n, t, abd):
    D = sum(d for _, _, d in abd)
    s = 0.0
    for xi, (_, _, d) in zip(x, abd):
        y = t * d / D
        s += (xi - y) ** 2 / y
    return s

# ------------------------------------------------------------- brute force 1
def brute_grid(n, t, abd, step):
    """Exhaustive search on a lattice of feasible points (n small, t small)."""
    best = None; bestx = None
    ranges = []
    for a, b, d in abd:
        vals = []
        k = 0
        while a + k * step <= b + 1e-12:
            vals.append(a + k * step); k += 1
        if not vals or abs(vals[-1] - b) > 1e-12: vals.append(b)
        ranges.append(vals)
    for combo in itertools.product(*ranges[:-1]):
        last = t - sum(combo)
        a, b, _ = abd[-1]
        if last < a - 1e-12 or last > b + 1e-12: continue
        x = list(combo) + [last]
        v = obj(x, n, t, abd)
        if best is None or v < best: best, bestx = v, x
    return best, bestx

# ------------------------------------------------------------- brute force 2
def brute_pairwise(n, t, abd, iters=40000):
    """Pairwise coordinate descent: move mass between two coordinates, taking the
    exact minimiser of the resulting 1-D convex quadratic, until nothing moves."""
    D = sum(d for _, _, d in abd)
    y = [t * d / D for _, _, d in abd]
    # feasible start: a_i, then pour the rest in index order
    x = [a for a, b, d in abd]
    rem = t - sum(x)
    for i, (a, b, d) in enumerate(abd):
        add = min(rem, b - x[i]); x[i] += add; rem -= add
    assert rem < 1e-9, "infeasible instance"
    rng = random.Random(12345)
    for _ in range(iters):
        i = rng.randrange(n); j = rng.randrange(n)
        if i == j: continue
        # minimise (x_i+s-y_i)^2/y_i + (x_j-s-y_j)^2/y_j over admissible s
        num = (y[i] - x[i]) / y[i] - (y[j] - x[j]) / y[j]
        den = 1.0 / y[i] + 1.0 / y[j]
        s = num / den if den else 0.0
        lo = max(abd[i][0] - x[i], x[j] - abd[j][1])
        hi = min(abd[i][1] - x[i], x[j] - abd[j][0])
        s = max(lo, min(hi, s))
        x[i] += s; x[j] -= s
    return obj(x, n, t, abd), x

# ------------------------------------------------------------------- samples
def check_samples():
    s1 = solve(3, 10, [(0, 10, 1), (0, 10, 1), (0, 10, 1)])
    assert all(abs(v - 10 / 3) < 1e-6 for v in s1), s1
    s2 = solve(3, 10, [(0, 1, 1000), (2, 8, 2), (2, 8, 1)])
    assert all(abs(u - v) < 1e-6 for u, v in zip(s2, [1.0, 6.0, 3.0])), s2
    print("samples OK")

def random_instance(rng, n, tmax):
    abd = []
    for _ in range(n):
        a = rng.randint(0, 3)
        b = rng.randint(max(a, 1), max(a, 1) + rng.randint(0, 4))
        abd.append((a, b, rng.randint(1, 8)))
    lo = sum(a for a, b, d in abd); hi = sum(b for a, b, d in abd)
    if lo > tmax: return None
    t = rng.randint(max(1, lo), min(hi, tmax))
    return t, abd

def main():
    check_samples()
    rng = random.Random(7)
    # (1) grid cross-check, n in {2,3}
    bad = 0; tested = 0
    for it in range(400):
        n = rng.choice([2, 3])
        inst = random_instance(rng, n, 6)
        if inst is None: continue
        t, abd = inst
        x = solve(n, t, abd)
        assert abs(sum(x) - t) < 1e-6, (t, abd, x)
        assert all(a - 1e-9 <= xi <= b + 1e-9 for xi, (a, b, d) in zip(x, abd))
        mine = obj(x, n, t, abd)
        g, gx = brute_grid(n, t, abd, 0.05)
        tested += 1
        if g is not None and mine > g + 1e-9:
            bad += 1
            print("GRID BEATS SOLUTION", t, abd, mine, g, x, gx)
    print(f"grid cross-check: {tested} instances, {bad} failures")

    # (2) pairwise-descent cross-check, larger n
    bad2 = 0; tested2 = 0; worst = 0.0
    for it in range(300):
        n = rng.randint(2, 9)
        inst = random_instance(rng, n, 40)
        if inst is None: continue
        t, abd = inst
        x = solve(n, t, abd)
        mine = obj(x, n, t, abd)
        p, px = brute_pairwise(n, t, abd)
        tested2 += 1
        worst = max(worst, abs(mine - p))
        if mine > p + 1e-7:
            bad2 += 1
            print("DESCENT BEATS SOLUTION", t, abd, mine, p, x, px)
        # solutions should also agree coordinate-wise (minimiser is unique)
        for xi, pi in zip(x, px):
            if abs(xi - pi) > 1e-4:
                bad2 += 1; print("COORD MISMATCH", t, abd, x, px); break
    print(f"pairwise cross-check: {tested2} instances, {bad2} failures, "
          f"max |obj diff| = {worst:.3e}")

    # (3) big instance at the stated limits, just to time the bisection
    import time
    rng2 = random.Random(3)
    n = 10 ** 5
    abd = []
    for _ in range(n):
        a = rng2.randint(0, 5); b = a + rng2.randint(1, 20)
        abd.append((a, b, rng2.randint(1, 10 ** 6)))
    lo = sum(a for a, b, d in abd); hi = sum(b for a, b, d in abd)
    t = min(max(10 ** 6, lo), hi)
    st = time.time(); x = solve(n, t, abd); el = time.time() - st
    print(f"n=1e5 bisection: sum={sum(x):.6f} target={t} time={el:.2f}s (Python)")
    assert abs(sum(x) - t) < 1e-3

main()
