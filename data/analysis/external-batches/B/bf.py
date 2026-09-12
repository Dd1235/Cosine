from collections import deque
import sys

def state_after_k(n,k):
    """Return (peg1,peg2,peg3) bottom-to-top after k optimal moves of n-disk Hanoi 1->3."""
    pegs={1:[],2:[],3:[]}
    f,t,a=1,3,2
    for i in range(n,0,-1):
        b=(k>>(i-1))&1
        if b==0:
            pegs[f].append(i)
            f,t,a=f,a,t
        else:
            pegs[t].append(i)
            f,t,a=a,t,f
    # stacks were appended largest-first => bottom to top already sorted desc
    return tuple(tuple(pegs[r]) for r in (1,2,3))

def son_move(st):
    p1,p2,p3=st
    return ((),p2,p3+p1)

def bfs(start,n):
    goal=((),(),tuple(range(n,0,-1)))
    if start==goal: return 0
    dist={start:0}
    q=deque([start])
    while q:
        s=q.popleft(); d=dist[s]
        for i in range(3):
            if not s[i]: continue
            top=s[i][-1]
            for j in range(3):
                if i==j: continue
                if s[j] and s[j][-1]<top: continue
                ns=list(s); 
                ns[i]=s[i][:-1]; ns[j]=s[j]+(top,)
                ns=tuple(ns)
                if ns not in dist:
                    dist[ns]=d+1
                    if ns==goal: return d+1
                    q.append(ns)
    return None

if __name__=="__main__":
    for n in range(1,9):
        for k in range(0,2**n):
            st=state_after_k(n,k)
            # sanity: sorted stacks
            for p in st: assert list(p)==sorted(p,reverse=True), (n,k,st)
            y=son_move(st)
            ans=bfs(y,n)
            print(n,bin(k)[2:],ans,bin(ans)[2:] if ans is not None else None)
