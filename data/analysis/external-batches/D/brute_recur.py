import sys, itertools
from functools import lru_cache

L = 40  # tail terms to compare

def divisors(m):
    ds=[]
    i=1
    while i*i<=m:
        if m%i==0:
            ds.append(i)
            if i!=m//i: ds.append(m//i)
        i+=1
    return sorted(ds)

DIV = {}

def compositions(t):
    # yield tuples of positive ints summing to t
    if t==0:
        yield ()
        return
    for first in range(1,t+1):
        for rest in compositions(t-first):
            yield (first,)+rest

def tail(k,c,a,L=L):
    seq=list(a)
    out=[]
    while len(out)<L:
        nxt=sum(c[i]*seq[i] for i in range(k))
        seq=seq[1:]+[nxt]
        out.append(nxt)
    return tuple(out)

def gen(T):
    items=[]
    for t in range(1,T+1):
        for comp in compositions(t):
            k=len(comp)
            choices=[]
            for m in comp:
                if m not in DIV: DIV[m]=divisors(m)
                choices.append([(d,m//d) for d in DIV[m]])
            for pick in itertools.product(*choices):
                c=tuple(p[0] for p in pick)
                a=tuple(p[1] for p in pick)
                items.append((k,c,a))
    return items

if __name__=="__main__":
    T=int(sys.argv[1]) if len(sys.argv)>1 else 10
    items=gen(T)
    print("count objects with t1<=%d: %d"%(T,len(items)), file=sys.stderr)
    keyed=[]
    for (k,c,a) in items:
        keyed.append((tail(k,c,a), c, k, a))
    keyed.sort(key=lambda x:(x[0],x[1]))
    for idx in [1,2,3,4,5,6,7,8,9,10]:
        tl,c,k,a=keyed[idx-1]
        print(idx, "k=",k,"c=",c,"a=",a,"tail=",tl[:10])
    if len(keyed)>=1235:
        tl,c,k,a=keyed[1234]
        print(1235,"k=",k,"c=",c,"a=",a,"tail=",tl[:10])
