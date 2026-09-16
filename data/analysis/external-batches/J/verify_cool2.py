"""Kattis cool2 (2015 ICPC Singapore, G) -- UNSOLVED, this records what was established.

Task: print (with no input) a valid cool1 instance -- N in [3,200], a program of
length <= N over {<,>,^,v}, and an N x N walled grid with one R -- whose cool1
answer, the eventual period of the robot's trail, is at least 10^6.

Established here:
 (1) One full pass of the program induces a map F on cells, and the program counter
     returns to 0 after every pass, so every state cycle is a whole number of passes
     and X = sum over the cells of one F-cycle of the moves that pass makes.
     Hence X <= (N-2)^2 * L <= 198^2 * 200 = 7840800, and reaching 10^6 needs an
     F-cycle of at least 10^6/200 = 5000 cells, i.e. >= 12.7% of the interior.
 (2) A wall-free room is useless: with no interior walls the x and y coordinates
     evolve independently, each by clamped shifts, which are monotone maps of a
     chain and therefore converge to a fixed point.  So F has only fixed points and
     X <= L <= 200.  check_open_room() below demonstrates this.
     The same argument kills every 1-cell-wide corridor (a chain, so the pass map
     is order preserving along it) -- a long cycle needs genuine 2D coupling.
 (3) Searching did not find one.  Random search over four structured families
     (uniform random walls; horizontal corridors with random rungs; brick offsets;
     jagged "skyline" rooms), plus hill climbing on the skyline profiles and the
     program, topped out around X = 1.8*10^4 with only ~90 cells in the F-cycle --
     about 55x short.  search_demo() reproduces the shape of that plateau at N=40.

What is missing is a deliberate gadget that makes F a long-cycle permutation, i.e.
an odometer whose carry is triggered by a wall.  Every hand construction tried
(combs of teeth, two corridors joined by rungs, serpentine rings, billiard-style
bouncing) failed for the same reason: the horizontal drift is a clamped shift and
sticks at a wall, and a direction reversal needs state the program cannot carry,
because the program counter resets every pass.
"""
import random

DIRS = {'<': (0, -1), '>': (0, 1), '^': (-1, 0), 'v': (1, 0)}

def period(n, prog, blocked, start):
    """cool1's answer for this instance (same algorithm as verify_cool1.py)"""
    L = len(prog)
    seen = {}
    r, c = start
    pc, t = 0, 0
    while (r, c, pc) not in seen:
        seen[(r, c, pc)] = t
        dr, dc = DIRS[prog[pc]]
        if not blocked[r + dr][c + dc]:
            r, c = r + dr, c + dc
        pc = (pc + 1) % L
        t += 1
    cyclen = t - seen[(r, c, pc)]
    block = []
    for _ in range(cyclen):
        dr, dc = DIRS[prog[pc]]
        if not blocked[r + dr][c + dc]:
            r, c = r + dr, c + dc
            block.append(r * n + c)
        pc = (pc + 1) % L
    if not block:
        return 1
    m = len(block)
    fail = [0] * (m + 1)
    k = 0
    for i in range(1, m):
        while k and block[i] != block[k]:
            k = fail[k]
        if block[i] == block[k]:
            k += 1
        fail[i + 1] = k
    p = m - fail[m]
    return p if m % p == 0 else m

def check_open_room(n=20, trials=300):
    """claim (2): a room with no interior walls can never beat L"""
    rnd = random.Random(1)
    blocked = [[i in (0, n - 1) or j in (0, n - 1) for j in range(n)] for i in range(n)]
    worst = 0
    for _ in range(trials):
        prog = ''.join(rnd.choice('<>^v') for _ in range(rnd.randint(1, n)))
        start = (rnd.randint(1, n - 2), rnd.randint(1, n - 2))
        worst = max(worst, period(n, prog, blocked, start))
    assert worst <= n, worst
    print("open room, N=%d: worst period over %d random programs = %d (<= L <= %d)"
          % (n, trials, worst, n))

def search_demo(n=40, trials=400):
    """claim (3): random mazes plateau far below what is needed"""
    rnd = random.Random(2)
    best = 0
    for _ in range(trials):
        dens = rnd.uniform(0.05, 0.4)
        blocked = [[i in (0, n - 1) or j in (0, n - 1) or rnd.random() < dens
                    for j in range(n)] for i in range(n)]
        free = [(i, j) for i in range(1, n - 1) for j in range(1, n - 1) if not blocked[i][j]]
        if not free:
            continue
        prog = ''.join(rnd.choice('<>^v') for _ in range(n))
        best = max(best, period(n, prog, blocked, rnd.choice(free)))
    bound = (n - 2) ** 2 * n
    print("random mazes, N=%d: best period found over %d tries = %d (state-space bound %d, target 10^6)"
          % (n, trials, best, bound))
    return best

if __name__ == "__main__":
    check_open_room()
    search_demo()
    print("status: UNSOLVED -- no instance reaching 10^6 was constructed")
