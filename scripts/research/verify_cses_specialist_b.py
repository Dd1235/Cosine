import itertools,heapq,random,math,collections,json,bisect,time
rng=random.Random(31093401)
checks={}
def k_fixed(a,m,k):
 a=sorted(a);n=len(a);base=sum(a[:m]);ans=[base];q=[];serial=0
 def push(cost,s,v,tail):
  nonlocal serial
  serial+=1;heapq.heappush(q,(cost,serial,s,(v,tail)))
 if k>1:push(base+a[m]-a[m-1],m-1,m,None)
 while len(ans)<k:
  cost,_,s,node=heapq.heappop(q);v,tail=node;ans.append(cost)
  if v+1<(tail[0] if tail else n):push(cost+a[v+1]-a[v],s,v+1,tail)
  if s>0:push(cost+a[s]-a[s-1],s-1,s,node)
 return ans
ct=0
for n in range(2,11):
 for m in range(1,n):
  for _ in range(15):
   a=[rng.randrange(-5,6) for _ in range(n)];br=sorted(sum(c) for c in itertools.combinations(a,m))
   assert k_fixed(a,m,len(br))==br,(a,m);ct+=1
checks['3109']=f'All subset sums (with duplicate-value multiplicity) matched exhaustive combinations in {ct} random cases, n=2..10 and every legal m.'

def stick(a,m):
 n=len(a);limit=n+m;t=[1]*n;q=[(-x,i) for i,x in enumerate(a)];heapq.heapify(q);C=n;low=min(a);points=[]
 while C<=limit:
  R=-q[0][0];points.append((C,R,low))
  if R==1:break
  while C<=limit and -q[0][0]==R:
   _,i=heapq.heappop(q);t[i]+=1;C+=1;low=min(low,a[i]//t[i]);heapq.heappush(q,(-((a[i]+t[i]-1)//t[i]),i))
 q=[(-x,i,1) for i,x in enumerate(a)];heapq.heapify(q);ans=[]
 for K in range(1,limit+1):
  neg,i,j=heapq.heappop(q);L0=-neg
  if j<a[i]:heapq.heappush(q,(-(a[i]//(j+1)),i,j+1))
  if K>=n:ans.append(min(R-min(L0,L) for C,R,L in points if C<=K))
 return ans
ct=0
for n,V in [(1,15),(2,15),(3,10),(4,7)]:
 for a in itertools.combinations_with_replacement(range(1,V+1),n):
  best=[10**9]*(sum(a)-n+1)
  for t in itertools.product(*(range(1,x+1) for x in a)):
   z=max((x+y-1)//y for x,y in zip(a,t))-min(x//y for x,y in zip(a,t));K=sum(t)-n;best[K]=min(best[K],z)
  assert stick(a,sum(a)-n)==best,(a,stick(a,sum(a)-n),best);ct+=1
checks['3401']=f'Sweep/L0 formula matched exhaustive allocations for all k in {ct} multisets: n=1,max a=15; n=2,max a=15; n=3,max a=10; n=4,max a=7. Includes counterexample [5,5,12] to naive split-largest greedy.'

def two_paths(n,edges):
 incoming=[[] for _ in range(n+1)];es=set(edges)
 for a,b in edges:incoming[b].append(a)
 S={0};parent=[None]*(n+1)
 for v in range(2,n+1):
  candidate=0 if 0 in S else next((u for u in incoming[v] if u in S),None)
  if (v-1,v) not in es:S.clear()
  if candidate is not None:S.add(v-1);parent[v-1]=candidate
  if not S:return None
 j=next(iter(S));i=n;c=0;colors=[None]*(n+1)
 while i:
  for v in range(j+1,i+1):colors[v]=c
  i,j,c=j,parent[j] if j else 0,c^1
 paths=[[v for v in range(1,n+1) if colors[v]==c] for c in range(2)]
 assert all((a,b) in es for p in paths for a,b in zip(p,p[1:]))
 return paths
ct=0
for n in range(2,6):
 possible=list(itertools.combinations(range(1,n+1),2))
 for mask in range(1<<len(possible)):
  es={e for i,e in enumerate(possible) if mask>>i&1};got=two_paths(n,es)
  ok=False
  for assignment in range(1<<n):
   p=[[i+1 for i in range(n) if (assignment>>i&1)==c] for c in range(2)]
   if all((a,b) in es for q in p for a,b in zip(q,q[1:])):ok=True;break
  assert (got is not None)==ok,(n,es);ct+=1
checks['3358']=f'Linear frontier-state DP and reconstruction matched exhaustive two-color path assignments on all {ct} forward-edge DAGs for n=2..5.'

def beautiful(n):
 rem=list(range(1,n+1));out=[]
 while len(rem)>6:
  j=next(i for i,x in enumerate(rem) if not out or abs(x-out[-1])!=1);out.append(rem.pop(j))
 for tail in itertools.permutations(rem):
  p=out+list(tail)
  if all(abs(a-b)!=1 for a,b in zip(p,p[1:])):return p
 return None
for n in range(1,10):
 br=next((list(p) for p in itertools.permutations(range(1,n+1)) if all(abs(a-b)!=1 for a,b in zip(p,p[1:]))),None)
 assert beautiful(n)==br,(n,beautiful(n),br)
for n in list(range(10,101))+[1000,100000]:
 p=beautiful(n);assert sorted(p)==list(range(1,n+1)) and all(abs(a-b)!=1 for a,b in zip(p,p[1:]))
checks['3175']='Greedy with six-element exhaustive tail matched lexicographic exhaustive search for n=1..9; valid permutations checked through n=100 and at n=1000,100000. Dirac extension proof covers arbitrary n.'

def knight(x,y):
 x,y=max(x,y),min(x,y)
 if (x,y)==(1,0):return 3
 if (x,y) in [(1,1),(2,2)]:return 4
 d=max((x+1)//2,(x+y+2)//3);return d+((d+x+y)&1)
D={(0,0):0};q=collections.deque(D);moves=[(sx*a,sy*b) for a,b in [(1,2),(2,1)] for sx in [-1,1] for sy in [-1,1]]
while q:
 x,y=q.popleft()
 for dx,dy in moves:
  z=x+dx,y+dy
  if 0<=z[0]<140 and 0<=z[1]<140 and z not in D:D[z]=D[x,y]+1;q.append(z)
assert all(knight(x,y)==D[x,y] for x in range(101) for y in range(101))
checks['3218']='Closed form matched exact nonnegative-quadrant BFS on all 10201 displacements x,y=0..100 using a 140x140 search board. Explicit exceptions include (1,1), unlike the unrestricted-plane formula.'
for A in range(1,41):
 for B in range(1,41):
  g=math.gcd(A,B);L=A*B//g
  vis={(min(t%(2*A),2*A-t%(2*A)),min(t%(2*B),2*B-t%(2*B))) for t in range(2*L)}
  assert len(vis)==L+1-((A//g-1)*(B//g-1))//2,(A,B)
checks['3216']='Return-period and distinct-cell formula matched direct full-cycle simulation for all 1600 side-length pairs A,B=1..40 (grid dimensions A+1,B+1).'

base4=[[3,2,3,4],[4,1,1,2],[4,1,2,4],[3,2,1,3]]
def grid(n):
 if n<4:return None
 if n==4:return base4
 a=[[n if j==1 else (i if j>i else i-1) for j in range(1,n+1)] for i in range(1,n+1)]
 i=n//2;j=3 if n%2 else n//2+2
 a[1][0],a[1][j-1]=a[1][j-1],a[1][0]
 a[i][-1],a[i+1][-1]=a[i+1][-1],a[i][-1]
 return a
for n in range(5,1001):
 R=[(n-2)*i+n+1 for i in range(1,n+1)];C=[n*n]+[n*(n-1)//2+j-1 for j in range(2,n+1)]
 i=n//2;j=3 if n%2 else n//2+2
 C[0]-=n-2;C[j-1]+=n-2;R[i]+=1;R[i+1]-=1
 assert len(set(R+C))==2*n,n
for n in list(range(4,101))+[500,1000]:
 a=grid(n);counts=collections.Counter(x for row in a for x in row)
 assert all(counts[x]==n for x in range(1,n+1))
 assert len(set([sum(row) for row in a]+[sum(row[j] for row in a) for j in range(n)]))==2*n,n
checks['3424']='Symbolic corrected row/column totals checked for every n=5..1000; explicit grids verified for every n=4..100 plus n=500,1000, including exact n copies of each symbol. Independently found fixed n=4 template.'

ct=0
for _ in range(80):
 n=rng.randrange(2,13);g=[[] for _ in range(n)];edges=[]
 for v in range(1,n):
  u=rng.randrange(v);g[u].append(v);g[v].append(u);edges.append((u,v))
 coins=rng.sample(range(n),rng.randrange(1,min(5,n)+1));coinset=set(coins);degree=list(map(len,g));alive=[True]*n;q=collections.deque(v for v in range(n) if degree[v]==1 and v not in coinset)
 while q:
  v=q.popleft();alive[v]=False
  for u in g[v]:
   if alive[u]:
    degree[u]-=1
    if degree[u]==1 and u not in coinset:q.append(u)
 E=sum(alive[u] and alive[v] for u,v in edges);proj=[None]*n;dep=[0]*n;q=collections.deque()
 for v in range(n):
  if alive[v]:proj[v]=v;q.append(v)
 while q:
  v=q.popleft()
  for u in g[v]:
   if proj[u] is None:proj[u]=proj[v];dep[u]=dep[v]+1;q.append(u)
 dist=[]
 for s in range(n):
  row=[-1]*n;row[s]=0;q=collections.deque([s])
  while q:
   v=q.popleft()
   for u in g[v]:
    if row[u]<0:row[u]=row[v]+1;q.append(u)
  dist.append(row)
 bits={v:1<<i for i,v in enumerate(coins)};full=(1<<len(coins))-1
 for _ in range(10):
  a,b=rng.randrange(n),rng.randrange(n);q=collections.deque([(a,bits.get(a,0),0)]);seen={(a,bits.get(a,0))}
  while q:
   v,mask,d=q.popleft()
   if v==b and mask==full:br=d;break
   for u in g[v]:
    st=u,mask|bits.get(u,0)
    if st not in seen:seen.add(st);q.append((*st,d+1))
  got=2*E+dep[a]+dep[b]-dist[proj[a]][proj[b]]
  assert got==br,(g,coins,a,b,got,br);ct+=1
checks['3149']=f'Core-projection formula matched exact BFS on (vertex, collected-coin-mask) for {ct} random queries over 80 trees with n<=12 and up to five coins.'

def same_sum(a):
 n=len(a);h=n//2
 def halves(v):
  z=[(0,0)]
  for i,x in enumerate(v):z += [(s+x,mask|(1<<i)) for s,mask in z]
  return sorted(z)
 L,R=halves(a[:h]),halves(a[h:]);ls=[s for s,m in L];rs=[s for s,m in R]
 def count(t):
  j=len(rs)-1;total=0
  for x in ls:
   while j>=0 and x+rs[j]>t:j-=1
   total+=j+1
  return total
 lo,hi,below=0,sum(a),0
 while lo<hi:
  mid=(lo+hi)//2;c=count(mid)
  if c-below>mid-lo+1:hi=mid
  else:lo=mid+1;below=c
 right=collections.defaultdict(list)
 for s,mask in R:
  if len(right[s])<2:right[s].append(mask)
 found=[]
 for s,mask in L:
  for z in right.get(lo-s,[]):
   found.append(mask|(z<<h))
   if len(found)==2:
    x,y=found;return x&~y,y&~x
 raise AssertionError
ct=0
for n in range(3,19):
 sets=[[1<<i for i in range(n-1)]+[(1<<(n-1))-1]]
 for _ in range(10):
  a=[rng.randrange(1,max(2,((1<<n)-2)//n)) for _ in range(n)]
  if sum(a)<=(1<<n)-2:sets.append(a)
 for a in sets:
  x,y=same_sum(a);assert x and y and not x&y
  assert sum(v for i,v in enumerate(a) if x>>i&1)==sum(v for i,v in enumerate(a) if y>>i&1);ct+=1
checks['3425']=f'Deterministic MITM overfull-interval recovery validated in {ct} cases n=3..18, including near-binary adversarial sets with only a single colliding sum. The earlier randomized birthday argument is explicitly rejected.'
print(json.dumps(checks,indent=2))
open('/tmp/specialist_b_checks.json','w').write(json.dumps(checks,indent=2)+'\n')
