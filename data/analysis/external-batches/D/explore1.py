import itertools
from brute_recur import gen, tail
items=gen(6)
keyed=[]
for (k,c,a) in items:
    keyed.append((tail(k,c,a,20), c, k, a))
keyed.sort(key=lambda x:(x[0],x[1]))
for idx,(tl,c,k,a) in enumerate(keyed,1):
    if tl[0]<=5:
        print("%3d t1=%d k=%d c=%-12s a=%-12s tail=%s"%(idx,tl[0],k,c,a,tl[:6]))
