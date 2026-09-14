"""kattis-towerofnoiha / "Tower of noiHa" (ICPC WF 2024, problem K) -- verification.

Setting: n disks, the first k optimal Hanoi moves (A -> C) were made, then the whole
stack of rod A was dumped, order preserved, on top of rod C.  Rod C is now
C_old ++ A_old (two sorted blocks; the only possible inversion is at the junction).
Wanted: min number of valid moves (never a disk onto a smaller one) to the perfect
tower on C.  n <= 2e5, k and the answer are binary strings.

Intended solution (O(n)):
  * Decode k bit by bit (MSB = largest disk) into the rod of every disk, tracking the
    (src, aux, dst) role permutation of the recursion.
  * big   = largest disk on A (bottom of the dumped block), small = smallest disk on C_old.
    If A or C_old is empty, or big < small, the dumped state is a REGULAR state: answer
    = standard regular-state -> perfect-tower distance
        for d = n..1: if rod[d] != target: ans += 2^(d-1); target = third rod.
  * Otherwise the junction is the single inversion; it disappears exactly when `big`
    is lifted off C, and afterwards the position is regular.  Just before the lift all
    disks smaller than big that are above the junction (rest of A_old, and B's disks
    smaller than big) sit sorted on one rod, big goes to the other rod t in {A, B}
    (whose top must be > big: empty, or `next` = smallest disk > big on B, first
    parked on A).  Optimal cost = min over 4 plans
        [ gather B's disks < big onto the A_old block, move `next` to A ]   (optional)
      + gather all disks < big above the junction onto the rod != t   (regular subgame,
        exponents are ranks INSIDE the subset, not disk sizes)
      + 1 (lift big onto t)
      + regular distance of the resulting regular state to the perfect tower.
    Every term is a sum of O(n) powers of two, so the answer is built as a count per
    bit position followed by one carry pass: O(n) total.

This file:  fast() (the algorithm, exact Python ints), fast_bits() (the same with the
O(n) carry-array normalisation, as one would code it for n = 2e5), brute() (BFS over
ordered stacks), cross-check for every k with n <= 8, plus the three samples.
"""
import sys
from collections import deque


# ------------------------------------------------------------------ intended
def decode(n, k):
    """rod (1=A,2=B,3=C) of disk index i (0 = largest) after k optimal moves A->C."""
    bits = format(k, 'b').zfill(n) if isinstance(k, int) else k.zfill(n)
    d = [0] * n
    src, aux, dst = 1, 2, 3
    for i, ch in enumerate(bits):
        if ch == '1':
            d[i] = dst
            src, aux = aux, src          # remaining disks travel aux -> dst
        else:
            d[i] = src
            dst, aux = aux, dst          # remaining disks travel src -> aux
    return d


def reg(v):
    """Regular Hanoi: exponents e (ranks inside v, smallest disk = 0) such that
    sum 2^e = min moves from configuration v (largest first) to all-on-3."""
    exps = []
    t = 3
    m = len(v)
    for i, r in enumerate(v):
        if r != t:
            exps.append(m - 1 - i)
            t = 6 - t - r
    return exps


def plans(n, k):
    """Yield (exponent list, constant) for every candidate plan; min is the answer."""
    d = decode(n, k)
    big = next((i for i in range(n) if d[i] == 1), None)
    small = next((i for i in range(n - 1, -1, -1) if d[i] == 3), None)
    if big is None or small is None or big > small:           # regular state
        yield reg([3 if r == 1 else r for r in d]), 0
        return
    nxt = next((i for i in range(big - 1, -1, -1) if d[i] == 2), None)
    for use_next in (0, 1):
        dd = list(d)
        pre, c = [], 0
        if use_next:
            if nxt is None:
                continue
            idx = [i for i in range(big, n) if d[i] != 3]
            pre += reg([3 if d[i] == 1 else 2 for i in idx])   # B's small disks onto the block
            for i in idx:
                dd[i] = 1
            dd[nxt] = 1                                        # next -> empty rod A
            c += 1
        for t in (1, 2):
            fixd = [3 if (dd[i] == 2 and t == 1) else dd[i]
                    for i in range(big + 1, n) if dd[i] != 3]
            lastd = [dd[i] if (dd[i] == 3 or i < big) else 3 - t for i in range(n)]
            lastd[big] = t
            yield pre + reg(fixd) + reg(lastd), c + 1


def fast(n, k):
    return min(sum(1 << e for e in ex) + c for ex, c in plans(n, k))


def fast_bits(n, k):
    """Same answer as a binary string, using the O(n) carry pass (no big ints)."""
    best = None
    for ex, c in plans(n, k):
        cnt = [0] * (n + 3)
        for e in ex:
            cnt[e] += 1
        cnt[0] += c
        carry = 0
        bits = []
        for i in range(n + 3):
            s = cnt[i] + carry
            bits.append(s & 1)
            carry = s >> 1
        assert carry == 0
        s = ''.join(map(str, reversed(bits))).lstrip('0') or '0'
        if best is None or len(s) < len(best) or (len(s) == len(best) and s < best):
            best = s
    return best


# ------------------------------------------------------------------ brute
def initial_stacks(n, k):
    d = decode(n, k)
    stacks = [[], [], []]
    for i in range(n):                    # largest first = bottom first
        stacks[d[i] - 1].append(n - i)
    stacks[2] = stacks[2] + stacks[0]
    stacks[0] = []
    return tuple(tuple(s) for s in stacks)


def brute(n, k):
    start = initial_stacks(n, k)
    goal = ((), (), tuple(range(n, 0, -1)))
    if start == goal:
        return 0
    dist = {start: 0}
    dq = deque([start])
    while dq:
        s = dq.popleft()
        dcur = dist[s]
        for i in range(3):
            if not s[i]:
                continue
            top = s[i][-1]
            for j in range(3):
                if i == j or (s[j] and s[j][-1] < top):
                    continue
                ns = list(s)
                ns[i] = s[i][:-1]
                ns[j] = s[j] + (top,)
                ns = tuple(ns)
                if ns in dist:
                    continue
                dist[ns] = dcur + 1
                if ns == goal:
                    return dcur + 1
                dq.append(ns)


if __name__ == '__main__':
    for n, k, want in ((3, '0', '0'), (3, '10', '110'), (5, '11011', '11')):
        got = fast_bits(n, k)
        print('sample', n, k, got, 'OK' if got == want else 'MISMATCH')
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    bad = 0
    tot = 0
    for n in range(1, N + 1):
        for k in range(1 << n):
            b = brute(n, k)
            f = fast(n, k)
            fb = fast_bits(n, k)
            tot += 1
            if b != f or format(f, 'b') != fb:
                bad += 1
                print('MISMATCH', n, format(k, f'0{n}b'), 'brute', b, 'fast', f, fb, initial_stacks(n, k))
    print(f'checked {tot} (n,k) pairs up to n={N}: {bad} mismatches')
