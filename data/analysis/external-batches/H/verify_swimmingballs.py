"""swimmingballs: water level h solves  W*L*h - sum_i displaced_i(h) = V, clamped at D.
A ball resting on the bottom is submerged to depth min(h,2r) (spherical cap pi t^2 (3r-t)/3); a ball
that floats displaces exactly its own weight w*(4/3)pi r^3.  Whichever is SMALLER is the real
displacement, so displaced(h) = min(cap(min(h,2r)), w*V_sphere) -- monotone non-decreasing in h, so
binary search on h.  Cross-checked against a dense scan of the same equation and against samples."""
import math, random

def cap(r, t):
    t = max(0.0, min(t, 2*r))
    return math.pi * t*t * (3*r - t) / 3.0

def disp(h, r, w):
    return min(cap(r, min(h, 2*r)), w * 4.0/3.0*math.pi*r**3)

def water(h, balls):
    return sum(disp(h, r, w) for r, w in balls)

def solve(n, W, L, D, V, balls):
    lo, hi = 0.0, float(D)
    if W*L*hi - water(hi, balls) <= V: return float(D)
    for _ in range(200):
        mid = (lo+hi)/2
        if W*L*mid - water(mid, balls) < V: lo = mid
        else: hi = mid
    return (lo+hi)/2

def scan(n, W, L, D, V, balls, steps=2000000):
    """independent: dense linear scan for the smallest h with net water volume >= V"""
    best = float(D)
    for k in range(steps+1):
        h = D*k/steps
        if W*L*h - water(h, balls) >= V:
            best = h; break
    return best

a = solve(1, 2, 2, 2, 5, [(1.0, 1.0)])
b = solve(1, 2, 2, 2, 5, [(0.8, 1.0)])
assert abs(a - 2.0) < 1e-9, a
assert abs(b - 1.78616514621) < 1e-8, b
random.seed(23)
worst = 0.0
for t in range(60):
    n = random.randint(1, 4)
    W = random.randint(2, 5); L = random.randint(2, 5); D = random.randint(1, 5)
    balls = [(round(random.uniform(0.05, 2.0), 2), round(random.uniform(0.05, 2.0), 2)) for _ in range(n)]
    V = random.uniform(0, W*L*D)
    s = solve(n, W, L, D, V, balls)
    sc = scan(n, W, L, D, V, balls, 200000)
    worst = max(worst, abs(s - sc))
print("samples ok (2.0 / 1.78616514621); max |binary-search - dense scan| =", worst)
