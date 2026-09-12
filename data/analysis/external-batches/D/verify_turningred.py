"""
kattis-turningred  (ICPC World Finals 2022, "Turning Red")

MODEL
-----
Colours R,G,B = 0,1,2.  Pressing a button adds +1 (mod 3) to every light it
controls.  If light i starts at colour c_i and the buttons controlling it are
pressed x_u times in total, the final colour is c_i + sum(x) (mod 3); we need
that to be 0, i.e.  sum of presses over the buttons of light i  ==  d_i  (mod 3)
with d_i = (-c_i) mod 3.

Only residues matter, and the cheapest way to realise residue r on one button is
r presses (r in {0,1,2}).  So: minimise  sum_j x_j,  x_j in {0,1,2}, subject to a
Z_3 linear system in which every equation touches at most TWO variables (a light
is controlled by at most two buttons).

That makes it a graph: buttons = vertices, a 2-button light = an edge with
equation x_u + x_v = d, a 1-button light = a unary constraint x_u = d, a
0-button light = a feasibility check d = 0.  Inside one connected component,
fixing the root's value t determines every other value by propagation
(x_v = d - x_u along an edge), so there are only 3 candidate solutions per
component; costs of different components are independent and add.  Try t in
{0,1,2}, keep the consistent ones, take the cheapest.   O(3*(l+b)).

Note the equation is x_u + x_v (not a difference), so values flip sign on odd
steps: an odd cycle pins t (2t = const has a unique root mod 3), an even cycle
gives a t-independent consistency check.  The 3-way enumeration handles both
without special-casing.

This file cross-checks that O(l+b) solution against an exhaustive 3^b brute
force on random small instances, plus the four official samples.
"""
import random
from itertools import product

IMP = "impossible"


# ---------------------------------------------------------------- fast solver
def solve(l, b, colors, buttons):
    """colors: string of R/G/B.  buttons: list of lists of 0-based light ids."""
    need = [(-"RGB".index(ch)) % 3 for ch in colors]
    owners = [[] for _ in range(l)]
    for j, lights in enumerate(buttons):
        for i in lights:
            owners[i].append(j)

    adj = [[] for _ in range(b)]          # (other button, d)
    unary = [[] for _ in range(b)]        # forced values
    for i in range(l):
        o = owners[i]
        if len(o) == 0:
            if need[i] != 0:
                return IMP
        elif len(o) == 1:
            unary[o[0]].append(need[i])
        else:
            u, v = o
            adj[u].append((v, need[i]))
            adj[v].append((u, need[i]))

    val = [-1] * b
    seen = [False] * b
    total = 0
    for root in range(b):
        if seen[root]:
            continue
        comp = []
        stack = [root]
        seen[root] = True
        while stack:                       # collect the component once
            u = stack.pop()
            comp.append(u)
            for v, _ in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    stack.append(v)
        best = None
        for t in range(3):
            for u in comp:
                val[u] = -1
            val[root] = t
            ok = True
            order = [root]
            head = 0
            while head < len(order) and ok:
                u = order[head]
                head += 1
                for d in unary[u]:
                    if val[u] != d:
                        ok = False
                        break
                if not ok:
                    break
                for v, d in adj[u]:
                    w = (d - val[u]) % 3
                    if val[v] == -1:
                        val[v] = w
                        order.append(v)
                    elif val[v] != w:
                        ok = False
                        break
            if ok:
                cost = sum(val[u] for u in comp)
                if best is None or cost < best:
                    best = cost
        if best is None:
            return IMP
        total += best
    return total


# ---------------------------------------------------------------- brute force
def brute(l, b, colors, buttons):
    base = ["RGB".index(ch) for ch in colors]
    best = None
    for x in product(range(3), repeat=b):
        cur = base[:]
        for j, p in enumerate(x):
            if p:
                for i in buttons[j]:
                    cur[i] = (cur[i] + p) % 3
        if all(c == 0 for c in cur):
            s = sum(x)
            if best is None or s < best:
                best = s
    return IMP if best is None else best


# ---------------------------------------------------------------- samples
SAMPLES = [
    ("8 6\nGBRBRRRG\n2 1 4\n1 2\n4 4 5 6 7\n3 5 6 7\n1 8\n1 8", 8),
    ("4 3\nRGBR\n2 1 2\n2 2 3\n2 3 4", IMP),
    ("4 4\nGBRG\n2 1 2\n2 2 3\n2 3 4\n1 4", 6),
    ("3 3\nRGB\n1 1\n1 2\n1 3", 3),
]


def parse(text):
    it = iter(text.split("\n"))
    l, b = map(int, next(it).split())
    colors = next(it).strip()
    buttons = []
    for _ in range(b):
        parts = list(map(int, next(it).split()))
        buttons.append([x - 1 for x in parts[1:]])
    return l, b, colors, buttons


def run_samples():
    for text, expected in SAMPLES:
        l, b, colors, buttons = parse(text)
        got = solve(l, b, colors, buttons)
        assert got == expected, (text, got, expected)
        assert brute(l, b, colors, buttons) == expected, "brute disagrees on sample"
    print("4/4 official samples OK (fast solver and brute force)")


# ---------------------------------------------------------------- random tests
def random_case(rng, maxl=6, maxb=7):
    l = rng.randint(1, maxl)
    slots = []                     # each light may be used at most twice
    for i in range(l):
        slots += [i] * rng.choice([0, 1, 2, 2])
    rng.shuffle(slots)
    b = rng.randint(0, min(maxb, 2 * l))
    buttons = [[] for _ in range(b)]
    if b:
        for i in slots:
            # place light i in a button that does not already hold it
            cand = [j for j in range(b) if i not in buttons[j]]
            if cand:
                buttons[rng.choice(cand)].append(i)
    buttons = [x for x in buttons if x]            # k >= 1 per the statement
    b = len(buttons)
    colors = "".join(rng.choice("RGB") for _ in range(l))
    return l, b, colors, buttons


def run_random(n=6000, seed=12345):
    rng = random.Random(seed)
    imp = feas = 0
    for _ in range(n):
        l, b, colors, buttons = random_case(rng)
        got = solve(l, b, colors, buttons)
        exp = brute(l, b, colors, buttons)
        if got != exp:
            print("MISMATCH")
            print(" l,b =", l, b, "colors =", colors, "buttons =", buttons)
            print(" fast =", got, " brute =", exp)
            raise SystemExit(1)
        if exp == IMP:
            imp += 1
        else:
            feas += 1
    print(f"{n} random small cases OK  ({feas} feasible, {imp} impossible)")


def run_random_dense(n=1500, seed=999):
    """Bias towards many 2-button lights so cycles (odd and even) show up."""
    rng = random.Random(seed)
    odd = 0
    for _ in range(n):
        l = rng.randint(2, 6)
        b = rng.randint(2, 6)
        buttons = [[] for _ in range(b)]
        for i in range(l):
            js = rng.sample(range(b), min(b, 2))
            for j in js:
                buttons[j].append(i)
        buttons = [x for x in buttons if x]
        b = len(buttons)
        if b == 0:
            continue
        colors = "".join(rng.choice("RGB") for _ in range(l))
        got, exp = solve(l, b, colors, buttons), brute(l, b, colors, buttons)
        if got != exp:
            print("MISMATCH (dense)", l, b, colors, buttons, got, exp)
            raise SystemExit(1)
        if exp != IMP:
            odd += 1
    print(f"{n} dense cycle-heavy cases OK ({odd} feasible)")


def run_stress_size():
    """Sanity: the O(l+b) solver handles the real limits quickly."""
    import time
    rng = random.Random(7)
    l = 200000
    b = 2 * l
    buttons = [[] for _ in range(b)]
    for i in range(l):                      # a long chain of components
        buttons[2 * i].append(i)
        buttons[2 * i + 1].append(i)
    colors = "".join(rng.choice("RGB") for _ in range(l))
    t0 = time.time()
    ans = solve(l, b, colors, buttons)
    print(f"l=2e5 b=4e5 answer={ans} in {time.time() - t0:.2f}s")


if __name__ == "__main__":
    run_samples()
    run_random()
    run_random_dense()
    run_stress_size()
