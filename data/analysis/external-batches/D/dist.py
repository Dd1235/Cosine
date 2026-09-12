import itertools, sys
from collections import Counter
sys.setrecursionlimit(10000)

def divisors(m):
    ds=[]; i=1
    while i*i<=m:
        if m%i==0:
            ds.append(i)
            if i!=m//i: ds.append(m//i)
        i+=1
    return sorted(ds)
DIV={m:divisors(m) for m in range(1,40)}

def comps(t):
    if t==0:
        yield (); return
    for first in range(1,t+1):
        for rest in comps(t-first):
            yield (first,)+rest

def tailpref(k,c,a,L):
    seq=list(a); out=[]
    for _ in range(L):
        nxt=sum(c[i]*seq[i] for i in range(k))
        seq=seq[1:]+[nxt]; out.append(nxt)
    return tuple(out)

for t in range(6,18):
    c2=Counter(); c3=Counter(); c4=Counter(); tot=0
    for comp in comps(t):
        k=len(comp)
        choices=[[(d,m//d) for d in DIV[m]] for m in comp]
        for pick in itertools.product(*choices):
            c=tuple(p[0] for p in pick); a=tuple(p[1] for p in pick)
            tl=tailpref(k,c,a,4)
            tot+=1
            c2[tl[1]]+=1; c3[tl[1:3]]+=1; c4[tl[1:4]]+=1
    print("t1=%2d N=%9d  distinct_t2=%4d max_t2bucket=%9d (%.4f)  max_t3=%8d (%.5f) max_t4=%7d (%.6f) maxt2val=%d"%(
        t,tot,len(c2),max(c2.values()),max(c2.values())/tot,max(c3.values()),max(c3.values())/tot,
        max(c4.values()),max(c4.values())/tot, max(c2)))
