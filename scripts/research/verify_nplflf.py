"""
codechef-nplflf  "Query On Strings"
Ops on a multiset of strings:
  1 s      add s
  2 k l    is there a group of k strings sharing a common suffix of length l?
  3 x      remove the string added at operation x (if still present)

Intended solution
-----------------
A "common suffix of length l" is a node at depth l in a trie of the REVERSED
strings.  cnt[node] = how many currently-present strings pass through it, i.e.
how many strings carry that exact length-l suffix.  The query (k,l) is exactly
"is max over nodes at depth l of cnt >= k?".

Add/remove walk one root-to-leaf path and do cnt +/- 1 on <= |s| nodes, so the
total node-touching work is O(sum |s|) for the adds and O(sum |s|) for the
removals (every add is removable at most once) -- both <= 1e5.

Per depth we keep freq[l][c] = #nodes at depth l whose cnt == c, plus best[l] =
the running maximum.  Because every update moves one cnt by exactly +/-1, the
maximum can only rise to the new value or, when the unique holder of the
maximum drops, fall by exactly one (that same node now sits at best-1).  So
best[l] is maintained in O(1) per touched node and each query is O(1).

Total: O(q + sum|s|) time, O(sum|s|) memory.  Comfortably inside q,sum|s| <=1e5.
"""
import random, sys


# ---------------------------------------------------------------- fast
def solve_fast(ops):
    ch = [dict()]          # trie over reversed strings; node 0 = root (depth 0)
    cnt = [0]
    depth = [0]
    freq = []              # freq[l] : dict cnt -> #nodes at depth l with that cnt
    best = []              # best[l] : max cnt at depth l
    added = {}             # op index (1-based) -> string, or None once removed
    out = []

    def ensure(l):
        while len(freq) <= l:
            freq.append({})
            best.append(0)

    def bump(node, delta):
        l = depth[node]
        ensure(l)
        old = cnt[node]
        new = old + delta
        cnt[node] = new
        f = freq[l]
        if old:
            f[old] -= 1
            if f[old] == 0:
                del f[old]
        if new:
            f[new] = f.get(new, 0) + 1
        if delta > 0:
            if new > best[l]:
                best[l] = new
        else:
            if old == best[l] and old not in f:
                best[l] = old - 1

    def walk(s, delta):
        node = 0
        for c in reversed(s):
            nxt = ch[node].get(c)
            if nxt is None:
                nxt = len(ch)
                ch.append({})
                cnt.append(0)
                depth.append(depth[node] + 1)
                ch[node][c] = nxt
            node = nxt
            bump(node, delta)

    for i, op in enumerate(ops, 1):
        if op[0] == 1:
            added[i] = op[1]
            walk(op[1], +1)
        elif op[0] == 2:
            k, l = op[1], op[2]
            ok = l < len(best) and best[l] >= k
            out.append("YES" if ok else "NO")
        else:
            x = op[1]
            s = added.get(x)
            if s is not None:
                added[x] = None
                walk(s, -1)
    return out


# ---------------------------------------------------------------- brute
def solve_brute(ops):
    added = {}
    live = []              # list of (op index, string) still present
    out = []
    for i, op in enumerate(ops, 1):
        if op[0] == 1:
            added[i] = op[1]
            live.append(i)
        elif op[0] == 2:
            k, l = op[1], op[2]
            tally = {}
            for j in live:
                s = added[j]
                if len(s) >= l:
                    suf = s[len(s) - l:]
                    tally[suf] = tally.get(suf, 0) + 1
            out.append("YES" if any(v >= k for v in tally.values()) else "NO")
        else:
            x = op[1]
            if x in added and x in live:
                live.remove(x)
    return out


SAMPLE = ([(1, "aba"), (1, "accba"), (2, 2, 2), (2, 2, 3), (1, "aaaa"),
           (1, "ababa"), (2, 3, 2), (3, 1), (2, 3, 2)],
          ["YES", "NO", "YES", "NO"])


def rand_ops(rng, n, alpha, maxlen):
    ops, add_idx = [], []
    for i in range(1, n + 1):
        r = rng.random()
        if r < 0.45 or not add_idx:
            s = "".join(rng.choice(alpha) for _ in range(rng.randint(1, maxlen)))
            ops.append((1, s))
            add_idx.append(i)
        elif r < 0.8:
            ops.append((2, rng.randint(1, 4), rng.randint(1, maxlen + 1)))
        else:
            ops.append((3, rng.choice(add_idx)))
    return ops


if __name__ == "__main__":
    got = solve_fast(SAMPLE[0])
    assert got == SAMPLE[1], (got, SAMPLE[1])
    assert solve_brute(SAMPLE[0]) == SAMPLE[1]
    print("sample OK:", got)

    rng = random.Random(12345)
    for t in range(3000):
        ops = rand_ops(rng, rng.randint(1, 30), "ab" if t % 2 else "abc",
                       rng.randint(1, 5))
        a, b = solve_fast(ops), solve_brute(ops)
        if a != b:
            print("MISMATCH", ops, a, b)
            sys.exit(1)
    print("3000 random small tests OK")

    # a duplicate-heavy / repeated-removal stress
    rng = random.Random(999)
    for t in range(500):
        ops = rand_ops(rng, rng.randint(1, 60), "a", rng.randint(1, 6))
        if solve_fast(ops) != solve_brute(ops):
            print("MISMATCH dup", ops)
            sys.exit(1)
    print("500 duplicate-heavy tests OK")

    # scale check: q = 1e5, sum|s| = 1e5
    import time
    rng = random.Random(7)
    ops, add_idx, budget = [], [], 100000
    for i in range(1, 100001):
        r = rng.random()
        if r < 0.34 and budget > 0:
            L = min(budget, rng.randint(1, 20))
            budget -= L
            ops.append((1, "".join(rng.choice("abcdefghij") for _ in range(L))))
            add_idx.append(i)
        elif r < 0.8 or not add_idx:
            ops.append((2, rng.randint(1, 50), rng.randint(1, 100000)))
        else:
            ops.append((3, rng.choice(add_idx)))
    t0 = time.time()
    res = solve_fast(ops)
    print("scale: q=100000 sum|s|<=100000 -> %d answers in %.2fs (Python)"
          % (len(res), time.time() - t0))
