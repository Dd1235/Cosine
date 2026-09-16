r'''Dropping Ball: M x N board (M*N <= 1e5), every cell holds a diagonal wall
'\' or '/'.  Q <= 1e5 queries: flip one wall, or drop a ball at the top of column y
and report the bottom-edge exit column (or -1 if it leaves sideways / gets stuck).

Ball model (derived from the samples): a ball occupying cell (i,j)
  '\'  -> rolls down-right.  If j == N it leaves by the right edge (-1).
          If cell (i,j+1) is '/' the two diagonals meet in a V at the shared bottom
          corner and the ball is STUCK (-1).  Otherwise it enters (i+1, j+1), and if
          i == M it exits the bottom at column j+1.
  '/'  -> mirror image: left edge, V with '\' at (i,j-1), else (i+1, j-1).
This reproduces all five sample answers, including the -1 caused by flipping (4,4)
which lies OFF the ball's path and only creates the V.

Fast solution: sqrt decomposition on ROWS.  If M <= N just simulate, O(M) <=
O(sqrt(MN)) per drop.  Otherwise (M > N, so N < sqrt(MN)) cut the rows into blocks
of B = max(1, isqrt(M/N)) rows and precompute, per block, entry column -> (exit
column | dead) in O(B*N); a drop walks M/B blocks and a flip rebuilds one block,
both O(sqrt(M*N)).  Total O(M*N + Q*sqrt(M*N)) time, O(M*N) space.

Check: sample; block-decomposition answers vs the naive step-by-step simulation on
random boards and random query streams, for many (M,N) shapes.
'''
import random
from math import isqrt

DEAD = -1

def step_sim(grid, M, N, col):
    """naive: returns exit column or -1"""
    i, j = 1, col
    while True:
        ch = grid[i-1][j-1]
        if ch == '\\':
            if j == N: return -1
            if grid[i-1][j] == '/': return -1
            j += 1
        else:
            if j == 1: return -1
            if grid[i-1][j-2] == '\\': return -1
            j -= 1
        i += 1
        if i > M: return j
    # unreachable

class Blocks:
    def __init__(self, grid, M, N):
        self.g = grid; self.M = M; self.N = N
        if M <= N:
            self.B = 0            # simulate directly
            return
        self.B = max(1, isqrt(max(1, M // max(1, N))))
        self.nb = (M + self.B - 1)//self.B
        self.tab = [None]*self.nb
        for b in range(self.nb):
            self.build(b)
    def build(self, b):
        B, M, N, g = self.B, self.M, self.N, self.g
        lo = b*B + 1; hi = min(M, lo + B - 1)
        t = [DEAD]*(N+2)
        for c in range(1, N+1):
            i, j = lo, c
            ok = True
            while i <= hi:
                ch = g[i-1][j-1]
                if ch == '\\':
                    if j == N or g[i-1][j] == '/': ok = False; break
                    j += 1
                else:
                    if j == 1 or g[i-1][j-2] == '\\': ok = False; break
                    j -= 1
                i += 1
            t[c] = j if ok else DEAD
        self.tab[b] = t
    def flip(self, x, y):
        row = list(self.g[x-1]); row[y-1] = '/' if row[y-1] == '\\' else '\\'
        self.g[x-1] = ''.join(row)
        if self.B:
            b = (x-1)//self.B
            self.build(b)
            # a flip can also change the V-check for the neighbouring columns in the
            # same row, which lives in the same block, so one rebuild suffices
    def drop(self, col):
        if not self.B:
            return step_sim(self.g, self.M, self.N, col)
        c = col
        for b in range(self.nb):
            c = self.tab[b][c]
            if c == DEAD: return -1
        return c

def main():
    grid = ["\\\\\\\\", "////", "\\\\\\\\", "/\\\\\\"]
    assert all(len(r) == 4 for r in grid), [len(r) for r in grid]
    bl = Blocks(list(grid), 4, 4)
    out = []
    out.append(bl.drop(4)); out.append(bl.drop(1))
    bl.flip(4, 2)
    out.append(bl.drop(1)); out.append(bl.drop(2))
    bl.flip(4, 4)
    out.append(bl.drop(2))
    print("sample:", out)
    assert out == [-1, 3, 1, 4, -1], out
    print("sample OK")

    random.seed(9); bad = 0
    for trial in range(300):
        M = random.randint(1, 12); N = random.randint(1, 12)
        g = [''.join(random.choice('\\/') for _ in range(N)) for _ in range(M)]
        bl = Blocks(list(g), M, N)
        gg = list(g)
        for _ in range(40):
            if random.random() < 0.4:
                x = random.randint(1, M); y = random.randint(1, N)
                bl.flip(x, y)
                row = list(gg[x-1]); row[y-1] = '/' if row[y-1] == '\\' else '\\'
                gg[x-1] = ''.join(row)
            else:
                c = random.randint(1, N)
                a = bl.drop(c); b = step_sim(gg, M, N, c)
                if a != b:
                    bad += 1
                    if bad < 4: print("MISMATCH", M, N, gg, c, a, b)
    print("blocks vs naive over random boards/queries: mismatches =", bad)
    assert bad == 0
    # shapes that exercise the M>N branch hard
    for (M, N) in [(50, 2), (100, 1), (37, 3), (9, 9), (2, 50)]:
        g = [''.join(random.choice('\\/') for _ in range(N)) for _ in range(M)]
        bl = Blocks(list(g), M, N); gg = list(g)
        for _ in range(200):
            if random.random() < 0.4:
                x = random.randint(1, M); y = random.randint(1, N)
                bl.flip(x, y)
                row = list(gg[x-1]); row[y-1] = '/' if row[y-1] == '\\' else '\\'
                gg[x-1] = ''.join(row)
            else:
                c = random.randint(1, N)
                assert bl.drop(c) == step_sim(gg, M, N, c), (M, N, gg, c)
    print("tall/wide shapes OK")
    print("droppingball: OK")

main()
