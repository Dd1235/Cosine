"""
codechef-xrqrs "Xor Queries" -- verification.

Intended solution: a PERSISTENT binary trie (equivalently a persistent segment
tree over the value domain [0, 2^19), since 1 <= x <= 5*10^5 < 524288) built
over the array prefixes.  root[i] is the trie holding a[1..i]; each insert
copies only the O(19) nodes on one root-to-leaf path.

  type 0 x      : root.append(insert(root[-1], x))              O(19)
  type 2 k      : pop k roots -- persistence makes truncation O(k) pointer pops
  type 1 L R x  : greedy descent on (root[R], root[L-1]) taking the child
                  opposite to x's bit whenever its subtree count difference
                  cnt[R]-cnt[L-1] > 0                            O(19)
  type 3 L R x  : walk the bits of x; whenever x's bit is 1, add the whole
                  0-child count difference, then follow the 1-child (plus the
                  leaf itself, since the query is "<= x")        O(19)
  type 4 L R k  : descend, comparing k against the 0-child count difference
                  (k-th order statistic)                         O(19)

Counts over a range work because node counts are additive over prefixes:
cnt_{[L..R]}(v) = cnt_{root[R]}(v) - cnt_{root[L-1]}(v), and the two versions
share structure, so the subtraction is done node-pairwise during one descent.
Total O(M log C) time, O(M log C) nodes.

This file checks that implementation against an O(n) brute force on the
provided sample and on random query streams.
"""
import random

BITS = 19            # 5*10**5 < 2**19 = 524288
SIZE = 1 << BITS

# ---------------- persistent binary trie (= persistent segment tree) --------
left = [0]
right = [0]
cnt = [0]

def new_node(l, r, c):
    left.append(l); right.append(r); cnt.append(c)
    return len(cnt) - 1

def insert(prev, x):
    cur = new_node(left[prev], right[prev], cnt[prev] + 1)
    root = cur
    for b in range(BITS - 1, -1, -1):
        bit = (x >> b) & 1
        p = right[prev] if bit else left[prev]
        nxt = new_node(left[p], right[p], cnt[p] + 1)
        if bit:
            right[cur] = nxt
        else:
            left[cur] = nxt
        cur, prev = nxt, p
    return root

def max_xor(ru, rv, x):
    """ru = root[R], rv = root[L-1]; returns the y in a[L..R] maximizing x^y."""
    y = 0
    for b in range(BITS - 1, -1, -1):
        bit = (x >> b) & 1
        want_one = 1 - bit                     # opposite bit is better
        cu = right[ru] if want_one else left[ru]
        cv = right[rv] if want_one else left[rv]
        if cnt[cu] - cnt[cv] > 0:
            y |= want_one << b
            ru, rv = cu, cv
        else:
            ru = right[ru] if not want_one else left[ru]
            rv = right[rv] if not want_one else left[rv]
            y |= bit << b
    return y

def count_le(ru, rv, x):
    """number of values <= x in a[L..R]"""
    res = 0
    for b in range(BITS - 1, -1, -1):
        bit = (x >> b) & 1
        lu, lv = left[ru], left[rv]
        if bit:
            res += cnt[lu] - cnt[lv]           # whole 0-subtree is < x here
            ru, rv = right[ru], right[rv]
        else:
            ru, rv = lu, lv
    res += cnt[ru] - cnt[rv]                   # values exactly equal to x
    return res

def kth(ru, rv, k):
    """k-th smallest (1-indexed) in a[L..R]"""
    v = 0
    for b in range(BITS - 1, -1, -1):
        lu, lv = left[ru], left[rv]
        c = cnt[lu] - cnt[lv]
        if k <= c:
            ru, rv = lu, lv
        else:
            k -= c
            v |= 1 << b
            ru, rv = right[ru], right[rv]
    return v

# ---------------- driver ---------------------------------------------------
def solve(queries):
    global left, right, cnt
    left = [0]; right = [0]; cnt = [0]
    roots = [0]                                # roots[i] = version after i elems
    out = []
    for q in queries:
        t = q[0]
        if t == 0:
            roots.append(insert(roots[-1], q[1]))
        elif t == 1:
            _, L, R, x = q
            out.append(max_xor(roots[R], roots[L - 1], x))
        elif t == 2:
            del roots[len(roots) - q[1]:]
        elif t == 3:
            _, L, R, x = q
            out.append(count_le(roots[R], roots[L - 1], x))
        else:
            _, L, R, k = q
            out.append(kth(roots[R], roots[L - 1], k))
    return out

def brute(queries):
    a = []
    out = []
    for q in queries:
        t = q[0]
        if t == 0:
            a.append(q[1])
        elif t == 1:
            _, L, R, x = q
            out.append(max(a[L - 1:R], key=lambda y: x ^ y))
        elif t == 2:
            del a[len(a) - q[1]:]
        elif t == 3:
            _, L, R, x = q
            out.append(sum(1 for y in a[L - 1:R] if y <= x))
        else:
            _, L, R, k = q
            out.append(sorted(a[L - 1:R])[k - 1])
    return out

# ---------------- sample ---------------------------------------------------
SAMPLE = """0 8
4 1 1 1
0 2
1 2 2 7
1 2 2 7
0 1
3 2 2 2
1 1 2 3
3 1 3 5
0 6"""
EXPECTED = [8, 2, 2, 1, 8, 2]

sample_q = [tuple(map(int, line.split())) for line in SAMPLE.splitlines()]
got = solve(sample_q)
print("sample got     :", got)
print("sample expected:", EXPECTED)
assert got == EXPECTED, "SAMPLE MISMATCH"
assert brute(sample_q) == EXPECTED, "brute force disagrees with sample"
print("sample OK\n")

# ---------------- randomized cross-check -----------------------------------
random.seed(7)
MAXV = 50
for trial in range(400):
    n = 0
    qs = []
    for _ in range(random.randint(1, 60)):
        r = random.random()
        if n == 0 or r < 0.40:
            qs.append((0, random.randint(1, MAXV))); n += 1
        elif r < 0.55:
            k = random.randint(1, n); qs.append((2, k)); n -= k
        else:
            L = random.randint(1, n); R = random.randint(L, n)
            t = random.choice([1, 3, 4])
            if t == 4:
                qs.append((4, L, R, random.randint(1, R - L + 1)))
            else:
                qs.append((t, L, R, random.randint(1, MAXV)))
    e, g = brute(qs), solve(qs)
    assert e == g, (qs, e, g)
print("400 random trials (values <= 50) OK")

# wider values, exercising the high bits
MAXV = 500000
random.seed(11)
for trial in range(150):
    n = 0
    qs = []
    for _ in range(random.randint(1, 80)):
        r = random.random()
        if n == 0 or r < 0.45:
            qs.append((0, random.randint(1, MAXV))); n += 1
        elif r < 0.55:
            k = random.randint(1, n); qs.append((2, k)); n -= k
        else:
            L = random.randint(1, n); R = random.randint(L, n)
            t = random.choice([1, 3, 4])
            if t == 4:
                qs.append((4, L, R, random.randint(1, R - L + 1)))
            else:
                qs.append((t, L, R, random.randint(1, MAXV)))
    e, g = brute(qs), solve(qs)
    assert e == g, (qs, e, g)
print("150 random trials (values <= 5*10^5) OK")

# ---------------- node-count / limit sanity --------------------------------
left = [0]; right = [0]; cnt = [0]
roots = [0]
M = 5 * 10**5
for i in range(20000):
    roots.append(insert(roots[-1], random.randint(1, MAXV)))
per_insert = (len(cnt) - 1) / 20000
print("nodes per insert: %.1f  ->  %d inserts would need ~%.1e nodes"
      % (per_insert, M, per_insert * M))
print("ALL CHECKS PASSED")
