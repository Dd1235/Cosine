"""Offline independent 0-1 BFS oracle against a derived counting formula. Seed710.
Not a scalable judge solution; run directly with Python3.
"""
import random,itertools,collections,math,json

def brute(n,edges,labels):
 g=[[] for _ in range(n)]
 for (u,v),l in zip(edges,labels):g[u].append((v,l));g[v].append((u,l))
 start=(0,1,1);dist={start:0};q=collections.deque([start])
 while q:
  u,mask,x=q.popleft();d=dist[u,mask,x]
  if u==0 and mask==(1<<n)-1:return d
  for v,l in g[u]:
   if l==x:continue
   z=(v,mask|1<<v,x)
   if z not in dist or dist[z]>d:dist[z]=d;q.appendleft(z)
  if x<n:
   z=u,mask,x+1
   if z not in dist or dist[z]>d+1:dist[z]=d+1;q.append(z)

def predicted(n,edges,labels):
 par=[-1]*n;depth=[0]*n;g=[[] for _ in range(n)]
 for u,v in edges:g[u].append(v);g[v].append(u)
 order=[0]
 for u in order:
  for v in g[u]:
   if v!=par[u]:par[v]=u;depth[v]=depth[u]+1;order.append(v)
 def ancestor(u,v):
  while depth[v]>depth[u]:v=par[v]
  return u==v
 deepest=0;last=0;up=False
 for (u,v),l in sorted(zip(edges,labels),key=lambda t:t[1]):
  u=u if depth[u]>depth[v] else v
  if not ancestor(u,deepest) and not ancestor(deepest,u):return l-1
  if l>1:
   if depth[u]<depth[last]:up=True
   elif up:return l-1
  if depth[u]>depth[deepest]:deepest=u
  last=u
 return n-1

def tail_count(n, edges, c):
 if c >= n:return 0
 g=[[] for _ in range(n)]
 for u,v in edges:g[u].append(v);g[v].append(u)
 depth=[0]*n;parent=[-1]*n;order=[0]
 for u in order:
  for v in g[u]:
   if v!=parent[u]:parent[v]=u;depth[v]=depth[u]+1;order.append(v)
 return 2**(c-1)*math.factorial(n-1-c)*sum(math.comb(d-1,c-1) for d in depth[1:] if d>=c)

random.seed(710)
count=0
for n in range(2,8):
 for trial in range(10):
  edges=[(v,random.randrange(v)) for v in range(1,n)]
  perms=list(itertools.permutations(range(1,n)))
  if len(perms)>80:perms=random.sample(perms,80)
  for labels in perms:
   a=brute(n,edges,labels);b=predicted(n,edges,labels);count+=1
   if a!=b:print('FAIL',n,edges,labels,a,b);raise SystemExit(1)
# Independently aggregate every labeling for small trees and compare the closed form.
for n in range(2,8):
 for trial in range(5):
  edges=[(v,random.randrange(v)) for v in range(1,n)]
  histogram=collections.Counter(brute(n,edges,p) for p in itertools.permutations(range(1,n)))
  for c in range(1,n):
   assert histogram[c] == tail_count(n,edges,c)-tail_count(n,edges,c+1),(n,edges,c,histogram)
print('PASS: 1930 individual traversal checks; 30 exhaustive tree histograms')
