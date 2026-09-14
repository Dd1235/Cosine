from collections import deque

def phys_bfs(a,b,c,D):
    start=(a,b,c)
    dist={(start,0,0):0}
    q=deque([(start,0,0)])
    while q:
        st,px,py=q.popleft()
        d=dist[(st,px,py)]
        if d==D: continue
        X,Y,Z=st
        for ns,npx,npy in (
            ((Z,Y,X),px+(X+Z),py),   # east
            ((Z,Y,X),px-(X+Z),py),   # west
            ((X,Z,Y),px,py+(Y+Z)),   # north
            ((X,Z,Y),px,py-(Y+Z)),   # south
        ):
            k=(ns,npx,npy)
            if k not in dist:
                dist[k]=d+1
                q.append(k)
    return dist,start

if __name__=='__main__':
    d,st=phys_bfs(3,4,5,6)
    for (x,y,exp) in [(8,0,2),(-8,9,4)]:
        print(x,y,d.get((st,2*x,2*y)),'expected',exp)
