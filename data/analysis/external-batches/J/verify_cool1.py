"""Kattis cool1 (2015 ICPC Singapore, F).

Task: an N x N walled grid (3 <= N <= 200, border all walls) and a program string
of length L <= N over {<,>,^,v}.  The robot repeats the program forever, skipping
a move that would enter a wall.  The trail is the sequence of cells it ENTERS
(nothing is appended for a skipped move).  Print 1 if the trail is finite,
otherwise the eventual minimal period X of the trail.

Solution under test: the configuration (cell, program counter) is a state, and the
step map is deterministic, so the state graph is a functional graph with at most
N*N*L <= 8*10^6 nodes.  Walk it, stamping first-visit times, until a state repeats;
that gives the rho's cycle.  Replay exactly one lap of the cycle and collect the
cells entered: that block B repeats forever.  If B is empty the robot stops moving
and the trail is finite -> print 1.  Otherwise the tail is B^infinity, whose
minimal period divides |B|, so take p = |B| - failure[|B|] from the KMP prefix
function of B and answer p if p divides |B|, else |B|.
Time and space O(N*N*L).

Brute force: run the robot for a long time, then find the smallest X that the
observed tail is genuinely periodic with.
"""
import random

DIRS = {'<': (0, -1), '>': (0, 1), '^': (-1, 0), 'v': (1, 0)}

def solve(n, prog, grid):
    L = len(prog)
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 'R':
                sr, sc = i, j
    blocked = [[grid[i][j] == '#' for j in range(n)] for i in range(n)]
    seen = {}
    r, c, pc, t = sr, sc, 0, 0
    while (r, c, pc) not in seen:
        seen[(r, c, pc)] = t
        dr, dc = DIRS[prog[pc]]
        nr, nc = r + dr, c + dc
        if not blocked[nr][nc]:
            r, c = nr, nc
        pc = (pc + 1) % L
        t += 1
    t0 = seen[(r, c, pc)]
    cyclen = t - t0
    block = []
    for _ in range(cyclen):
        dr, dc = DIRS[prog[pc]]
        nr, nc = r + dr, c + dc
        if not blocked[nr][nc]:
            r, c = nr, nc
            block.append(r * n + c)
        pc = (pc + 1) % L
    if not block:
        return 1
    return minimal_period(block)

def minimal_period(b):
    m = len(b)
    fail = [0] * (m + 1)
    k = 0
    for i in range(1, m):
        while k and b[i] != b[k]:
            k = fail[k]
        if b[i] == b[k]:
            k += 1
        fail[i + 1] = k
    p = m - fail[m]
    return p if m % p == 0 else m

def brute(n, prog, grid, steps=200000):
    L = len(prog)
    for i in range(n):
        for j in range(n):
            if grid[i][j] == 'R':
                r, c = i, j
    blocked = [[grid[i][j] == '#' for j in range(n)] for i in range(n)]
    trail = [r * n + c]
    pc = 0
    for _ in range(steps):
        dr, dc = DIRS[prog[pc]]
        nr, nc = r + dr, c + dc
        if not blocked[nr][nc]:
            r, c = nr, nc
            trail.append(r * n + c)
        pc = (pc + 1) % L
    if len(trail) < steps // 50:          # essentially stopped moving
        return 1
    tail = trail[len(trail) // 2:]        # safely past the transient
    for x in range(1, len(tail) // 3):
        if all(tail[i] == tail[i + x] for i in range(len(tail) - x)):
            return x
    return None                            # inconclusive

def samples():
    cases = [
        (6, ">^<^", ["######", "#.#..#", "#....#", "#..R.#", "#....#", "######"], 2),
        (4, "v<^>", ["####", "#.R#", "#..#", "####"], 4),
        (4, "<<<", ["####", "#.R#", "#..#", "####"], 1),
        (5, "<<>>", ["#####", "#R..#", "#####", "#####", "#####"], 4),
    ]
    for n, p, g, want in cases:
        got = solve(n, p, g)
        assert got == want, (p, got, want)
    print("samples OK (all 4)")

def rand_case(rnd, n=6):
    while True:
        g = [['#'] * n for _ in range(n)]
        cells = []
        for i in range(1, n - 1):
            for j in range(1, n - 1):
                if rnd.random() < 0.7:
                    g[i][j] = '.'
                    cells.append((i, j))
        if cells:
            break
    r, c = rnd.choice(cells)
    g[r][c] = 'R'
    prog = ''.join(rnd.choice('<>^v') for _ in range(rnd.randint(1, n)))
    return n, prog, [''.join(row) for row in g]

def fuzz(trials=1500):
    rnd = random.Random(31337)
    checked = 0
    for _ in range(trials):
        n, prog, g = rand_case(rnd, rnd.randint(3, 7))
        a = solve(n, prog, g)
        b = brute(n, prog, g, steps=20000)
        if b is None:
            continue
        checked += 1
        if a != b:
            print("MISMATCH", n, prog, g, a, b)
            return False
    print("fuzz OK (%d random grids cross-checked against a long direct simulation)" % checked)
    return True

if __name__ == "__main__":
    samples()
    assert fuzz()
