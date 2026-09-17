"""Kattis magicallights (2015 ICPC Singapore, J).

Task: rooted tree, N<=300000 nodes, each coloured 1..100.  Q<=1000000 operations:
"0 X" asks how many colours occur an ODD number of times in the subtree of X,
"K X" (1<=K<=100) recolours node X to K.

Solution under test: flatten the tree with a DFS euler tour so every subtree is a
contiguous range [tin[v], tout[v]].  Because only 100 colours exist, the parity
vector of a range is a 100-bit mask; store it in a Fenwick tree whose group
operation is XOR (self-inverse, so a prefix-XOR to tout minus/XOR prefix to tin-1
gives the range).  A recolour is one point XOR of two bits.  Answer = popcount.
O((N+Q) log N) word operations on 2 64-bit words, O(N) space (plus 100 bits/node).

Brute force: recompute each query by walking the subtree.
"""
import random

class BIT:
    def __init__(self, n):
        self.n = n
        self.t = [0] * (n + 1)
    def xor(self, i, v):
        while i <= self.n:
            self.t[i] ^= v
            i += i & -i
    def pre(self, i):
        r = 0
        while i > 0:
            r ^= self.t[i]
            i -= i & -i
        return r

def solve(n, colour, parent, ops):
    kids = [[] for _ in range(n + 1)]
    for v in range(2, n + 1):
        kids[parent[v]].append(v)
    tin = [0] * (n + 1)
    tout = [0] * (n + 1)
    timer = 0
    stack = [(1, 0)]
    while stack:                       # iterative dfs, euler tour
        v, state = stack.pop()
        if state == 0:
            timer += 1
            tin[v] = timer
            stack.append((v, 1))
            for c in reversed(kids[v]):
                stack.append((c, 0))
        else:
            tout[v] = timer
    bit = BIT(n)
    cur = colour[:]
    for v in range(1, n + 1):
        bit.xor(tin[v], 1 << (cur[v] - 1))
    out = []
    for k, x in ops:
        if k == 0:
            m = bit.pre(tout[x]) ^ bit.pre(tin[x] - 1)
            out.append(bin(m).count("1"))
        else:
            if cur[x] != k:
                bit.xor(tin[x], (1 << (cur[x] - 1)) | (1 << (k - 1)))
                cur[x] = k
    return out

def brute(n, colour, parent, ops):
    kids = [[] for _ in range(n + 1)]
    for v in range(2, n + 1):
        kids[parent[v]].append(v)
    cur = colour[:]
    out = []
    for k, x in ops:
        if k == 0:
            cnt = {}
            st = [x]
            while st:
                v = st.pop()
                cnt[cur[v]] = cnt.get(cur[v], 0) + 1
                st.extend(kids[v])
            out.append(sum(1 for c in cnt.values() if c % 2))
        else:
            cur[x] = k
    return out

def samples():
    n, colour = 10, [0] + list(range(1, 11))
    parent = [0, 0] + list(range(1, 10))
    ops = [(0, 1), (0, 4), (1, 4), (0, 1), (0, 4)]
    assert solve(n, colour, parent, ops) == [10, 7, 8, 7], solve(n, colour, parent, ops)
    n2, colour2 = 7, [0, 1, 2, 2, 1, 1, 2, 1]
    parent2 = [0, 0, 1, 1, 1, 2, 2, 3]
    ops2 = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7)]
    assert solve(n2, colour2, parent2, ops2) == [1, 1, 2, 1, 1, 1, 1]
    print("samples OK")

def fuzz(trials=400):
    rnd = random.Random(99)
    for _ in range(trials):
        n = rnd.randint(1, 12)
        ncol = rnd.randint(1, 4)
        colour = [0] + [rnd.randint(1, ncol) for _ in range(n)]
        parent = [0, 0] + [rnd.randint(1, v - 1) for v in range(2, n + 1)]
        ops = []
        for _ in range(rnd.randint(1, 15)):
            if rnd.random() < 0.5:
                ops.append((0, rnd.randint(1, n)))
            else:
                ops.append((rnd.randint(1, ncol), rnd.randint(1, n)))
        a, b = solve(n, colour, parent, ops), brute(n, colour, parent, ops)
        if a != b:
            print("MISMATCH", n, colour, parent, ops, a, b)
            return False
    print("fuzz OK (%d random trees/op mixes)" % trials)
    return True

if __name__ == "__main__":
    samples()
    assert fuzz()
