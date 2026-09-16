"""Land Inheritance: simple polygon P (N<=100, integer coords) and a line L.
Alob owns A = P on one side, Bice owns B = P on the other; their fields must be
mirror images across L.  Maximise Alob's field area  =>  area(A  intersect  mirror(B)).
(The answer is side-independent: mirror(A cap mirror(B)) = mirror(A) cap B.)

Solution: decompose P into SIGNED triangles (O,p_i,p_{i+1}) with sign s_i, so that
sum_i s_i * [x in T_i] is the indicator of P (orient P counter-clockwise first).
Then indicator(A)   = sum_i s_i [x in T_i cap H+]
     indicator(B')  = sum_j s_j [x in mirror(T_j cap H-)]
and area(A cap B') = sum_{i,j} s_i s_j * area( (T_i cap H+) cap mirror(T_j cap H-) ),
each factor a CONVEX polygon (triangle clipped by a half-plane, <=4 vertices), so
each term is one convex-convex clip.  O(N^2) clips, O(N) space.

Check: the three samples, plus Monte-Carlo estimation of area(A cap mirror(B))
on random simple polygons.
"""
import random, math

EPS = 1e-12

def poly_area(pts):
    s = 0.0
    for i in range(len(pts)):
        x1,y1 = pts[i]; x2,y2 = pts[(i+1)%len(pts)]
        s += x1*y2 - x2*y1
    return s/2.0

def clip_halfplane(poly, a, b, c):
    """keep {(x,y): a*x+b*y+c >= 0}"""
    if not poly: return []
    out=[]
    n=len(poly)
    for i in range(n):
        p=poly[i]; q=poly[(i+1)%n]
        dp=a*p[0]+b*p[1]+c; dq=a*q[0]+b*q[1]+c
        if dp>=-EPS: out.append(p)
        if (dp>EPS and dq<-EPS) or (dp<-EPS and dq>EPS):
            t=dp/(dp-dq)
            out.append((p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1])))
    return out

def convex_clip(subject, clipper):
    """intersection of convex polygon `subject` with convex polygon `clipper`"""
    if len(clipper)<3 or len(subject)<3: return []
    # make clipper CCW
    if poly_area(clipper)<0: clipper=clipper[::-1]
    poly=subject
    n=len(clipper)
    for i in range(n):
        x1,y1=clipper[i]; x2,y2=clipper[(i+1)%n]
        # inside = left of (x1,y1)->(x2,y2):  cross >= 0
        a = y1-y2; b = x2-x1; c = x1*y2 - x2*y1
        # a*x+b*y+c = (x2-x1)*(y-y1) - (y2-y1)*(x-x1)  ... check sign
        poly = clip_halfplane(poly, a, b, c)
        if not poly: return []
    return poly

def mirror_pt(p, A, B, C):
    """reflect across line A*x+B*y+C=0 (A,B not both 0)"""
    d = (A*p[0]+B*p[1]+C)/(A*A+B*B)
    return (p[0]-2*A*d, p[1]-2*B*d)

def solve(pts, xa,ya,xb,yb):
    pts=[(float(x),float(y)) for x,y in pts]
    if poly_area(pts)<0: pts=pts[::-1]
    # line through (xa,ya),(xb,yb):  A x + B y + C = 0
    A = float(yb-ya); B = float(xa-xb); C = float(xb*ya - xa*yb)
    n=len(pts)
    O=(0.0,0.0)
    plus=[]; minus=[]; signs=[]
    for i in range(n):
        p=pts[i]; q=pts[(i+1)%n]
        cr = p[0]*q[1]-q[0]*p[1]
        if abs(cr)<EPS:
            signs.append(0); plus.append([]); minus.append([]); continue
        s = 1 if cr>0 else -1
        tri=[O,p,q]
        signs.append(s)
        plus.append(clip_halfplane(tri, A,B,C))          # side >= 0
        mm = clip_halfplane(tri, -A,-B,-C)               # side <= 0
        minus.append([mirror_pt(z,A,B,C) for z in mm])
    total=0.0
    for i in range(n):
        if signs[i]==0 or len(plus[i])<3: continue
        for j in range(n):
            if signs[j]==0 or len(minus[j])<3: continue
            inter=convex_clip(plus[i], minus[j])
            if len(inter)>=3:
                total += signs[i]*signs[j]*abs(poly_area(inter))
    return total

# ---------- brute force ----------
def point_in_poly(pt, poly):
    x,y=pt; inside=False; n=len(poly)
    for i in range(n):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y):
            xin = x1+(y-y1)*(x2-x1)/(y2-y1)
            if xin>x: inside=not inside
    return inside

def monte(pts, xa,ya,xb,yb, samples=400000, seed=1):
    rnd=random.Random(seed)
    A=float(yb-ya); B=float(xa-xb); C=float(xb*ya-xa*yb)
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    x0,x1=min(xs)-0.5,max(xs)+0.5; y0,y1=min(ys)-0.5,max(ys)+0.5
    cnt=0
    for _ in range(samples):
        x=rnd.uniform(x0,x1); y=rnd.uniform(y0,y1)
        if A*x+B*y+C < 0: continue          # must be on Alob's (>=0) side
        if not point_in_poly((x,y), pts): continue
        m=mirror_pt((x,y),A,B,C)
        if A*m[0]+B*m[1]+C > 0: continue
        if point_in_poly(m, pts): cnt+=1
    return cnt/samples*(x1-x0)*(y1-y0)

def main():
    s1=solve([(0,0),(2,0),(2,2),(0,2)],0,-1,0,3)
    print("sample1", s1); assert abs(s1-0.0)<1e-9
    s2=solve([(0,1),(0,4),(3,6),(7,5),(4,2),(7,0)],5,7,2,0)
    print("sample2", s2); assert abs(s2-9.476048311178)<1e-6
    s3=solve([(-5,0),(-3,-2),(0,1),(3,-2),(5,0),(0,5)],0,0,1,0)
    print("sample3", s3); assert abs(s3-8.0)<1e-9
    print("samples OK")
    # monte carlo cross-checks on the samples and on random star-shaped polygons
    for name,(pp,ln) in [("s2",([(0,1),(0,4),(3,6),(7,5),(4,2),(7,0)],(5,7,2,0))),
                         ("s3",([(-5,0),(-3,-2),(0,1),(3,-2),(5,0),(0,5)],(0,0,1,0)))]:
        m=monte(pp,*ln)
        e=solve(pp,*ln)
        print("  %s exact=%.6f monte=%.4f" % (name,e,m))
        assert abs(e-m)<0.06*max(1,e)
    rnd=random.Random(5)
    worst=0.0
    for t in range(12):
        k=rnd.randint(3,9)
        ang=sorted(rnd.uniform(0,2*math.pi) for _ in range(k))
        pp=[(round(6*math.cos(a),3), round(6*math.sin(a),3)) for a in ang]
        pp=[(x+rnd.uniform(-1,1), y+rnd.uniform(-1,1)) for x,y in pp]   # star-shaped => simple
        ln=(rnd.uniform(-3,3),rnd.uniform(-3,3),rnd.uniform(-3,3),rnd.uniform(-3,3))
        if abs(ln[0]-ln[2])<1e-6 and abs(ln[1]-ln[3])<1e-6: continue
        e=solve(pp,*ln); m=monte(pp,*ln,samples=200000,seed=t)
        d=abs(e-m)
        worst=max(worst,d)
        assert d < 0.35, ("mismatch", pp, ln, e, m)
    print("random star-shaped polygons vs Monte-Carlo: worst abs diff = %.4f" % worst)
    print("landinheritance: OK")

main()
