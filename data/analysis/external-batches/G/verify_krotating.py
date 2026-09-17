"""K-Rotating: N classes / N teachers (teacher i starts in class i), M weeks,
Q <= 1e5 mixed operations.  "0 K x p1..pK" inserts, at week x, the rotation that
moves teacher p_i into the class p_{i+1} currently occupies (p_K takes p_1's);
"1 d x" asks which class teacher d has in week x, counting every plan inserted SO
FAR whose week is <= x.  K <= 10, weeks are distinct.

Algebra: a rotation is the near-identity permutation rho with rho(p_i)=p_{i+1},
rho(p_K)=p_1, and new_pos = old_pos o rho, so pos_x = rho_{w1} o ... o rho_{wk}
over the weeks w1<...<=x in INCREASING order.  Evaluating at one teacher therefore
means applying the rotations from the LATEST week down to the earliest.

Fast solution: sqrt decomposition over the week axis.  Blocks of B weeks each store
the composed permutation of their plans as a SPARSE map (support <= B*K).  A query
applies the plans of x's own block individually and then one O(1) map lookup per
earlier block: O(B + M/B).  An insertion rebuilds one block: O(B*K).  With
B ~ sqrt(M/K) both are O(sqrt(M*K)), so O(Q*sqrt(M*K)) time and O(M + Q*K) space.

Check: both samples, and the sqrt structure against a naive replay of all plans for
random operation streams.
"""
import random
from math import isqrt

class Naive:
    def __init__(self, N, M):
        self.N=N; self.M=M; self.plans={}      # week -> rho dict
    def add(self, x, p):
        rho={}
        K=len(p)
        for i in range(K): rho[p[i]] = p[(i+1)%K]
        self.plans[x]=rho
    def query(self, d, x):
        v=d
        for w in sorted([w for w in self.plans if w<=x], reverse=True):
            v=self.plans[w].get(v, v)
        return v

class Sqrt:
    def __init__(self, N, M, K=10):
        self.N=N; self.M=M
        self.B=max(1, isqrt(max(1, M//K)))
        self.nb=(M+self.B-1)//self.B
        self.plans=[dict() for _ in range(self.nb)]   # block -> {week: rho}
        self.comp=[dict() for _ in range(self.nb)]    # block -> composed sparse perm
    def rebuild(self, b):
        cur={}
        for w in sorted(self.plans[b]):
            rho=self.plans[b][w]
            # cur <- cur o rho   :  h(t) = cur(rho(t))
            new=dict(cur)
            for t, r in rho.items():
                new[t]=cur.get(r, r)
            cur=new
        cur={t:v for t,v in cur.items() if t!=v}
        self.comp[b]=cur
    def add(self, x, p):
        rho={}
        K=len(p)
        for i in range(K): rho[p[i]]=p[(i+1)%K]
        b=(x-1)//self.B
        self.plans[b][x]=rho
        self.rebuild(b)
    def query(self, d, x):
        v=d
        b=(x-1)//self.B
        for w in sorted([w for w in self.plans[b] if w<=x], reverse=True):
            v=self.plans[b][w].get(v, v)
        for bb in range(b-1, -1, -1):
            c=self.comp[bb]
            if c: v=c.get(v, v)
        return v

def run(ops, N, M, cls):
    s=cls(N,M); out=[]
    for op in ops:
        if op[0]==0: s.add(op[1], op[2])
        else: out.append(s.query(op[1], op[2]))
    return out

def main():
    ops1=[(1,3,4),(0,2,[3,2]),(1,3,2),(1,2,4),(1,1,4)]
    assert run(ops1,3,4,Sqrt)==[3,2,3,1], run(ops1,3,4,Sqrt)
    ops2=[(1,3,4),(0,2,[3,2]),(1,3,2),(0,3,[3,1,2]),(1,2,4),(1,1,4)]
    assert run(ops2,3,4,Sqrt)==[3,2,2,3], run(ops2,3,4,Sqrt)
    print("samples OK")
    random.seed(21); bad=0
    for t in range(200):
        N=random.randint(2,8); M=random.randint(1,12)
        used=set(); ops=[]
        for _ in range(random.randint(1,25)):
            if random.random()<0.5 and len(used)<M:
                x=random.choice([w for w in range(1,M+1) if w not in used]); used.add(x)
                K=random.randint(2,min(10,N))
                p=random.sample(range(1,N+1),K)
                ops.append((0,x,p))
            else:
                ops.append((1,random.randint(1,N),random.randint(1,M)))
        a=run(ops,N,M,Sqrt); b=run(ops,N,M,Naive)
        if a!=b:
            bad+=1
            if bad<4: print("MISMATCH",N,M,ops,a,b)
    print("sqrt vs naive on random streams: mismatches =", bad)
    assert bad==0
    # bijection sanity: after any prefix of plans the map teacher->class is a permutation
    random.seed(5)
    for t in range(30):
        N=random.randint(2,9); M=random.randint(11,15)
        s=Sqrt(N,M); nv=Naive(N,M); used=set()
        for _ in range(10):
            x=random.choice([w for w in range(1,M+1) if w not in used]); used.add(x)
            K=random.randint(2,min(10,N)); p=random.sample(range(1,N+1),K)
            s.add(x,p); nv.add(x,p)
            for xx in range(1,M+1):
                img=[s.query(d,xx) for d in range(1,N+1)]
                assert sorted(img)==list(range(1,N+1)), (N,M,xx,img)
                assert img==[nv.query(d,xx) for d in range(1,N+1)]
    print("permutation invariant + naive agreement OK")
    print("krotating: OK")

main()
