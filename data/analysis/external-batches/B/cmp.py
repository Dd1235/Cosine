import sys
sys.path.insert(0,'/private/tmp/claude-501/-Users-dedeepya-Cosine/d35bbe98-9789-429d-86f7-c2af7329c583/scratchpad/batchB')
from bf import state_after_k, son_move, bfs
from solver import G
bad=0
for n in range(1,9):
    for k in range(2**n):
        y=son_move(state_after_k(n,k))
        a=bfs(y,n); b=G(tuple(y),2)
        if a!=b:
            bad+=1
            if bad<15: print("MISMATCH",n,bin(k)[2:],a,b,y)
print("bad",bad)
