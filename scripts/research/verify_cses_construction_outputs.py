"""Independent output validators; compile cited external author implementations separately."""
import random,subprocess,itertools,collections,json,time
import argparse
parser=argparse.ArgumentParser(description='Validate emitted paths/moves from external CSES reference binaries; does not prove NO answers.')
parser.add_argument('--grid-binary',required=True)
parser.add_argument('--letter-binary',required=True)
args=parser.parse_args()
random.seed(532)
cases=[]
for n in range(1,6):
 for m in range(1,6):
  for a in range(n*m):
   for b in range(a+1,n*m):cases.append((n,m,a//m,a%m,b//m,b%m))
for _ in range(500):
 n=random.randint(1,50);m=random.randint(1,50)
 if n*m<2:continue
 a,b=random.sample(range(n*m),2);cases.append((n,m,a//m,a%m,b//m,b%m))
s=str(len(cases))+'\n'+'\n'.join(' '.join(map(str,[n,m,y+1,x+1,v+1,u+1])) for n,m,y,x,v,u in cases)+'\n'
out=subprocess.check_output([args.grid_binary],input=s.encode()).decode().splitlines();it=iter(out);yes=0
for n,m,y,x,v,u in cases:
 if next(it)=='NO':continue
 path=next(it);seen={(y,x)};assert len(path)==n*m-1
 for ch in path:
  dy,dx={'U':(-1,0),'D':(1,0),'L':(0,-1),'R':(0,1)}[ch];y+=dy;x+=dx
  assert 0<=y<n and 0<=x<m and (y,x) not in seen,(n,m,path)
  seen.add((y,x))
 assert (y,x)==(v,u);yes+=1
print('2418',len(cases),'cases',yes,'valid YES paths; NO answers not independently checked')
count=0;maxmoves=0
for n in list(range(1,7))+[20,50,100]:
 for trial in range(40):
  letters=list('A'*(n-1)+'B'*(n-1));random.shuffle(letters);p=random.randrange(2*n-1);s=''.join(letters[:p])+ '..'+''.join(letters[p:]);old=s
  out=subprocess.check_output([args.letter_binary],input=f'{n}\n{s}\n'.encode()).decode().splitlines();k=int(out[0]);count+=1
  if k<0:
   assert n<=3;continue
  assert k<=1000 and len(out)==k+1;maxmoves=max(maxmoves,k)
  for new in out[1:]:
   p=old.index('..');q=new.index('..');assert abs(p-q)>=2
   expected=list(old);expected[p:p+2]=old[q:q+2];expected[q:q+2]='..';assert ''.join(expected)==new;old=new
  assert old.replace('.','')=='A'*(n-1)+'B'*(n-1)
print('2427',count,'cases maxmoves',maxmoves)
