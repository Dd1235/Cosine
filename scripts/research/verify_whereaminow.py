"""
Verification for kattis-whereaminow  (ICPC WF 2024, "Where Am I Now?")

Derived solution under test
---------------------------
Interactive localisation in a KNOWN map from an unknown start state (cell, heading).
State = (row, col, dir); observation o(state) = number of open cells strictly ahead
before the first wall; actions left / right / step (step legal iff o > 0).

The solution rests on:
 (1) Every candidate consistent with the observation history reports the SAME o each
     round, so one observation-driven action sequence is simultaneously legal and
     meaningful for all of them: plan in a RELATIVE frame and every candidate follows
     along in its own frame.  In particular "step" is safe for everybody iff o > 0.
 (2) left/right/step are injective on states, so the candidate set S only ever shrinks
     by observation splits - there is no merging trick, we must out-observe the ties.
 (3) Two states are forever indistinguishable  <=>  a rotation (multiple of 90 deg,
     no reflection - turning is handed) plus a translation carries the 4-connected open
     component of one onto the component of the other, state to state.  PART A checks
     this against explicit Moore-machine minimisation.
 (4) Hence: DFS-explore the component in relative coordinates (a 3-turn scan at a cell
     reveals its 4 neighbours; every observation also reveals a whole ray of open cells
     plus one wall).  When exploration is complete the survivors are exactly one
     indistinguishability class.  Answer "yes i j" the moment all survivors share a
     position; otherwise walk to a cell that every surviving isometry maps to the same
     square (a common fixed point) if one exists - that resolves an ambiguous start -
     and only if none exists answer "no".
Cost O(r*c) rounds: <=3 rounds per move, 2 moves per spanning-tree edge, 3 rounds of
scan per cell; the 100000-round budget is sized for exactly this.

Parts
  A  theory: bisimulation classes == isometry-of-component classes
  B  end-to-end: run the strategy from EVERY start state of random small maps and of
     hand-built symmetric maps, compare the verdict with brute force, assert we never
     step into a wall and that a "yes" names the true CURRENT cell
  C  the three sample interactions from the statement
  D  round budget on 100x100 worst-ish maps
"""
import random
from collections import deque

DR = [-1, 0, 1, 0]          # N, E, S, W ; turning right = +1 (clockwise as printed)
DC = [0, 1, 0, -1]


# ---------------------------------------------------------------- world model
def obs_of(r, c, op, i, j, d):
    k = 0
    while True:
        ni, nj = i + DR[d] * (k + 1), j + DC[d] * (k + 1)
        if 0 <= ni < r and 0 <= nj < c and op[ni][nj]:
            k += 1
        else:
            return k


def all_states(r, c, op):
    return [(i, j, d) for i in range(r) for j in range(c) if op[i][j] for d in range(4)]


def rot_cw(v, k):
    di, dj = v
    for _ in range(k % 4):
        di, dj = dj, -di          # N(-1,0)->E(0,1)->S(1,0)->W(0,-1)
    return (di, dj)


def component(r, c, op, i, j):
    seen = {(i, j)}
    q = deque([(i, j)])
    while q:
        a, b = q.popleft()
        for d in range(4):
            na, nb = a + DR[d], b + DC[d]
            if 0 <= na < r and 0 <= nb < c and op[na][nb] and (na, nb) not in seen:
                seen.add((na, nb))
                q.append((na, nb))
    return seen


def comp_map(r, c, op):
    out = {}
    for i in range(r):
        for j in range(c):
            if op[i][j] and (i, j) not in out:
                comp = component(r, c, op, i, j)
                for cell in comp:
                    out[cell] = comp
    return out


def isometry_sig(cm, s):
    """the component as the robot itself sees it: own cell at origin, facing north"""
    i, j, d = s
    k = (4 - d) % 4
    return frozenset(rot_cw((a - i, b - j), k) for (a, b) in cm[(i, j)])


# --------------------------------------------------- brute force ground truth
def bisim_classes(r, c, op):
    """Moore-machine minimisation over the alphabet {left, right, step}."""
    st = all_states(r, c, op)
    ob = {s: obs_of(r, c, op, *s) for s in st}
    L = {s: (s[0], s[1], (s[2] - 1) % 4) for s in st}
    R = {s: (s[0], s[1], (s[2] + 1) % 4) for s in st}
    S = {s: ((s[0] + DR[s[2]], s[1] + DC[s[2]], s[2]) if ob[s] > 0 else None) for s in st}
    cls = dict(ob)                       # initial partition: by observation
    nblocks = len(set(cls.values()))
    while True:
        m, new = {}, {}
        for s in st:
            g = (cls[s], cls[L[s]], cls[R[s]], cls[S[s]] if S[s] else -1)
            if g not in m:
                m[g] = len(m)
            new[s] = m[g]
        if len(m) == nblocks:
            return cls
        cls, nblocks = new, len(m)


def truth(r, c, op):
    """Per start state: can the position EVER be pinned down?  Every cell of the
    component is reachable and turning does not move us, so the start state can be
    resolved iff some cell of its component has a single-position class."""
    cls = bisim_classes(r, c, op)
    cm = comp_map(r, c, op)
    bypos = {}
    for s, k in cls.items():
        bypos.setdefault(k, set()).add((s[0], s[1]))
    resolvable = {}
    for s in cls:
        comp = cm[(s[0], s[1])]
        resolvable[s] = any(len(bypos[cls[(a, b, 0)]]) == 1 for (a, b) in comp)
    return resolvable, cls


# ------------------------------------------------------------------- agent
class Agent:
    """The strategy.  Plans in a relative frame so that every issued action is valid
    for every survivor at once."""

    def __init__(self, r, c, op, track_S=True):
        self.r, self.c, self.op = r, c, op
        self.pos, self.dir = (0, 0), 0
        self.known = {(0, 0): True}       # relative cell -> open?
        self.plan = []
        self.scan_turns = 0
        self.scanned = set()
        self.visited = {(0, 0)}
        self.parent = {}
        self.explored = False
        self.track_S = track_S
        self.rounds = 0
        self.phase2 = False
        if track_S:
            self.cm = comp_map(r, c, op)
            self.sig = {s: isometry_sig(self.cm, s) for s in all_states(r, c, op)}
            self.S = set(self.sig)

    # ---- relative-map bookkeeping
    def _record(self, d):
        pi, pj = self.pos
        for t in range(1, d + 1):
            self.known[(pi + DR[self.dir] * t, pj + DC[self.dir] * t)] = True
        self.known[(pi + DR[self.dir] * (d + 1), pj + DC[self.dir] * (d + 1))] = False

    def _turns_to(self, k):
        return {0: [], 1: ['right'], 2: ['right', 'right'], 3: ['left']}[(k - self.dir) % 4]

    # ---- one round: feed the observation, get an action or a verdict
    def observe(self, d):
        self.rounds += 1
        self._record(d)
        if self.track_S:
            self.S = {s for s in self.S if obs_of(self.r, self.c, self.op, *s) == d}
            assert self.S, "candidate set went empty - model bug"
            poss = {(s[0], s[1]) for s in self.S}
            if len(poss) == 1:
                return ('yes', poss.pop())
            if not self.phase2 and (self.explored
                                    or len({self.sig[s] for s in self.S}) == 1):
                # survivors are one indistinguishability class: no observation will
                # ever split them again.  Only a common fixed point can still help.
                self.phase2 = True
                self.plan = self._goto_fixed_point()
                if self.plan is None:
                    return ('no',)
            if self.phase2 and not self.plan:
                return ('no',)
        elif self.explored:
            return ('done',)
        act = self._next_action()
        if act is None:                    # exploration just finished
            return ('done',)
        return ('act', act)

    # ---- phase 2: is there a square that every survivor's isometry agrees on?
    def _goto_fixed_point(self):
        rep = min(self.S)
        ri, rj, rd = rep
        target = None
        for (a, b) in self.cm[(ri, rj)]:
            img = set()
            for (i, j, d) in self.S:
                v = rot_cw((a - ri, b - rj), (d - rd) % 4)
                img.add((i + v[0], j + v[1]))
                if len(img) > 1:
                    break
            if len(img) == 1:
                target = (a, b)
                break
        if target is None:
            return None
        # shortest path in rep's own (fully known) component, replayed relatively
        prev = {(ri, rj): None}
        q = deque([(ri, rj)])
        while q:
            cell = q.popleft()
            if cell == target:
                break
            for k in range(4):
                nb = (cell[0] + DR[k], cell[1] + DC[k])
                if nb in self.cm.get((ri, rj), ()) and nb not in prev:
                    prev[nb] = cell
                    q.append(nb)
        path, cur = [], target
        while prev[cur] is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        acts, cell, wdir = [], (ri, rj), rd
        k = (rd - self.dir) % 4           # relative dir e  <->  world dir (e+k)%4
        simdir = self.dir
        for nxt in path:
            wd = [t for t in range(4)
                  if (cell[0] + DR[t], cell[1] + DC[t]) == nxt][0]
            rel = (wd - k) % 4
            acts += {0: [], 1: ['right'], 2: ['right', 'right'], 3: ['left']}[(rel - simdir) % 4]
            acts.append('step')
            simdir, cell = rel, nxt
        return acts

    # ---- action selection
    def _next_action(self):
        while not self.plan:
            self._plan_more()
            if self.explored and not self.plan:
                return None
        a = self.plan.pop(0)
        if a == 'left':
            self.dir = (self.dir - 1) % 4
        elif a == 'right':
            self.dir = (self.dir + 1) % 4
        else:
            self.pos = (self.pos[0] + DR[self.dir], self.pos[1] + DC[self.dir])
        if self.track_S:                   # carry every candidate along
            if a == 'left':
                self.S = {(i, j, (d - 1) % 4) for (i, j, d) in self.S}
            elif a == 'right':
                self.S = {(i, j, (d + 1) % 4) for (i, j, d) in self.S}
            else:
                self.S = {(i + DR[d], j + DC[d], d) for (i, j, d) in self.S}
        return a

    def _plan_more(self):
        cur = self.pos
        if cur not in self.scanned:                 # learn all four neighbours
            if self.scan_turns < 3:
                self.scan_turns += 1
                self.plan = ['right']
                return
            self.scanned.add(cur)
            self.scan_turns = 0
        for k in range(4):                          # DFS deeper
            nb = (cur[0] + DR[k], cur[1] + DC[k])
            if self.known.get(nb) and nb not in self.visited:
                self.visited.add(nb)
                self.parent[nb] = cur
                self.plan = self._turns_to(k) + ['step']
                return
        if cur in self.parent:                      # backtrack
            p = self.parent[cur]
            k = [t for t in range(4) if (cur[0] + DR[t], cur[1] + DC[t]) == p][0]
            self.plan = self._turns_to(k) + ['step']
            return
        self.explored = True


def simulate(r, c, op, true_state, limit=100000):
    ag = Agent(r, c, op, track_S=True)
    st = list(true_state)
    while True:
        assert ag.rounds < limit, "round limit"
        d = obs_of(r, c, op, *st)
        res = ag.observe(d)
        assert res[0] != 'done', "exploration finished without a verdict"
        if res[0] != 'act':
            return res, (st[0], st[1]), ag.rounds
        a = res[1]
        if a == 'left':
            st[2] = (st[2] - 1) % 4
        elif a == 'right':
            st[2] = (st[2] + 1) % 4
        else:
            assert d > 0, "STEPPED INTO A WALL"
            st[0] += DR[st[2]]
            st[1] += DC[st[2]]
            assert op[st[0]][st[1]]


# ------------------------------------------------------------------- tests
def random_map(r, c, p, rng):
    while True:
        g = [''.join('.' if rng.random() > p else '#' for _ in range(c)) for _ in range(r)]
        if any('.' in row for row in g):
            return g


def check_map(g, label=''):
    r, c = len(g), len(g[0])
    op = [[ch == '.' for ch in row] for row in g]
    res_ok, _ = truth(r, c, op)
    worst = 0
    for s in all_states(r, c, op):
        verdict, curpos, rounds = simulate(r, c, op, s)
        worst = max(worst, rounds)
        if res_ok[s]:
            assert verdict == ('yes', curpos), ("WRONG", label, g, s, verdict, curpos)
        else:
            assert verdict == ('no',), ("WRONG", label, g, s, verdict)
    return worst


def partA(trials=250, seed=1):
    rng = random.Random(seed)
    for _ in range(trials):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        g = random_map(r, c, rng.choice([0.2, 0.35, 0.5, 0.65]), rng)
        op = [[ch == '.' for ch in row] for row in g]
        cls = bisim_classes(r, c, op)
        cm = comp_map(r, c, op)
        sig = {s: isometry_sig(cm, s) for s in all_states(r, c, op)}
        a, b = {}, {}
        for s in cls:
            a.setdefault(cls[s], set()).add(s)
            b.setdefault(sig[s], set()).add(s)
        assert {frozenset(v) for v in a.values()} == {frozenset(v) for v in b.values()}, g
    print(f"A ok: bisimulation classes == isometry-of-component classes, "
          f"{trials} random maps (so rotations+translations are the ONLY ambiguity, "
          f"and reflections are NOT - turning is handed)")


def partB(trials=140, seed=7):
    rng = random.Random(seed)
    worst = 0
    for _ in range(trials):
        r, c = rng.randint(1, 6), rng.randint(1, 6)
        g = random_map(r, c, rng.choice([0.15, 0.3, 0.45, 0.6]), rng)
        worst = max(worst, check_map(g, 'rand'))
    print(f"B ok: {trials} random maps x every start state - verdict and reported cell "
          f"match brute force, never stepped into a wall (max rounds {worst})")


def partB2():
    tmpls = [
        ["...", "...", "..."],                      # square room: rotation about centre
        ["....", ".##.", "...."],
        [".#.", "###", ".#."],                      # four separate cells
        ["..#..", "..#..", "....."],
        ["#.#.#", ".....", "#.#.#"],
        [".....", ".###.", ".....", ".###.", "....."],
        ["..", ".#"],
        ["....", "....", "....", "...."],
        [".#.#.#.#."],
        ["...#...", "...#...", "...#..."],           # two congruent 3x3 rooms
        [".#.", "...", ".#."],                       # plus/cross: centre is a fixed point
        ["#.#", "...", "#.#"],
        ["....", "#..#", "#..#", "...."],
        ["..#", ".##", "###"],
        ["#####", "#...#", "#.#.#", "#...#", "#####"],
    ]
    worst = 0
    for g in tmpls:
        worst = max(worst, check_map(g, 'hand'))
    print(f"B2 ok: {len(tmpls)} hand-built symmetric/structured maps x every start "
          f"state (max rounds {worst})")


def partC():
    # sample 1: replay the judge's trajectory, see what it pins down
    g = ["##.", "#..", "..."]
    r, c = 3, 3
    op = [[ch == '.' for ch in row] for row in g]
    acts = ['right', 'step', 'left', 'right', 'right']
    reads = [1, 1, 0, 0, 0, 1]
    ok = []
    for s in all_states(r, c, op):
        st, good, prev = list(s), True, None
        for idx, a in enumerate([None] + acts):
            if a == 'right':
                st[2] = (st[2] + 1) % 4
            elif a == 'left':
                st[2] = (st[2] - 1) % 4
            elif a == 'step':
                if prev == 0:
                    good = False
                    break
                st[0] += DR[st[2]]
                st[1] += DC[st[2]]
            prev = obs_of(r, c, op, *st)
            if prev != reads[idx]:
                good = False
                break
        if good:
            ok.append(tuple(st))
    assert ok and {(x[0], x[1]) for x in ok} == {(1, 1)}, ok      # 0-indexed -> "2 2"
    check_map(g, 'sample1')
    # sample 2: four isolated cells -> every state is hopeless
    g2 = ["##.##", "###.#", ".#.##"]
    op2 = [[ch == '.' for ch in row] for row in g2]
    res2, _ = truth(3, 5, op2)
    assert not any(res2.values())
    for s in all_states(3, 5, op2):
        assert simulate(3, 5, op2, s)[0] == ('no',)
    # sample 3: the only open cell
    g3 = ["#", "."]
    op3 = [[ch == '.' for ch in row] for row in g3]
    v, pos, _ = simulate(2, 1, op3, (1, 0, 0))
    assert v == ('yes', (1, 0)) and pos == (1, 0)
    print("C ok: sample 1's trajectory pins down exactly row 2 col 2, and our strategy "
          "answers correctly from every start state of it; sample 2 is 'no' from every "
          "state; sample 3 is 'yes 2 1'")


def partD():
    def rounds_for(g):
        r, c = len(g), len(g[0])
        op = [[ch == '.' for ch in row] for row in g]
        start = next((i, j) for i in range(r) for j in range(c) if op[i][j])
        ag = Agent(r, c, op, track_S=False)
        st = [start[0], start[1], 0]
        while True:
            d = obs_of(r, c, op, *st)
            res = ag.observe(d)
            if res[0] == 'done':
                return ag.rounds, len(component(r, c, op, *start))
            a = res[1]
            if a == 'left':
                st[2] = (st[2] - 1) % 4
            elif a == 'right':
                st[2] = (st[2] + 1) % 4
            else:
                assert d > 0
                st[0] += DR[st[2]]
                st[1] += DC[st[2]]

    maps = {}
    maps['all open 100x100'] = ['.' * 100 for _ in range(100)]
    maps['comb'] = ['.' * 100] + [''.join('.' if j % 2 == 0 else '#' for j in range(100))
                                  for _ in range(99)]
    rng = random.Random(5)
    n = 50
    grid = [['#'] * 99 for _ in range(99)]
    seen = [[False] * n for _ in range(n)]
    stack = [(0, 0)]
    seen[0][0] = True
    grid[0][0] = '.'
    while stack:
        i, j = stack[-1]
        nb = [(i + a, j + b) for a, b in ((-1, 0), (1, 0), (0, -1), (0, 1))
              if 0 <= i + a < n and 0 <= j + b < n and not seen[i + a][j + b]]
        if not nb:
            stack.pop()
            continue
        ni, nj = rng.choice(nb)
        seen[ni][nj] = True
        grid[ni * 2][nj * 2] = '.'
        grid[i + ni][j + nj] = '.'
        stack.append((ni, nj))
    maps['perfect maze 99x99'] = [''.join(row) for row in grid]
    sp = [['.'] * 100 for _ in range(100)]
    for k in range(0, 50, 2):
        for j in range(k, 100 - k):
            sp[k + 1][j] = '#'
        sp[k + 1][100 - k - 1] = '.'
    maps['spiral-ish'] = [''.join(row) for row in sp]
    worst = 0
    for name, g in maps.items():
        rd, cells = rounds_for(g)
        worst = max(worst, rd)
        flag = 'OK' if rd <= 100000 else 'OVER BUDGET'
        print(f"   {name:20s} component {cells:6d} cells -> {rd:6d} rounds to explore "
              f"it FULLY  [{flag}]")
    print(f"D: worst full-exploration cost {worst} rounds vs the 100000 budget "
          f"(a real run stops as soon as the survivors agree, usually far sooner)")


if __name__ == '__main__':
    partA()
    partB()
    partB2()
    partC()
    partD()
