import subprocess,random,itertools,math,time,json
rng=random.Random(846231)
def run(exe,inp):return subprocess.check_output([exe],input=inp.encode(),timeout=15).decode().split()
# Every dimension, batches matching the statement's t<=100 limit.
t0=time.perf_counter();cnt=0
for n in range(1,101):
 cases=[(n,m) for m in range(1,101)];out=iter(run('/private/tmp/trominos_c','100\n'+''.join(f'{a} {b}\n' for a,b in cases)))
 for a,b in cases:
  status=next(out);expected=a*b%3==0 and min(a,b)>1 and not(a%2 and b%2 and min(a,b)==3)
  assert (status=='YES')==expected,(a,b,status)
  if status=='NO':continue
  grid=[next(out) for _ in range(a)];assert all(len(s)==b for s in grid)
  seen=set()
  for i in range(a):
   for j in range(b):
    if (i,j) in seen:continue
    todo=[(i,j)];seen.add((i,j));comp=[]
    for x,y in todo:
     comp.append((x,y))
     for u,v in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
      if 0<=u<a and 0<=v<b and (u,v) not in seen and grid[u][v]==grid[x][y]:seen.add((u,v));todo.append((u,v))
    assert len(comp)==3 and len({x for x,y in comp})==len({y for x,y in comp})==2,(a,b,comp)
  cnt+=1
print('trominos 10000 dimension pairs verified; successful grids',cnt,'seconds',time.perf_counter()-t0,flush=True)
# Strong connectivity and minimum edge count; independent reachability oracle for small graphs.
def reach(n,edges,s,reverse=False):
 adj=[[] for _ in range(n)]
 for u,v in edges:adj[v if reverse else u].append(u if reverse else v)
 seen={s};todo=[s]
 for u in todo:
  for v in adj[u]:
   if v not in seen:seen.add(v);todo.append(v)
 return seen
for z in range(1500):
 n=rng.randrange(2,25);edges=[(u,v) for u in range(n) for v in range(n) if rng.random()<.09]
 if not edges:edges=[(0,0)]
 rr=[reach(n,edges,i) for i in range(n)];ids=[-1]*n;c=0
 for i in range(n):
  if ids[i]<0:
   for j in range(n):
    if j in rr[i] and i in rr[j]:ids[j]=c
   c+=1
 ins=[0]*c;outs=[0]*c
 for u,v in edges:
  if ids[u]!=ids[v]:ins[ids[v]]=1;outs[ids[u]]=1
 optimum=0 if c==1 else max(ins.count(0),outs.count(0))
 out=list(map(int,run('/private/tmp/routes_c',f'{n} {len(edges)}\n'+''.join(f'{u+1} {v+1}\n' for u,v in edges))))
 assert out[0]==optimum and len(out)==1+2*optimum
 added=[(out[i]-1,out[i+1]-1) for i in range(1,len(out),2)]
 assert len(reach(n,edges+added,0))==len(reach(n,edges+added,0,True))==n
print('routes 1500 random directed graphs verified against independent SCC/minimum oracle',flush=True)
# Completion: enumerate permutation pairs satisfying independently generated partial permutations.
for n in range(2,7):
 perms=list(itertools.permutations(range(n)))
 for z in range(35):
  p=list(rng.choice(perms));q=list(rng.choice(perms));grid=[['.']*n for _ in range(n)]
  for i in range(n):
   if rng.random()<.5:grid[i][p[i]]='A'
  for i in range(n):
   if rng.random()<.5 and grid[i][q[i]]=='.':grid[i][q[i]]='B'
  pp=[p for p in perms if all('A' not in grid[i] or grid[i][p[i]]=='A' for i in range(n))]
  qq=[q for q in perms if all('B' not in grid[i] or grid[i][q[i]]=='B' for i in range(n))]
  expected=sum(all(p[i]!=q[i] for i in range(n)) for p in pp for q in qq)
  got=int(run('/private/tmp/completion_c',str(n)+'\n'+'\n'.join(map(''.join,grid))+'\n')[0]);assert got==expected,(n,grid,got,expected)
print('completion 175 partial grids n=2..6 checked against permutation-pair enumeration',flush=True)
