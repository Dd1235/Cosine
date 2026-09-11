"""Official reference counting transcription vs exhaustive statement oracle, n<=8."""
import itertools,math,collections

def formula(n):
 groups=collections.defaultdict(list)
 for i in range(1,n):
  x=i*(i+1);ps=[];p=2
  while p*p<=x:
   if x%p==0:
    ps.append(p)
    while x%p==0:x//=p
   p+=1
  if x>1:ps.append(x)
  ds=[(1,1)]
  for p in ps:ds += [(d*p,-s) for d,s in ds]
  for d,s in ds[1:]:groups[d,s].append(i)
 ans=1
 for (d,mu),es in groups.items():
  ways=math.factorial(n)//math.factorial(n-n//d)
  l=0
  while l<len(es):
   r=l+1
   while r<len(es) and es[r]==es[r-1]+1:r+=1
   cnt=[0,0]
   for k in range(es[l],es[r-1]+2):
    if k%d:cnt[k%2]+=1
   ways*=math.comb(sum(cnt),cnt[0]);l=r
  ans-=mu*(ways-1)
 return ans

def brute(n):
 total=0
 for p in itertools.permutations(range(n)):
  for d in range(2,n+2):
   a=[v for i,v in enumerate(p,1) if i%d]
   if all(x<y for x,y in zip(a,a[1:])):total+=1;break
 return total
for n in range(1,9):
 a,b=formula(n),brute(n);assert a==b,(n,a,b);print(n,a)
