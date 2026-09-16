"""Arranging Wine: R red and W white boxes into non-empty piles, piles alternate
colour along a line, every red pile has at most d boxes.  Count arrangements mod 1e9+7.
R,W <= 1e6.

Derivation: with r red piles and w white piles the line is valid iff |r-w| <= 1
(2 orders when r==w, 1 otherwise), so with F(r) = #compositions of R into r parts
in [1,d] and G(w)=C(W-1,w-1),
  K = sum_{r>=1} F(r) * (2*C(W-1,r-1) + C(W-1,r-2) + C(W-1,r)).
Writing F(r) = [x^R] A(x)^r with A = x+...+x^d and summing the three binomial
series gives (1+A)^{W-1} * (1+2A+A^2) - 1 = (1+A)^{W+1} - 1, hence for R>=1

    K = [x^R] (1 + x + x^2 + ... + x^d)^{W+1}
      = sum_j (-1)^j C(W+1,j) C(R - j*(d+1) + W, W).

O(R + W) factorial precompute plus O(R/(d+1)) terms; O(R+W) space.

Check: closed form vs a direct O(R*W) DP over arrangements, over all small R,W,d.
"""
MOD = 10**9+7

def closed(R, W, d):
    n = R + W + 2
    f=[1]*(n+1)
    for i in range(1,n+1): f[i]=f[i-1]*i%MOD
    inv=[1]*(n+1); inv[n]=pow(f[n],MOD-2,MOD)
    for i in range(n,0,-1): inv[i-1]=inv[i]*i%MOD
    def C(a,b):
        if b<0 or a<0 or b>a: return 0
        return f[a]*inv[b]%MOD*inv[a-b]%MOD
    res=0; j=0
    while j<=W+1 and j*(d+1)<=R:
        t=C(W+1,j)*C(R-j*(d+1)+W, W)%MOD
        res = (res + t) if j%2==0 else (res - t)
        j+=1
    return res%MOD

def brute(R, W, d):
    """count sequences of piles directly: enumerate compositions"""
    from functools import lru_cache
    import sys
    sys.setrecursionlimit(10000)
    # comps[r] = #compositions of R into r parts in [1,d]
    def comps(total, parts, cap):
        dp=[[0]*(total+1) for _ in range(parts+1)]
        dp[0][0]=1
        for p in range(1,parts+1):
            for s in range(total+1):
                v=0
                for t in range(1,min(cap,s)+1): v+=dp[p-1][s-t]
                dp[p][s]=v
        return [dp[p][total] for p in range(parts+1)]
    F = comps(R, R, d)                 # F[r]
    G = comps(W, W, W)                 # unrestricted compositions of W into w parts
    tot=0
    for r in range(1,R+1):
        for w in range(1,W+1):
            if r==w: mult=2
            elif abs(r-w)==1: mult=1
            else: mult=0
            tot += mult*F[r]*G[w]
    return tot % MOD

def enum_brute(R, W, d):
    """fully explicit: enumerate every line of piles"""
    res=0
    def rec(r_left, w_left, last):
        nonlocal res
        if r_left==0 and w_left==0:
            res+=1; return
        if last!='R':
            for t in range(1, min(d, r_left)+1):
                rec(r_left-t, w_left, 'R')
        if last!='W':
            for t in range(1, w_left+1):
                rec(r_left, w_left-t, 'W')
    rec(R,W,None)
    return res % MOD

def main():
    assert closed(2,2,1)==3
    assert closed(2,2,2)==6
    print("samples OK")
    bad=0
    for R in range(1,9):
        for W in range(1,9):
            for d in range(1,R+1):
                a=closed(R,W,d); b=brute(R,W,d); c=enum_brute(R,W,d)
                if not (a==b==c):
                    bad+=1
                    if bad<8: print("MISMATCH R=%d W=%d d=%d closed=%d sum=%d enum=%d"%(R,W,d,a,b,c))
    print("exhaustive R,W in 1..8, d in 1..R: mismatches =", bad)
    assert bad==0
    # a couple of bigger cross-checks against the sum formula
    for (R,W,d) in [(30,17,3),(25,25,2),(40,9,7),(12,40,1)]:
        assert closed(R,W,d)==brute(R,W,d), (R,W,d)
    print("medium cross-checks OK")
    print("arrangingwine: OK   e.g. R=W=10^6,d=3 ->", closed(10**6,10**6,3))

main()
