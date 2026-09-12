# O(n log n) float implementation, for a timing sanity check at n = 1e5.
import bisect, random, time, sys

def sv(v, s, m):
    lo = bisect.bisect_left(s, v); hi = bisect.bisect_right(s, v)
    return (lo + 0.5 * (hi - lo)) / m

def lower_hull(pts):
    pts = sorted(set(pts))
    if len(pts) <= 2: return pts
    h = []
    for p in pts:
        while len(h) >= 2:
            (ox,oy),(ax,ay)=h[-2],h[-1]
            if (ax-ox)*(p[1]-oy)-(ay-oy)*(p[0]-ox) <= 0: h.pop()
            else: break
        h.append(p)
    return h

def q(pts, c):
    h = lower_hull(pts); best = None
    for x,y in h:
        if x >= c and (best is None or y < best): best = y
    for (xa,ya),(xb,yb) in zip(h,h[1:]):
        if xa <= c <= xb and xa != xb:
            y = ya + (c-xa)/(xb-xa)*(yb-ya)
            if best is None or y < best: best = y
    return best

def solve(A,B):
    sA,sB = sorted(A), sorted(B)
    if sum(sv(v,sB,len(B)) for v in A)/len(A) > 0.5: D1,D2,s1,s2 = A,B,sA,sB
    else: D1,D2,s1,s2 = B,A,sB,sA
    vals = {1}
    for f in A: vals.add(f); vals.add(f+1)
    for f in B: vals.add(f); vals.add(f+1)
    pts = [(sv(v,s1,len(D1)), sv(v,s2,len(D2))) for v in sorted(vals)]
    a1 = q(pts, 0.5)
    a2 = -q([(-y,-x) for x,y in pts], -0.5)
    return a1,a2

print(solve([1,1,6,6,8,8],[2,4,9]), solve([9,3,7,5],[4,2,3]))
rng = random.Random(1)
A=[rng.randint(1,10**9) for _ in range(10**5)]
B=[rng.randint(1,10**9) for _ in range(10**5)]
t=time.time(); r=solve(A,B); print("n=1e5 ->", r, "%.2fs (python; C++ far faster)"%(time.time()-t))
