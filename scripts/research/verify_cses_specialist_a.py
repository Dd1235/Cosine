"""Independent small-instance checks for specialist CSES assessment A.
Run directly. These verify deductions, not the external implementations.
"""
from functools import lru_cache
from itertools import product

@lru_cache(None)
def drain(value, digits, prefix_max):
    """Apply largest-digit subtraction until this suffix borrows; report cost/remainder.
    With no external nonzero prefix, stop at zero instead of borrowing.
    """
    if value == 0 and prefix_max == 0:
        return 0, 0
    if digits == 1:
        cost = 0
        while value >= 0 and (value or prefix_max):
            value -= max(prefix_max, value)
            cost += 1
        return cost, value
    base = 10 ** (digits - 1)
    leading, suffix = divmod(value, base)
    cost = 0
    while leading >= 0:
        steps, remainder = drain(suffix, digits - 1, max(prefix_max, leading))
        cost += steps
        if leading == 0 and prefix_max == 0:
            return cost, remainder
        leading -= 1
        suffix = base + remainder
    return cost, remainder


def buildings(grid):
    n,m=len(grid),len(grid[0]);a=[[0]*(m+1) for _ in range(n+1)];h=[0]*m
    for row in grid:
        h=[old+1 if ch=='.' else 0 for old,ch in zip(h,row)]
        # Independent direct nearest-boundary version of the linear contribution.
        for i,height in enumerate(h):
            l=i-1
            while l>=0 and h[l]>=height:l-=1
            r=i+1
            while r<m and h[r]>height:r+=1
            left,right=sorted((i-l,r-i))
            for width in range(1,left+right):
                ways=min(width,left,left+right-width)
                for y in range(1,height+1):a[y][width]+=ways
    return a


def brute_buildings(grid):
    n,m=len(grid),len(grid[0]);a=[[0]*(m+1) for _ in range(n+1)]
    for top in range(n):
        for bottom in range(top,n):
            for left in range(m):
                for right in range(left,m):
                    if all(grid[y][x]=='.' for y in range(top,bottom+1) for x in range(left,right+1)):
                        a[bottom-top+1][right-left+1]+=1
    return a

if __name__ == '__main__':
    dp=[0]*10001
    for n in range(1,len(dp)):
        dp[n]=1+min(dp[n-int(c)] for c in str(n) if c!='0')
        assert drain(n,len(str(n)),0)[0]==dp[n],n
    print('2174: all n1..10000 match unrestricted digit-choice DP; n=10^18 result',drain(10**18,19,0)[0])
    count=0
    for n,m in [(1,4),(2,3),(3,3)]:
        for chars in product('.*',repeat=n*m):
            grid=[''.join(chars[i*m:(i+1)*m]) for i in range(n)]
            assert buildings(grid)==brute_buildings(grid)
            count+=1
    print('1148: trapezoid counting matches every size on',count,'exhaustive binary grids')
