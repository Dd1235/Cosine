import sys
from functools import lru_cache
sys.setrecursionlimit(10000)

def divisors(t):
    r=[]
    i=1
    while i*i<=t:
        if t%i==0:
            r.append(i)
            if i!=t//i: r.append(t//i)
        i+=1
    return sorted(r)

def gen_all(M):
    """all (c,a) with sum c_i a_i <= M"""
    out=[]
    def rec(rem, c, a):
        # optionally stop here (k=len(c)) if rem==0
        if c and rem>=0:
            pass
        for t in range(1, rem+1):
            for cv in divisors(t):
                av=t//cv
                c.append(cv); a.append(av)
                if rem-t==0:
                    out.append((tuple(c),tuple(a)))
                rec(rem-t, c, a)
                c.pop(); a.pop()
    # we want sum exactly m for each m<=M -> easier: for each m
    res=[]
    for m in range(1,M+1):
        out=[]
        def rec2(rem,c,a):
            if rem==0:
                res.append((tuple(c),tuple(a)))
                return
            for t in range(1,rem+1):
                for cv in divisors(t):
                    c.append(cv); a.append(t//cv)
                    rec2(rem-t,c,a)
                    c.pop(); a.pop()
        rec2(m,[],[])
    return res

def tail(c,a,L=70):
    k=len(c)
    seq=list(a)
    while len(seq)<k+L:
        seq.append(sum(c[i]*seq[len(seq)-k+i] for i in range(k)))
    return tuple(seq[k:k+L])

M=9
alls=gen_all(M)
print("count",len(alls))
items=[]
for c,a in alls:
    items.append((tail(c,a),c,a))
items.sort(key=lambda x:(x[0],x[1]))
for idx in [1,2,3,4,5,1235]:
    t,c,a=items[idx-1]
    print("n=",idx,"k=",len(c),"c=",c,"a=",a,"gen=",t[:10])
