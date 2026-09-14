"""Partial Gym106179F research: exact BFS operation-sequence oracle.
Verifies the minimum-length lemma; it does NOT solve scalable sequence counting.
"""
from collections import deque
from itertools import product

def counts(a):
    return [sum(x>v for x in a[:i]) for i,v in enumerate(a)]

def gap(a):
    f=sorted(counts(a))
    return f[-1]-f[-2]

def oracle(a):
    dist={a:0};ways={a:1};q=deque([a]);best=None;answer=0
    while q:
        s=q.popleft();d=dist[s]
        if best is not None and d>best:break
        if gap(s)==0:
            best=d;answer+=ways[s];continue
        for i in range(len(s)-1):
            t=list(s);t[i],t[i+1]=t[i+1],t[i];t=tuple(t)
            if t not in dist:dist[t]=d+1;ways[t]=0;q.append(t)
            if dist[t]==d+1:ways[t]+=ways[s]
    return best,answer

if __name__=='__main__':
    total=0
    for n in range(2,7):
        for a in product(range(1,min(n,3)+1),repeat=n):
            distance,ways=oracle(a)
            assert distance==gap(a),(a,distance,gap(a))
            total+=1
    for a,expected in [((1,1),(0,1)),((1,2,1),(1,2)),((2,3,1),(2,2))]:
        assert oracle(a)==expected
    print('PASS',total,'arrays: BFS minimum equals top-two count gap; all three official sample counts pass')
