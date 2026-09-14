"""codechef-gpd "Gotham PD" -- persistent binary trie over root paths.

Tree rooted at R, grows by adding leaves online. Query (v, k): over the keys of
all nodes on the path v -> R, report min(key ^ k) and max(key ^ k).
Queries are forced online (every token is xored with the previous answer), so an
offline Euler-tour / DFS-with-one-trie sweep is not available.

Solution: version the trie by node. root_trie[u] = insert(root_trie[parent(u)],
key(u)) on a persistent binary trie (31 bits, path copying). A query is one
greedy descent for the min (follow k's bit) and one for the max (follow the
opposite bit) in the version stored at v. O((N+Q)*31) time and nodes.

This script checks the persistent-trie solution against a brute force that walks
the parent chain, on the official sample and on random trees, and also exercises
the encoded (online) input protocol end to end.
"""
import random
import sys
from io import StringIO

BITS = 31  # keys, ids and k are all <= 2^31 - 1


# ---------------------------------------------------------------- persistent trie
class PersistentTrie:
    def __init__(self):
        self.ch = [[0, 0]]  # node 0 = empty / null

    def insert(self, prev, val):
        ch = self.ch
        ch.append(list(ch[prev]))
        cur = len(ch) - 1
        new_root = cur
        for b in range(BITS - 1, -1, -1):
            bit = (val >> b) & 1
            nxt = ch[cur][bit]
            ch.append(list(ch[nxt]) if nxt else [0, 0])
            ch[cur][bit] = len(ch) - 1
            cur = len(ch) - 1
        return new_root

    def _descend(self, root, k, want_same):
        cur, res = root, 0
        for b in range(BITS - 1, -1, -1):
            bit = (k >> b) & 1
            pref = bit if want_same else bit ^ 1
            if self.ch[cur][pref]:
                cur = self.ch[cur][pref]
                res |= (pref ^ bit) << b
            else:
                cur = self.ch[cur][pref ^ 1]
                res |= ((pref ^ 1) ^ bit) << b
        return res

    def min_xor(self, root, k):
        return self._descend(root, k, True)

    def max_xor(self, root, k):
        return self._descend(root, k, False)


def solve_ops(R, rkey, edges, ops):
    """edges: list of (child, parent, key) in any order. ops: decoded queries."""
    key = {R: rkey}
    parent = {R: 0}
    kids = {}
    for u, v, k in edges:
        key[u] = k
        parent[u] = v
        kids.setdefault(v, []).append(u)

    trie = PersistentTrie()
    root_of = {R: trie.insert(0, rkey)}
    stack = [R]                      # BFS/DFS from R: parents get their version first,
    while stack:                     # the input need not list edges top-down
        u = stack.pop()
        for c in kids.get(u, ()):
            root_of[c] = trie.insert(root_of[u], key[c])
            stack.append(c)

    out = []
    for op in ops:
        if op[0] == 0:
            _, v, u, k = op
            root_of[u] = trie.insert(root_of[v], k)
        else:
            _, v, k = op
            out.append((trie.min_xor(root_of[v], k), trie.max_xor(root_of[v], k)))
    return out


def solve_brute(R, rkey, edges, ops):
    key = {R: rkey}
    parent = {R: None}
    for u, v, k in edges:
        key[u] = k
        parent[u] = v
    out = []
    for op in ops:
        if op[0] == 0:
            _, v, u, k = op
            key[u] = k
            parent[u] = v
        else:
            _, v, k = op
            cur, vals = v, []
            while cur is not None:
                vals.append(key[cur] ^ k)
                cur = parent[cur]
            out.append((min(vals), max(vals)))
    return out


# ---------------------------------------------------------------- encoded protocol
def run_encoded(text):
    """Full reader: decodes each token with the running last_answer, as the
    statement's note prescribes, and prints 'min max' per type-1 query."""
    it = iter(text.split())
    nxt = lambda: int(next(it))
    N, Q = nxt(), nxt()
    R, rkey = nxt(), nxt()
    edges = [(nxt(), nxt(), nxt()) for _ in range(N - 1)]

    key = {R: rkey}
    kids = {}
    for u, v, k in edges:
        key[u] = k
        kids.setdefault(v, []).append(u)
    trie = PersistentTrie()
    root_of = {R: trie.insert(0, rkey)}
    stack = [R]
    while stack:
        u = stack.pop()
        for c in kids.get(u, ()):
            root_of[c] = trie.insert(root_of[u], key[c])
            stack.append(c)

    last, out = 0, []
    for _ in range(Q):
        t = nxt() ^ last
        if t == 0:
            v, u, k = nxt() ^ last, nxt() ^ last, nxt() ^ last
            root_of[u] = trie.insert(root_of[v], k)
        else:
            v, k = nxt() ^ last, nxt() ^ last
            mn = trie.min_xor(root_of[v], k)
            mx = trie.max_xor(root_of[v], k)
            out.append(f"{mn} {mx}")
            last = mn ^ mx
    return "\n".join(out)


def encode(R, rkey, edges, ops):
    """Inverse of the protocol: produce the encoded input file for these ops."""
    lines = [f"{len(edges) + 1} {len(ops)}", f"{R} {rkey}"]
    lines += [f"{u} {v} {k}" for u, v, k in edges]
    last = 0
    for op in ops:
        if op[0] == 0:
            _, v, u, k = op
            lines.append(f"{0 ^ last} {v ^ last} {u ^ last} {k ^ last}")
        else:
            _, v, k = op
            lines.append(f"{1 ^ last} {v ^ last} {k ^ last}")
            mn, mx = None, None
            # last_answer needs the true answer, so borrow the brute force
            mn, mx = solve_brute(R, rkey, edges, ops[:ops.index(op) + 1])[-1]
            last = mn ^ mx
    return "\n".join(lines)


SAMPLE_IN = """6 4
1 2
5 1 3
2 1 4
3 2 5
4 2 1
6 3 3
1 4 2
6 0 12
0 7 12 7
4 0 7"""
SAMPLE_OUT = "0 6\n2 7\n0 1"


def test_sample():
    got = run_encoded(SAMPLE_IN)
    assert got == SAMPLE_OUT, f"sample mismatch:\n{got}\n!=\n{SAMPLE_OUT}"
    print("sample OK")


def test_random(trials=400, seed=1):
    rng = random.Random(seed)
    for t in range(trials):
        n = rng.randint(1, 8)
        maxv = rng.choice([3, 7, 31, 2 ** 31 - 1])
        ids = rng.sample(range(1, 60), n + 6)
        R = ids[0]
        rkey = rng.randint(1, maxv)
        nodes = [R]
        edges = []
        for u in ids[1:n]:
            v = rng.choice(nodes)
            edges.append((u, v, rng.randint(1, maxv)))
            nodes.append(u)
        rng.shuffle(edges)  # parents are not guaranteed to come first in the input
        live = list(nodes)
        spare = ids[n:]
        ops = []
        for _ in range(rng.randint(1, 10)):
            if spare and rng.random() < 0.4:
                u = spare.pop()
                ops.append((0, rng.choice(live), u, rng.randint(1, maxv)))
                live.append(u)
            else:
                ops.append((1, rng.choice(live), rng.randint(1, maxv)))
        exp = solve_brute(R, rkey, edges, ops)
        got = solve_ops(R, rkey, edges, ops)
        assert exp == got, (t, edges, ops, exp, got)
        # and through the encoded reader
        enc = run_encoded(encode(R, rkey, edges, ops))
        assert enc == "\n".join(f"{a} {b}" for a, b in exp), (t, enc, exp)
    print(f"random OK ({trials} trials, brute vs persistent trie, encoded protocol)")


def test_scale():
    """Sanity check on the real limits: a path-shaped tree, N=1e5 + Q=2e5."""
    import time
    rng = random.Random(7)
    N, Q = 100000, 200000
    R, rkey = 1, rng.randint(1, 2 ** 31 - 1)
    edges = [(i, i - 1, rng.randint(1, 2 ** 31 - 1)) for i in range(2, N + 1)]
    ops = []
    nid = N + 1
    for _ in range(Q):
        if rng.random() < 0.3:
            ops.append((0, rng.randint(1, N), nid, rng.randint(1, 2 ** 31 - 1)))
            nid += 1
        else:
            ops.append((1, rng.randint(1, N), rng.randint(1, 2 ** 31 - 1)))
    t0 = time.time()
    res = solve_ops(R, rkey, edges, ops)
    print(f"scale OK: N={N} Q={Q}, {len(res)} answers, "
          f"{time.time() - t0:.1f}s in python, "
          f"~{(N + Q) * BITS / 1e6:.1f}M trie nodes "
          "(a C++ implementation is comfortably inside the limits)")


if __name__ == "__main__":
    test_sample()
    test_random()
    if "--scale" in sys.argv:
        test_scale()
